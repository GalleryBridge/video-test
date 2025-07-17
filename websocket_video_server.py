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

class WebSocketVideoServer:
    def __init__(self):
        self.connections = set()
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
        self.connections.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"新客户端连接: {client_addr}")
        
        try:
            # 发送连接成功消息
            await self.send_message(websocket, "connected", {
                "message": "WebSocket视频服务器连接成功",
                "server_type": "websocket_video",
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
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error("无法解析JSON消息")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端断开连接: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket错误: {e}")
        finally:
            self.connections.discard(websocket)
            
    async def handle_message(self, websocket, data):
        """处理接收到的消息"""
        message_type = data.get("type")
        
        if message_type == "start_video":
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
            logger.warning(f"未知消息类型: {message_type}")
    
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
                *[ws.send(message) for ws in self.connections.copy()],
                return_exceptions=True
            )
    
    async def start_video_stream(self):
        """开始视频流"""
        if self.is_streaming:
            return
            
        if not self.setup_camera():
            return
            
        self.is_streaming = True
        logger.info("开始视频流传输")
        
        # 启动视频流任务
        asyncio.create_task(self.video_stream_loop())
    
    async def stop_video_stream(self):
        """停止视频流"""
        self.is_streaming = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("视频流已停止")
    
    async def video_stream_loop(self):
        """视频流循环"""
        frame_interval = 1.0 / VIDEO_FPS
        last_frame_time = 0
        
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
                
                # 编码为JPEG
                _, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # 转换为base64
                frame_base64 = base64.b64encode(jpeg_data).decode('utf-8')
                
                # 广播视频帧
                await self.broadcast_message("video_frame", {
                    "image": frame_base64,
                    "width": VIDEO_WIDTH,
                    "height": VIDEO_HEIGHT,
                    "timestamp": current_time
                })
                
                last_frame_time = current_time
                
            except Exception as e:
                logger.error(f"视频流处理错误: {e}")
                await asyncio.sleep(0.1)
        
        # 清理
        await self.stop_video_stream()
    
    async def start_server(self, host="0.0.0.0", port=8765):
        """启动WebSocket视频服务器"""
        logger.info(f"启动WebSocket视频服务器 {host}:{port}")
        logger.info(f"RTSP源: {self.rtsp_url}")
        
        async with websockets.serve(self.handle_websocket, host, port):
            logger.info("WebSocket视频服务器已启动")
            logger.info("支持JPEG图像流传输 (无WebRTC依赖)")
            await asyncio.Future()  # 永远运行

def main():
    """主函数"""
    server = WebSocketVideoServer()
    
    try:
        asyncio.run(server.start_server(WEBRTC_SERVER_HOST, WEBRTC_SERVER_PORT))
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器错误: {e}")

if __name__ == "__main__":
    main() 