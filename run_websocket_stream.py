#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动WebSocket视频流服务器
"""

import subprocess
import sys
import os

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    try:
        import websockets
        print("✅ websockets库已安装")
    except ImportError:
        print("❌ 缺少websockets库")
        print("正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        print("✅ websockets库安装完成")

def main():
    """主函数"""
    print("🎥 WebSocket视频流服务器启动器")
    print("=" * 40)
    
    # 检查依赖
    check_dependencies()
    
    # 检查FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg未安装或不在PATH中")
        print("请先安装FFmpeg: https://ffmpeg.org/download.html")
        return
    
    print("\n🚀 启动WebSocket视频流服务器...")
    print("📝 使用配置:")
    print("   - 服务器地址: 192.168.1.196:8103")
    print("   - 视频格式: H.264/MPEG-TS")
    print("   - 分辨率: 640x480")
    print("   - 帧率: 15fps")
    print("\n🌐 前端访问:")
    print("   - 打开 jsmpeg-player.html")
    print("   - 服务器地址填写: 192.168.1.196")
    print("   - 端口: 8103")
    print("\n按 Ctrl+C 停止服务器")
    print("-" * 40)
    
    # 运行WebSocket服务器
    try:
        from ffmpeg_websocket_stream import main as ws_main
        import asyncio
        asyncio.run(ws_main())
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    main() 