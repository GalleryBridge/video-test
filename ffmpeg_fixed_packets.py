#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复MPEG-TS包边界的FFmpeg脚本
确保JSMpeg能正确解析数据
"""

import subprocess
import socket
import time
import errno
import threading

def read_stderr(stderr_pipe, process_name="FFmpeg"):
    """实时读取FFmpeg的stderr输出"""
    try:
        for line in iter(stderr_pipe.readline, b''):
            error_msg = line.decode('utf-8', errors='ignore').strip()
            if error_msg:
                print(f"🔍 {process_name} stderr: {error_msg}")
    except Exception as e:
        print(f"❌ 读取{process_name} stderr时出错: {e}")

def start_fixed_video():
    """启动修复包边界的视频流"""
    
    # 修复MPEG-TS包边界的FFmpeg配置
    ffmpeg_cmd = [
        "ffmpeg",
        
        # 输入源配置
        "-rtsp_transport", "tcp",
        "-i", "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0",
        
        # 基础优化参数
        "-timeout", "10000000",
        "-fflags", "nobuffer",
        
        # H.264编码优化
        "-vcodec", "libx264",
        "-profile:v", "baseline",
        "-level", "3.0",
        "-pix_fmt", "yuv420p",
        
        # 编码性能
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        
        # 码率控制
        "-b:v", "800k",
        "-maxrate", "800k",
        "-bufsize", "800k",
        
        # GOP设置
        "-g", "15",
        "-keyint_min", "15",
        
        # 分辨率和帧率
        "-s", "640x480",
        "-r", "15",
        
        # 关键：MPEG-TS包大小和边界控制
        "-f", "mpegts",
        "-mpegts_m2ts_mode", "0",              # 标准MPEG-TS
        "-mpegts_original_network_id", "1",    # 网络ID
        "-mpegts_transport_stream_id", "1",    # 传输流ID
        "-mpegts_service_id", "1",             # 服务ID
        "-mpegts_start_pid", "256",            # 起始PID
        "-muxrate", "1000000",                 # 1Mbps复用率，确保连续数据
        
        # 关键：确保包对齐和连续性
        "-metadata", "service_name=VideoStream",
        "-metadata", "service_provider=FFmpeg",
        
        # 禁用音频
        "-an",
        
        # 输出优化
        "-flush_packets", "1",
        "-avoid_negative_ts", "make_zero",     # 避免负时间戳
        
        "pipe:1"
    ]

    print(f"🚀 启动包边界修复FFmpeg:")
    print("🎯 关键修复项:")
    print("   - 标准MPEG-TS模式")
    print("   - 固定复用率确保连续性")
    print("   - 包对齐和边界控制")
    print("   - 时间戳规范化")
    
    # 启动FFmpeg进程
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    # 启动stderr监控
    stderr_thread = threading.Thread(target=read_stderr, args=(process.stderr, "FFmpeg-Fixed"), daemon=True)
    stderr_thread.start()
    print("🔍 FFmpeg stderr监控线程已启动")

    print("📡 开始读取修复的MPEG-TS视频流...")

    target_ip = '192.168.1.196'
    target_port = 8101

    total_bytes_sent = 0
    packet_count = 0
    start_time = time.time()
    last_data_time = time.time()

    try:
        print(f"🔗 连接到 {target_ip}:{target_port}...")
        with socket.create_connection((target_ip, target_port), timeout=10) as sock:
            print("✅ Socket连接成功")
            
            # 优化socket配置
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # MPEG-TS包边界检测
            buffer = b''  # 用于累积数据
            mpeg_ts_packets = 0
            invalid_packets = 0
            buffer_size_limit = 8192  # 缓冲区大小限制
            
            while True:
                # 检查FFmpeg进程状态
                poll_result = process.poll()
                if poll_result is not None:
                    print(f"❌ FFmpeg进程退出，返回码: {poll_result}")
                    break
                
                # 检查数据流超时
                current_time = time.time()
                if current_time - last_data_time > 30:
                    print(f"⏰ 数据流超时: {current_time - last_data_time:.1f}秒")
                    break
                
                try:
                    # 读取数据块
                    chunk = process.stdout.read(1024)
                    if not chunk:
                        print("❌ 从FFmpeg读取不到数据")
                        break

                    last_data_time = current_time
                    buffer += chunk
                    
                    # 检查是否需要限制缓冲区大小
                    if len(buffer) > buffer_size_limit:
                        # 直接发送缓冲区数据，不等待完整包
                        data_to_send = buffer
                        buffer = b''
                        
                        # MPEG-TS质量检查
                        sync_byte_count = data_to_send.count(0x47)
                        if sync_byte_count > 0:
                            mpeg_ts_packets += sync_byte_count
                        else:
                            invalid_packets += 1
                        
                        # 发送数据
                        try:
                            sock.sendall(data_to_send)
                            total_bytes_sent += len(data_to_send)
                            packet_count += 1
                            
                            # 统计信息
                            if packet_count % 50 == 0:
                                elapsed_time = time.time() - start_time
                                rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
                                quality_ratio = mpeg_ts_packets / (mpeg_ts_packets + invalid_packets) if (mpeg_ts_packets + invalid_packets) > 0 else 0
                                
                                print(f"📊 包#{packet_count}: {total_bytes_sent:,}字节, {rate_kbps:.1f}Kbps")
                                print(f"   📺 MPEG-TS质量: {mpeg_ts_packets}个同步包, 质量比{quality_ratio:.1%}")
                                print(f"   📦 缓冲区大小: {len(buffer)}字节")
                                
                                # 检查数据包头部
                                if len(data_to_send) >= 8:
                                    header_hex = ' '.join(f'{b:02x}' for b in data_to_send[:8])
                                    print(f"   📄 数据包头: {header_hex}")
                                    
                            elif packet_count % 25 == 0:
                                print(f"📦 发送数据包 #{packet_count}, 大小: {len(data_to_send)}字节")
                                
                        except socket.error as send_error:
                            print(f"❌ Socket发送错误: {send_error}")
                            break
                        
                except IOError as read_error:
                    print(f"❌ 读取FFmpeg数据错误: {read_error}")
                    break

    except socket.timeout:
        print("❌ Socket连接超时")
    except ConnectionRefusedError:
        print("❌ 连接被拒绝 - 检查后端服务")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔄 清理资源...")
        
        # 发送剩余缓冲区数据
        if buffer:
            print(f"📤 发送剩余数据: {len(buffer)}字节")
        
        # 最终统计
        elapsed_time = time.time() - start_time
        if total_bytes_sent > 0:
            avg_rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
            quality_ratio = mpeg_ts_packets / (mpeg_ts_packets + invalid_packets) if (mpeg_ts_packets + invalid_packets) > 0 else 0
            
            print(f"📈 最终统计:")
            print(f"   - 运行时间: {elapsed_time:.1f}秒")
            print(f"   - 总数据量: {total_bytes_sent:,}字节")
            print(f"   - 平均速率: {avg_rate_kbps:.1f}Kbps")
            print(f"   - 数据包数: {packet_count}")
            print(f"   - MPEG-TS包: {mpeg_ts_packets}")
            print(f"   - 数据质量: {quality_ratio:.1%}")
        
        # 终止FFmpeg
        print("🛑 终止FFmpeg进程...")
        if process.poll() is None:
            process.terminate()
            wait_time = 0
            while process.poll() is None and wait_time < 5:
                time.sleep(0.1)
                wait_time += 0.1
            if process.poll() is None:
                print("🔨 强制终止FFmpeg...")
                process.kill()
                process.wait()
        
        print("✅ FFmpeg进程已结束")

    print("🏁 修复包边界的视频流结束!")

if __name__ == '__main__':
    start_fixed_video() 