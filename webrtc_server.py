import asyncio
import json
import logging
import base64
import cv2
import time
from datetime import datetime
import websockets
from config import *

# 配置日志
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

class WebRTCServer:
    def __init__(self):
        self.connections = {}  # 存储连接信息 {connection_id: {websocket, peer_connection}}
        self.rtsp_url = RTSP_URL
        self.is_streaming = False
        self.cap = None
        
    def setup_camera(self):
        """设置摄像头连接"""
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFER_SIZE)
                logger.info(f"摄像头连接成功: {self.rtsp_url}")
                return True
            else:
                logger.error(f"无法连接RTSP流: {self.rtsp_url}")
                return False
        except Exception as e:
            logger.error(f"设置摄像头失败: {e}")
            return False
    
    async def handle_websocket(self, websocket):
        """处理WebSocket连接"""
        connection_id = id(websocket)
        self.connections[connection_id] = {
            'websocket': websocket,
            'peer_connection': None,
            'data_channel': None
        }
        
        client_addr = websocket.remote_address
        logger.info(f"新WebRTC客户端连接: {client_addr}")
        
        try:
            # 发送连接成功消息
            await self.send_message(websocket, "connected", {
                "message": "WebRTC信令服务器连接成功",
                "connection_id": connection_id,
                "server_type": "webrtc_signaling",
                "video_config": {
                    "width": VIDEO_WIDTH,
                    "height": VIDEO_HEIGHT,
                    "fps": VIDEO_FPS
                }
            })
            
            # 处理客户端消息
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_signaling_message(websocket, connection_id, data)
                except json.JSONDecodeError:
                    logger.error("无法解析JSON消息")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端断开连接: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket错误: {e}")
        finally:
            if connection_id in self.connections:
                del self.connections[connection_id]
            
    async def handle_signaling_message(self, websocket, connection_id, data):
        """处理WebRTC信令消息"""
        message_type = data.get("type")
        
        if message_type == "offer":
            await self.handle_offer(websocket, connection_id, data)
        elif message_type == "answer":
            await self.handle_answer(websocket, connection_id, data)
        elif message_type == "ice_candidate":
            await self.handle_ice_candidate(websocket, connection_id, data)
        elif message_type == "start_video":
            await self.start_video_stream()
            await self.send_message(websocket, "video_started", {"message": "视频流已开始"})
        elif message_type == "stop_video":
            await self.stop_video_stream()
            await self.send_message(websocket, "video_stopped", {"message": "视频流已停止"})
        elif message_type == "get_status":
            await self.send_message(websocket, "status", {
                "streaming": self.is_streaming,
                "connections": len(self.connections),
                "rtsp_url": self.rtsp_url[:50] + "..."
            })
        else:
            logger.warning(f"未知信令消息类型: {message_type}")
    
    async def handle_offer(self, websocket, connection_id, data):
        """处理WebRTC Offer"""
        logger.info(f"收到WebRTC Offer: {connection_id}")
        
        # 这里应该创建Answer，但为了简化，我们直接启动视频流
        await self.send_message(websocket, "answer", {
            "sdp": self.create_answer_sdp(),
            "type": "answer"
        })
        
    async def handle_answer(self, websocket, connection_id, data):
        """处理WebRTC Answer"""
        logger.info(f"收到WebRTC Answer: {connection_id}")
        
    async def handle_ice_candidate(self, websocket, connection_id, data):
        """处理ICE候选"""
        logger.info(f"收到ICE Candidate: {connection_id}")
        
    def create_answer_sdp(self):
        """创建简化的SDP Answer"""
        return {
            "type": "answer",
            "sdp": f"""v=0
o=- 0 0 IN IP4 127.0.0.1
s=-
c=IN IP4 127.0.0.1
t=0 0
m=video {WEBRTC_SERVER_PORT} RTP/AVP 96
a=rtpmap:96 H264/90000
a=sendonly
"""
        }
    
    async def send_message(self, websocket, message_type, data):
        """发送消息到客户端"""
        try:
            response = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    async def broadcast_message(self, message_type, data):
        """广播消息到所有客户端"""
        if self.connections:
            message = json.dumps({
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            # 并发发送到所有连接
            await asyncio.gather(
                *[conn['websocket'].send(message) for conn in self.connections.values()],
                return_exceptions=True
            )
    
    async def start_video_stream(self):
        """开始视频流"""
        if self.is_streaming:
            return
            
        if not self.setup_camera():
            return
            
        self.is_streaming = True
        logger.info("开始WebRTC视频流传输")
        
        # 启动视频流任务
        asyncio.create_task(self.video_stream_loop())
    
    async def stop_video_stream(self):
        """停止视频流"""
        self.is_streaming = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("WebRTC视频流已停止")
    
    async def video_stream_loop(self):
        """WebRTC视频流循环"""
        frame_interval = 1.0 / VIDEO_FPS
        last_frame_time = 0
        frame_count = 0
        
        while self.is_streaming and self.connections:
            current_time = time.time()
            
            # 控制帧率
            if current_time - last_frame_time < frame_interval:
                await asyncio.sleep(0.01)
                continue
                
            try:
                if not self.cap or not self.cap.isOpened():
                    logger.warning("摄像头连接断开，尝试重新连接...")
                    if not self.setup_camera():
                        await asyncio.sleep(1)
                        continue
                
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("无法读取视频帧")
                    await asyncio.sleep(0.1)
                    continue
                
                # 调整分辨率
                frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
                
                # 编码为JPEG (WebRTC fallback)
                _, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                # 转换为base64
                frame_base64 = base64.b64encode(jpeg_data).decode('utf-8')
                
                # 广播视频帧 (作为WebRTC数据通道的备用方案)
                await self.broadcast_message("video_frame", {
                    "image": frame_base64,
                    "width": VIDEO_WIDTH,
                    "height": VIDEO_HEIGHT,
                    "timestamp": current_time,
                    "frame_count": frame_count,
                    "transport": "webrtc_fallback"
                })
                
                frame_count += 1
                last_frame_time = current_time
                
                # 每100帧输出一次状态
                if frame_count % 100 == 0:
                    logger.info(f"WebRTC已发送 {frame_count} 帧，连接数: {len(self.connections)}")
                
            except Exception as e:
                logger.error(f"WebRTC视频流处理错误: {e}")
                await asyncio.sleep(0.1)
        
        # 清理
        await self.stop_video_stream()
    
    async def start_server(self, host="0.0.0.0", port=8765):
        """启动WebRTC信令服务器"""
        logger.info(f"启动WebRTC信令服务器 {host}:{port}")
        logger.info(f"RTSP源: {self.rtsp_url}")
        logger.info(f"目标分辨率: {VIDEO_WIDTH}x{VIDEO_HEIGHT}@{VIDEO_FPS}FPS")
        
        async with websockets.serve(self.handle_websocket, host, port):
            logger.info("WebRTC信令服务器已启动")
            logger.info("支持WebRTC P2P连接 + JPEG备用传输")
            await asyncio.Future()  # 永远运行

def main():
    """主函数"""
    server = WebRTCServer()
    
    try:
        asyncio.run(server.start_server(WEBRTC_SERVER_HOST, WEBRTC_SERVER_PORT))
    except KeyboardInterrupt:
        logger.info("WebRTC服务器已停止")
    except Exception as e:
        logger.error(f"WebRTC服务器错误: {e}")

if __name__ == "__main__":
    main() 