import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCIceCandidate
from aiortc.contrib.media import MediaPlayer
import websockets
from av import VideoFrame
import cv2
import numpy as np
from config import *

# 配置日志
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

class RTSPVideoTrack(VideoStreamTrack):
    """
    从RTSP流读取视频帧的自定义视频轨道
    """
    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.cap = None
        self._timestamp = 0
        self._start_time = time.time()
        self.frame_rate = 30
        self.last_frame = None
        self._setup_capture()
        
    def _setup_capture(self):
        """设置视频捕获"""
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if self.cap.isOpened():
                # 设置缓冲区大小，减少延迟
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFER_SIZE)
                # 获取实际帧率
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                if fps > 0:
                    self.frame_rate = min(fps, VIDEO_FPS)  # 限制最大帧率
                logger.info(f"RTSP连接成功，帧率: {self.frame_rate}")
            else:
                logger.error(f"无法连接RTSP流: {self.rtsp_url}")
        except Exception as e:
            logger.error(f"设置RTSP捕获失败: {e}")
        
    async def recv(self):
        """
        接收视频帧
        """
        # 计算时间戳
        pts = int((time.time() - self._start_time) * 90000)  # 90kHz时钟
        
        if self.cap is None or not self.cap.isOpened():
            logger.warning("RTSP连接断开，尝试重新连接...")
            self._setup_capture()
            if self.cap is None or not self.cap.isOpened():
                # 如果无法连接，返回黑色帧
                if self.last_frame is not None:
                    frame = self.last_frame.copy()
                                 else:
                     frame = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
                     cv2.putText(frame, "RTSP Connection Lost", (VIDEO_WIDTH//2-100, VIDEO_HEIGHT//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                av_frame = VideoFrame.from_ndarray(frame, format="bgr24")
                av_frame.pts = pts
                av_frame.time_base = "1/90000"
                return av_frame
                
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("无法读取视频帧，尝试重新连接...")
            self.cap.release()
            self._setup_capture()
            # 返回最后一帧或黑色帧
            if self.last_frame is not None:
                frame = self.last_frame.copy()
                         else:
                 frame = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
                 cv2.putText(frame, "No Signal", (VIDEO_WIDTH//2-60, VIDEO_HEIGHT//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
         else:
             # 调整分辨率
             frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
            self.last_frame = frame.copy()
        
        # 转换为AV帧
        av_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        av_frame.pts = pts
        av_frame.time_base = "1/90000"
        
        return av_frame
    
    def stop(self):
        """停止视频流"""
        if self.cap:
            self.cap.release()
            self.cap = None

class WebRTCMediaServer:
    def __init__(self):
        self.connections = {}  # session_id -> {"pc": RTCPeerConnection, "websocket": WebSocket}
        self.rtsp_url = RTSP_URL
        
    async def handle_websocket(self, websocket):
        """
        处理WebSocket连接
        """
        session_id = id(websocket)
        logger.info(f"新的WebSocket连接: {websocket.remote_address}, Session: {session_id}")
        
        # 初始化连接信息
        self.connections[session_id] = {
            "websocket": websocket,
            "pc": None
        }
        
        try:
            # 发送连接成功消息
            await self.send_message(websocket, "connected", {
                "message": "WebRTC媒体服务器连接成功",
                "session_id": session_id
            })
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(session_id, data)
                except json.JSONDecodeError:
                    logger.error("无法解析JSON消息")
                    await self.send_error(websocket, "无效的JSON格式")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    await self.send_error(websocket, str(e))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket连接已关闭: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket错误: {e}")
        finally:
            await self.cleanup_connection(session_id)
            
    async def handle_message(self, session_id, data):
        """
        处理接收到的消息
        """
        message_type = data.get("type")
        logger.info(f"会话{session_id}收到消息类型: {message_type}")
        
        if message_type == "offer":
            await self.handle_offer(session_id, data)
        elif message_type == "ice-candidate":
            await self.handle_ice_candidate(session_id, data)
        elif message_type == "request-stream":
            await self.handle_stream_request(session_id, data)
        else:
            logger.warning(f"未知消息类型: {message_type}")
            await self.send_error_to_session(session_id, f"未知消息类型: {message_type}")
            
    async def handle_offer(self, session_id, data):
        """
        处理WebRTC Offer
        """
        logger.info(f"处理会话{session_id}的WebRTC Offer")
        
        connection_info = self.connections.get(session_id)
        if not connection_info:
            logger.error(f"会话{session_id}不存在")
            return
            
        try:
            # 创建RTCPeerConnection
            pc = RTCPeerConnection()
            connection_info["pc"] = pc
            
            # 设置ICE候选处理
            @pc.on("icecandidate")
            def on_icecandidate(candidate):
                if candidate:
                    asyncio.create_task(self.send_message(
                        connection_info["websocket"], 
                        "ice-candidate", 
                        {
                            "candidate": {
                                "candidate": candidate.candidate,
                                "sdpMid": candidate.sdpMid,
                                "sdpMLineIndex": candidate.sdpMLineIndex,
                            }
                        }
                    ))
            
            # 设置连接状态监控
            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info(f"会话{session_id}连接状态: {pc.connectionState}")
                await self.send_message(
                    connection_info["websocket"],
                    "connection-state",
                    {"state": pc.connectionState}
                )
            
            # 添加RTSP视频轨道
            video_track = RTSPVideoTrack(self.rtsp_url)
            pc.addTrack(video_track)
            logger.info(f"已为会话{session_id}添加RTSP视频轨道")
            
            # 设置远程描述
            offer = RTCSessionDescription(
                sdp=data["sdp"],
                type=data["type"]
            )
            await pc.setRemoteDescription(offer)
            logger.info(f"会话{session_id}设置远程描述成功")
            
            # 创建answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            logger.info(f"会话{session_id}创建Answer成功")
            
            # 发送answer回客户端
            await self.send_message(
                connection_info["websocket"],
                "answer",
                {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type
                }
            )
            
            logger.info(f"会话{session_id}WebRTC连接建立完成")
            
        except Exception as e:
            logger.error(f"处理会话{session_id}的offer时出错: {e}")
            await self.send_error_to_session(session_id, f"处理offer失败: {str(e)}")
            
    async def handle_ice_candidate(self, session_id, data):
        """
        处理ICE候选
        """
        logger.info(f"处理会话{session_id}的ICE候选")
        
        connection_info = self.connections.get(session_id)
        if not connection_info or not connection_info["pc"]:
            logger.error(f"会话{session_id}的PeerConnection不存在")
            return
            
        try:
            candidate_data = data.get("candidate")
            if candidate_data:
                candidate = RTCIceCandidate(
                    candidate=candidate_data["candidate"],
                    sdpMid=candidate_data.get("sdpMid"),
                    sdpMLineIndex=candidate_data.get("sdpMLineIndex")
                )
                await connection_info["pc"].addIceCandidate(candidate)
                logger.info(f"会话{session_id}添加ICE候选成功")
        except Exception as e:
            logger.error(f"处理会话{session_id}的ICE候选时出错: {e}")
            
    async def handle_stream_request(self, session_id, data):
        """
        处理视频流请求
        """
        logger.info(f"处理会话{session_id}的视频流请求")
        
        try:
                         await self.send_message_to_session(session_id, "stream-ready", {
                 "message": "RTSP视频流准备就绪",
                 "rtsp_url": self.rtsp_url,
                 "resolution": f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
                 "fps": VIDEO_FPS
             })
        except Exception as e:
            logger.error(f"处理会话{session_id}的流请求时出错: {e}")
            await self.send_error_to_session(session_id, str(e))
    
    async def send_message(self, websocket, message_type, data):
        """
        发送消息到WebSocket
        """
        try:
            response = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    async def send_message_to_session(self, session_id, message_type, data):
        """
        发送消息到指定会话
        """
        connection_info = self.connections.get(session_id)
        if connection_info:
            await self.send_message(connection_info["websocket"], message_type, data)
    
    async def send_error(self, websocket, error_message):
        """
        发送错误消息
        """
        await self.send_message(websocket, "error", {"message": error_message})
    
    async def send_error_to_session(self, session_id, error_message):
        """
        发送错误消息到指定会话
        """
        connection_info = self.connections.get(session_id)
        if connection_info:
            await self.send_error(connection_info["websocket"], error_message)
    
    async def cleanup_connection(self, session_id):
        """
        清理连接资源
        """
        connection_info = self.connections.get(session_id)
        if connection_info:
            # 关闭PeerConnection
            if connection_info["pc"]:
                await connection_info["pc"].close()
            
            # 移除连接记录
            del self.connections[session_id]
            logger.info(f"已清理会话{session_id}的资源")
            
    async def start_server(self, host="0.0.0.0", port=8765):
        """
        启动WebRTC媒体服务器
        """
        logger.info(f"启动WebRTC媒体服务器 {host}:{port}")
        logger.info(f"RTSP源: {self.rtsp_url}")
        
        async with websockets.serve(self.handle_websocket, host, port):
            logger.info("WebRTC媒体服务器已启动")
            logger.info("支持真实RTSP视频流传输")
            await asyncio.Future()  # 永远运行

def main():
    """
    主函数
    """
    server = WebRTCMediaServer()
    
    try:
        asyncio.run(server.start_server(WEBRTC_SERVER_HOST, WEBRTC_SERVER_PORT))
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}")

if __name__ == "__main__":
    main() 