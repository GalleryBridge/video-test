#!/usr/bin/env python3
import socket
import subprocess
import time
import threading

def check_process(name, pattern):
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)
        if pattern.lower() in result.stdout.lower():
            return "✅ 运行中"
        else:
            return "❌ 未运行"
    except:
        return "❓ 检查失败"

def check_port(host, port, name):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return f"✅ {name} 端口开放"
        else:
            return f"❌ {name} 端口关闭"
    except:
        return f"❓ {name} 检查失败"

def test_websocket_data():
    try:
        import websocket
        import json
        
        received_data = []
        connected = False
        
        def on_message(ws, message):
            nonlocal received_data
            received_data.append(len(message))
            print(f"📨 接收数据: {len(message)} 字节")
            if len(received_data) >= 3:
                ws.close()
        
        def on_open(ws):
            nonlocal connected
            connected = True
            print("🔗 WebSocket连接成功")
        
        def on_error(ws, error):
            print(f"❌ WebSocket错误: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("🔌 WebSocket连接关闭")
        
        ws = websocket.WebSocketApp("ws://192.168.1.196:8103/video",
                                   on_open=on_open,
                                   on_message=on_message,
                                   on_error=on_error,
                                   on_close=on_close)
        
        # 在线程中运行
        def run_ws():
            ws.run_forever()
        
        ws_thread = threading.Thread(target=run_ws)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 等待5秒
        time.sleep(5)
        
        if connected and received_data:
            return f"✅ 数据正常 - 接收{len(received_data)}包: {received_data}"
        elif connected:
            return "⚠️ 连接成功但无数据"
        else:
            return "❌ 连接失败"
            
    except ImportError:
        return "❓ 缺少websocket库"
    except Exception as e:
        return f"❌ 测试失败: {e}"

def main():
    print("=" * 60)
    print("🔍 系统状态检查")
    print("=" * 60)
    
    # 检查进程
    print("\n📋 进程状态:")
    print(f"FFmpeg: {check_process('FFmpeg', 'ffmpeg')}")
    print(f"Java后端: {check_process('Java', 'java')}")
    
    # 检查端口
    print("\n🔌 端口状态:")
    print(check_port('192.168.1.196', 8101, 'TCP'))
    print(check_port('192.168.1.196', 8103, 'WebSocket'))
    
    # 检查数据流
    print("\n📡 数据流测试:")
    result = test_websocket_data()
    print(result)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 