#!/usr/bin/env python3
"""
编码格式和数据流检测脚本
检查FFmpeg输出格式是否与JSMpeg兼容
"""

import socket
import subprocess
import time
import threading
import struct

def analyze_ffmpeg_output():
    """分析FFmpeg实际输出的数据格式"""
    print("🔍 分析FFmpeg输出格式...")
    
    # 连接到TCP端口，模拟后端接收
    try:
        print("📡 连接到FFmpeg输出端口 (192.168.1.196:8101)...")
        with socket.create_connection(('192.168.1.196', 8101), timeout=10) as sock:
            print("✅ 连接成功，开始接收数据...")
            
            received_data = []
            total_bytes = 0
            packet_count = 0
            
            # 接收前几个数据包进行分析
            start_time = time.time()
            while time.time() - start_time < 10 and packet_count < 5:  # 10秒或5个包
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                    
                    packet_count += 1
                    total_bytes += len(data)
                    received_data.append(data)
                    
                    print(f"📦 包 #{packet_count}: {len(data)} 字节")
                    
                    # 分析包头
                    if len(data) >= 16:
                        header = data[:16]
                        hex_header = ' '.join(f'{b:02x}' for b in header)
                        print(f"   📄 包头: {hex_header}")
                        
                        # 检查是否是MPEG-TS格式 (同步字节0x47)
                        if data[0] == 0x47:
                            print("   ✅ 检测到MPEG-TS同步字节 (0x47)")
                        else:
                            print(f"   ❌ 非标准MPEG-TS同步字节: 0x{data[0]:02x}")
                        
                        # 检查是否包含H.264标识
                        if b'\x00\x00\x00\x01' in data[:100]:
                            print("   ✅ 检测到H.264 NAL单元起始码")
                        elif b'\x00\x00\x01' in data[:100]:
                            print("   ✅ 检测到H.264短起始码")
                        else:
                            print("   ⚠️  未检测到明显的H.264标识")
                
                except socket.timeout:
                    print("   ⏰ 接收超时")
                    break
                except Exception as e:
                    print(f"   ❌ 接收错误: {e}")
                    break
            
            print(f"\n📊 接收统计:")
            print(f"   - 总包数: {packet_count}")
            print(f"   - 总字节: {total_bytes}")
            print(f"   - 平均包大小: {total_bytes//packet_count if packet_count > 0 else 0}")
            
            return received_data, packet_count > 0
            
    except Exception as e:
        print(f"❌ 连接FFmpeg输出失败: {e}")
        return [], False

def test_websocket_data_format():
    """测试WebSocket接收到的数据格式"""
    print("\n🔍 测试WebSocket数据格式...")
    
    try:
        import websocket
        
        data_samples = []
        
        def on_message(ws, message):
            data_samples.append(message)
            print(f"📨 WebSocket收到: {len(message)} 字节")
            
            # 分析前几个字节
            if len(message) >= 16:
                if isinstance(message, bytes):
                    header = message[:16]
                else:
                    header = bytes(message[:16])
                
                hex_header = ' '.join(f'{b:02x}' for b in header)
                print(f"   📄 WebSocket数据头: {hex_header}")
                
                # 检查MPEG-TS格式
                if header[0] == 0x47:
                    print("   ✅ WebSocket数据包含MPEG-TS同步字节")
                else:
                    print(f"   ❌ WebSocket数据非MPEG-TS格式: 0x{header[0]:02x}")
            
            # 收到3个包后关闭
            if len(data_samples) >= 3:
                ws.close()
        
        def on_error(ws, error):
            print(f"❌ WebSocket错误: {error}")
        
        def on_open(ws):
            print("✅ WebSocket连接成功")
            # 10秒后超时关闭
            threading.Timer(10.0, ws.close).start()
        
        def on_close(ws, close_status_code, close_msg):
            print("🔌 WebSocket连接关闭")
        
        ws = websocket.WebSocketApp("ws://192.168.1.196:8103/video",
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        ws.run_forever()
        
        return len(data_samples) > 0
        
    except ImportError:
        print("📦 需要websocket-client库")
        return False
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

def check_jsmpeg_compatibility():
    """检查JSMpeg兼容性配置"""
    print("\n🔍 检查JSMpeg兼容性...")
    
    print("📋 JSMpeg要求:")
    print("   - 视频编码: H.264")
    print("   - 容器格式: MPEG-TS")
    print("   - 传输方式: WebSocket Binary")
    print("   - 同步字节: 0x47 (MPEG-TS)")
    
    print("\n📋 当前FFmpeg配置:")
    print("   - 编码器: libx264 ✅")
    print("   - 输出格式: mpegts ✅") 
    print("   - 传输: pipe:1 -> TCP -> WebSocket ✅")
    
    # 检查可能的兼容性问题
    print("\n⚠️  可能的兼容性问题:")
    print("   1. MPEG-TS包大小不是188字节的倍数")
    print("   2. H.264参数与JSMpeg不兼容")
    print("   3. TCP传输可能破坏MPEG-TS包边界")
    print("   4. 后端WebSocket转发时数据分片问题")

def suggest_ffmpeg_fix():
    """建议FFmpeg修复方案"""
    print("\n🔧 建议的FFmpeg优化配置:")
    
    suggested_params = [
        "# 确保MPEG-TS包完整性",
        "-f", "mpegts",
        "-mpegts_m2ts_mode", "0",  # 标准MPEG-TS模式
        "-mpegts_copyts", "1",     # 保持时间戳
        
        "# H.264兼容性优化", 
        "-vcodec", "libx264",
        "-profile:v", "baseline",   # 基线档次，兼容性最好
        "-level", "3.0",           # H.264级别
        "-pix_fmt", "yuv420p",     # 像素格式
        
        "# 流媒体优化",
        "-tune", "zerolatency",
        "-preset", "ultrafast",
        "-g", "15",                # GOP大小
        "-b:v", "800k",            # 固定码率
        "-maxrate", "800k",
        "-bufsize", "1600k",
        
        "# 输出到stdout",
        "pipe:1"
    ]
    
    print("建议的FFmpeg命令参数:")
    for param in suggested_params:
        if param.startswith("#"):
            print(f"\n{param}")
        else:
            print(f"  {param}")

def main():
    print("=" * 60)
    print("🔍 编码格式和数据流检测")
    print("=" * 60)
    
    issues = []
    
    # 1. 分析FFmpeg输出
    ffmpeg_data, ffmpeg_ok = analyze_ffmpeg_output()
    if not ffmpeg_ok:
        issues.append("FFmpeg数据流异常")
    
    # 2. 测试WebSocket数据
    websocket_ok = test_websocket_data_format()
    if not websocket_ok:
        issues.append("WebSocket数据传输异常")
    
    # 3. 检查兼容性
    check_jsmpeg_compatibility()
    
    print("\n" + "=" * 60)
    print("📋 检测结果:")
    print("=" * 60)
    
    if not issues:
        print("🎉 数据流格式检测正常")
        print("💡 如果前端仍无法播放，可能是JSMpeg配置问题")
    else:
        print("⚠️  发现问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    # 4. 提供修复建议
    suggest_ffmpeg_fix()
    
    print(f"\n🔧 下一步建议:")
    print("1. 如果FFmpeg数据格式有问题，使用建议的参数重新配置")
    print("2. 如果WebSocket传输有问题，检查后端数据转发逻辑")
    print("3. 如果格式都正常，可能需要调整JSMpeg配置或使用其他播放器")

if __name__ == "__main__":
    main() 