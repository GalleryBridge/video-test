import asyncio
import json
import logging
import subprocess
import threading
import time
from datetime import datetime
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaPlayer
import websockets
from av import VideoFrame
import cv2
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
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
        
    async def recv(self):
        """
        接收视频帧
        """
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if not self.cap.isOpened():
                logger.error(f"无法打开RTSP流: {self.rtsp_url}")
                raise Exception("无法打开RTSP流")
                
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("无法读取视频帧，尝试重新连接...")
            self.cap.release()
            self.cap = cv2.VideoCapture(self.rtsp_url)
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("RTSP流断开")
        
        # 转换为RGB格式（OpenCV使用BGR）
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 创建AVFrame
        av_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        av_frame.pts = self._timestamp
        av_frame.time_base = 1 / 30  # 假设30fps
        
        self._timestamp += 1
        
        return av_frame

class WebRTCMediaServer:
    def __init__(self):
        self.pcs = set()
        self.rtsp_url = "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0"
        
    async def handle_websocket(self, websocket, path):
        """
        处理WebSocket连接
        """
        logger.info(f"新的WebSocket连接: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error("无法解析JSON消息")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"WebSocket错误: {e}")
            
    async def handle_message(self, websocket, data):
        """
        处理接收到的消息
        """
        message_type = data.get("type")
        
        if message_type == "offer":
            await self.handle_offer(websocket, data)
        elif message_type == "ice-candidate":
            await self.handle_ice_candidate(websocket, data)
        else:
            logger.warning(f"未知消息类型: {message_type}")
            
    async def handle_offer(self, websocket, data):
        """
        处理WebRTC Offer
        """
        try:
            # 创建RTCPeerConnection
            pc = RTCPeerConnection()
            self.pcs.add(pc)
            
            # 添加RTSP视频轨道
            video_track = RTSPVideoTrack(self.rtsp_url)
            pc.addTrack(video_track)
            
            # 设置远程描述
            offer = RTCSessionDescription(
                sdp=data["sdp"],
                type=data["type"]
            )
            await pc.setRemoteDescription(offer)
            
            # 创建answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            # 发送answer回客户端
            response = {
                "type": "answer",
                "sdp": pc.localDescription.sdp
            }
            await websocket.send(json.dumps(response))
            
            logger.info("WebRTC连接已建立")
            
            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info(f"连接状态变化: {pc.connectionState}")
                if pc.connectionState == "closed":
                    self.pcs.discard(pc)
                    
        except Exception as e:
            logger.error(f"处理offer时出错: {e}")
            error_response = {
                "type": "error",
                "message": str(e)
            }
            await websocket.send(json.dumps(error_response))
            
    async def handle_ice_candidate(self, websocket, data):
        """
        处理ICE候选
        """
        logger.info("收到ICE候选")
        # 在实际实现中，这里需要将ICE候选添加到对应的PeerConnection
        
    async def start_server(self, host="localhost", port=8765):
        """
        启动WebRTC媒体服务器
        """
        logger.info(f"启动WebRTC媒体服务器 {host}:{port}")
        
        async with websockets.serve(self.handle_websocket, host, port):
            logger.info("WebRTC媒体服务器已启动")
            await asyncio.Future()  # 永远运行

def main():
    """
    主函数
    """
    server = WebRTCMediaServer()
    
    try:
        asyncio.run(server.start_server("0.0.0.0", 8765))
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}")

if __name__ == "__main__":
    main() 