#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地视频文件WebSocket测试服务器
用于测试JSMpeg播放器的WebSocket连接
"""

import asyncio
import websockets
import subprocess
import time
import signal
import sys
import os

class LocalVideoWebSocketServer:
    def __init__(self, video_file="test_video.mp4", host='192.168.1.196', port=8103):
        self.video_file = video_file
        self.host = host
        self.port = port
        self.clients = set()
        self.ffmpeg_process = None
        self.is_running = False
        self.stats = {
            'bytes_sent': 0,
            'packets_sent': 0,
            'clients_count': 0
        }

    def log(self, message):
        """日志输出"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def check_video_file(self):
        """检查视频文件是否存在"""
        if not os.path.exists(self.video_file):
            self.log(f"❌ 视频文件不存在: {self.video_file}")
            self.log("💡 请将测试视频文件放在脚本同目录下，命名为 test_video.mp4")
            self.log("💡 或者创建一个测试视频:")
            self.log("   ffmpeg -f lavfi -i testsrc=duration=60:size=640x480:rate=15 -c:v libx264 test_video.mp4")
            return False
        
        self.log(f"✅ 找到视频文件: {self.video_file}")
        return True

    def start_ffmpeg_stream(self):
        """启动FFmpeg处理本地视频"""
        # FFmpeg命令 - 处理本地视频并输出MPEG-TS格式
        cmd = [
            'ffmpeg',
            '-re',                      # 以原始帧率读取（重要）
            '-stream_loop', '-1',       # 无限循环播放
            '-i', self.video_file,      # 输入本地视频文件
            
            # 视频编码设置
            '-vcodec', 'libx264',
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-pix_fmt', 'yuv420p',
            
            # 性能优化
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            
            # 码率控制
            '-b:v', '800k',
            '-maxrate', '800k',
            '-bufsize', '800k',
            
            # 关键帧设置
            '-g', '15',
            '-keyint_min', '15',
            
            # 分辨率和帧率
            '-s', '640x480',
            '-r', '15',
            
            # 关键：确保MPEG-TS格式
            '-f', 'mpegts',
            
            # 关键：禁用音频
            '-an',
            
            # 输出优化
            '-fflags', 'nobuffer',
            '-flush_packets', '1',
            
            # 关键：只输出到stdout
            'pipe:1'
        ]

        self.log("🚀 启动FFmpeg处理本地视频...")
        self.log("📝 配置: 本地文件 → H.264 + MPEG-TS + 禁音 + Binary输出")
        
        try:
            # 启动FFmpeg进程
            self.ffmpeg_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL,  # 忽略stderr
                bufsize=0
            )
            self.log("✅ FFmpeg进程启动成功")
            return True
        except Exception as e:
            self.log(f"❌ FFmpeg启动失败: {e}")
            return False

    async def handle_client(self, websocket):
        """处理WebSocket客户端连接"""
        self.clients.add(websocket)
        self.stats['clients_count'] = len(self.clients)
        client_addr = websocket.remote_address
        self.log(f"👤 客户端连接: {client_addr[0]}:{client_addr[1]} (总数: {self.stats['clients_count']})")
        
        try:
            # 等待客户端断开
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            self.stats['clients_count'] = len(self.clients)
            self.log(f"👋 客户端断开: {client_addr[0]}:{client_addr[1]} (总数: {self.stats['clients_count']})")

    async def broadcast_video_stream(self):
        """广播视频流 - 只转发stdout的binary数据"""
        if not self.ffmpeg_process:
            self.log("❌ FFmpeg进程未启动")
            return

        self.log("📡 开始广播本地视频binary流...")
        
        while self.is_running and self.ffmpeg_process.poll() is None:
            try:
                # 从FFmpeg stdout读取binary数据
                chunk = self.ffmpeg_process.stdout.read(1024)
                if not chunk:
                    self.log("⚠️ FFmpeg stdout结束，重启进程...")
                    # 重启FFmpeg进程
                    if self.start_ffmpeg_stream():
                        continue
                    else:
                        break

                # 只有当有客户端时才发送数据
                if self.clients:
                    # 准备要移除的断开客户端
                    disconnected = set()
                    
                    # 向所有客户端发送binary数据
                    for client in self.clients.copy():
                        try:
                            await client.send(chunk)  # 直接发送binary数据
                        except websockets.exceptions.ConnectionClosed:
                            disconnected.add(client)
                        except Exception as e:
                            self.log(f"❌ 发送失败: {e}")
                            disconnected.add(client)
                    
                    # 清理断开的客户端
                    for client in disconnected:
                        self.clients.discard(client)
                    
                    # 更新统计
                    self.stats['bytes_sent'] += len(chunk)
                    self.stats['packets_sent'] += 1
                    
                    # 每1000包输出统计
                    if self.stats['packets_sent'] % 1000 == 0:
                        rate_kb = self.stats['bytes_sent'] / 1024
                        self.log(f"📊 已发送: {self.stats['packets_sent']}包, {rate_kb:.1f}KB, {self.stats['clients_count']}客户端")

                # 避免过度占用CPU
                await asyncio.sleep(0.001)
                
            except Exception as e:
                self.log(f"❌ 广播错误: {e}")
                break

        self.log("🏁 视频流广播结束")

    async def start_server(self):
        """启动WebSocket服务器"""
        self.log(f"🌐 启动本地视频WebSocket服务器 {self.host}:{self.port}")
        self.is_running = True
        
        # 检查视频文件
        if not self.check_video_file():
            return

        # 启动FFmpeg
        if not self.start_ffmpeg_stream():
            return

        try:
            # 启动WebSocket服务器
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            
            self.log("✅ WebSocket服务器启动成功")
            self.log(f"🔗 连接地址: ws://{self.host}:{self.port}")
            self.log("🎯 前端设置: ws.binaryType = 'arraybuffer'")
            self.log("🔄 视频将循环播放")
            
            # 启动视频广播任务
            broadcast_task = asyncio.create_task(self.broadcast_video_stream())
            
            # 等待服务器或广播任务结束
            await asyncio.gather(
                server.wait_closed(),
                broadcast_task,
                return_exceptions=True
            )
            
        except Exception as e:
            self.log(f"❌ 服务器错误: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        self.log("🧹 清理资源...")
        self.is_running = False
        
        # 关闭所有客户端
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
            self.clients.clear()

        # 终止FFmpeg
        if self.ffmpeg_process:
            self.log("🛑 终止FFmpeg进程...")
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()

        # 最终统计
        total_mb = self.stats['bytes_sent'] / (1024 * 1024)
        self.log(f"📈 最终统计: {self.stats['packets_sent']}包, {total_mb:.2f}MB")
        self.log("✅ 清理完成")

# 全局变量
server = None

def signal_handler(signum, frame):
    """信号处理"""
    print(f"\n🛑 收到停止信号 {signum}")
    if server:
        server.is_running = False
    sys.exit(0)

def create_test_video():
    """创建测试视频文件"""
    if not os.path.exists("test_video.mp4"):
        print("🎬 创建测试视频文件...")
        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'testsrc=duration=10:size=640x480:rate=15',
                '-c:v', 'libx264',
                '-preset', 'fast',
                'test_video.mp4'
            ], check=True, capture_output=True)
            print("✅ 测试视频创建成功: test_video.mp4")
            return True
        except subprocess.CalledProcessError:
            print("❌ 创建测试视频失败")
            return False
    return True

async def main():
    """主函数"""
    global server
    
    print("🎥 本地视频WebSocket流测试服务器")
    print("=" * 50)
    print("🎯 特性:")
    print("   ✓ 本地视频文件输入")
    print("   ✓ 确保 -f mpegts 格式")
    print("   ✓ 确保 -an 禁音")
    print("   ✓ Binary模式传输")
    print("   ✓ 只转发stdout")
    print("   ✓ arraybuffer支持")
    print("   ✓ 循环播放")
    print("=" * 50)
    
    # 信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建测试视频（如果不存在）
    create_test_video()
    
    # 创建并启动服务器
    server = LocalVideoWebSocketServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 运行错误: {e}")

if __name__ == '__main__':
    # 检查websockets依赖
    try:
        import websockets
    except ImportError:
        print("❌ 需要安装: pip install websockets")
        sys.exit(1)
    
    # 运行服务器
    asyncio.run(main()) 