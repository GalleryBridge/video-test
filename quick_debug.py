#!/usr/bin/env python3
"""
快速诊断脚本 - 检查视频流数据问题
"""

import socket
import subprocess
import time
import threading

def check_ffmpeg_process():
    """检查是否有FFmpeg进程正在运行"""
    print("🔍 检查FFmpeg进程...")
    try:
        # Windows使用tasklist
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ffmpeg.exe'], 
                              capture_output=True, text=True, timeout=5)
        if 'ffmpeg.exe' in result.stdout:
            print("✅ 发现FFmpeg进程正在运行")
            lines = [line for line in result.stdout.split('\n') if 'ffmpeg.exe' in line]
            for line in lines:
                print(f"   📋 {line.strip()}")
            return True
        else:
            print("❌ 没有发现FFmpeg进程")
            return False
    except Exception as e:
        print(f"❌ 检查FFmpeg进程失败: {e}")
        return False

def check_java_backend():
    """检查Java后端是否运行"""
    print("\n🔍 检查Java后端进程...")
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq java.exe'], 
                              capture_output=True, text=True, timeout=5)
        if 'java.exe' in result.stdout:
            print("✅ 发现Java进程正在运行")
            # 检查特定端口
            return check_ports()
        else:
            print("❌ 没有发现Java进程")
            return False
    except Exception as e:
        print(f"❌ 检查Java进程失败: {e}")
        return False

def check_ports():
    """检查关键端口是否开放"""
    print("\n🔍 检查端口状态...")
    
    ports = {
        8101: "TCP数据接收端口",
        8103: "WebSocket端口", 
        8080: "Spring Boot HTTP端口"
    }
    
    all_open = True
    for port, desc in ports.items():
        try:
            with socket.create_connection(('192.168.1.196', port), timeout=3) as sock:
                print(f"✅ 端口 {port} ({desc}) - 开放")
        except Exception as e:
            print(f"❌ 端口 {port} ({desc}) - 关闭: {e}")
            all_open = False
    
    return all_open

def test_rtsp_quickly():
    """快速测试RTSP连接"""
    print("\n🔍 快速测试RTSP连接...")
    rtsp_url = "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0"
    
    try:
        # 简单的FFmpeg测试，只读取1帧
        cmd = [
            'ffmpeg', 
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-frames', '1',
            '-f', 'null',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 or "Stream #0" in result.stderr:
            print("✅ RTSP连接正常")
            return True
        else:
            print("❌ RTSP连接失败")
            print(f"   错误信息: {result.stderr[-200:]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ RTSP连接测试超时")
        return False
    except Exception as e:
        print(f"❌ RTSP测试异常: {e}")
        return False

def test_data_flow():
    """测试数据流是否正常"""
    print("\n🔍 测试WebSocket数据流...")
    
    try:
        import websocket
        
        data_received = False
        
        def on_message(ws, message):
            nonlocal data_received
            data_received = True
            print(f"✅ 收到数据: {len(message)} 字节")
            ws.close()  # 收到数据后立即关闭
        
        def on_error(ws, error):
            print(f"❌ WebSocket错误: {error}")
        
        def on_open(ws):
            print("✅ WebSocket连接成功，等待数据...")
            # 5秒后超时
            threading.Timer(5.0, lambda: ws.close() if not data_received else None).start()
        
        ws = websocket.WebSocketApp("ws://192.168.1.196:8103/video",
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error)
        
        ws.run_forever()
        
        return data_received
        
    except ImportError:
        print("📦 需要安装websocket-client: pip install websocket-client")
        return False
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("🚨 视频流数据问题快速诊断")
    print("=" * 60)
    
    issues = []
    
    # 1. 检查FFmpeg进程
    if not check_ffmpeg_process():
        issues.append("FFmpeg脚本未运行")
    
    # 2. 检查后端服务
    if not check_java_backend():
        issues.append("后端服务未启动或端口未开放")
    
    # 3. 检查RTSP连接
    if not test_rtsp_quickly():
        issues.append("RTSP摄像头连接异常")
    
    # 4. 测试数据流
    if not test_data_flow():
        issues.append("WebSocket没有接收到数据")
    
    print("\n" + "=" * 60)
    print("📋 诊断结果:")
    print("=" * 60)
    
    if not issues:
        print("🎉 所有检查通过！数据流应该正常")
    else:
        print("⚠️  发现以下问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 解决建议:")
        if "FFmpeg脚本未运行" in issues:
            print("   📌 运行: python ffmpeg_linux.py")
        if "后端服务未启动" in issues:
            print("   📌 启动Spring Boot后端服务")
        if "RTSP摄像头连接异常" in issues:
            print("   📌 检查摄像头IP、用户名密码")
        if "WebSocket没有接收到数据" in issues:
            print("   📌 确保前面的问题都解决后重试")

if __name__ == "__main__":
    main() 