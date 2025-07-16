#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H.264裸流FFmpeg脚本
避开MPEG-TS包边界问题，直接输出H.264数据
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

def start_h264_raw():
    """启动H.264裸流输出"""
    
    # H.264裸流FFmpeg配置
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
        
        # 关键：直接输出H.264裸流，避开MPEG-TS
        "-f", "h264",                    # H.264裸流格式
        "-bsf:v", "h264_mp4toannexb",   # 转换为Annex-B格式（带起始码）
        
        # 禁用音频
        "-an",
        
        # 输出优化
        "-flush_packets", "1",
        
        "pipe:1"
    ]

    print(f"🚀 启动H.264裸流FFmpeg:")
    print("🎯 关键特性:")
    print("   - H.264裸流格式（避开MPEG-TS）")
    print("   - Annex-B格式（带起始码）")
    print("   - 基线档次最佳兼容性")
    print("   - 无包边界问题")
    
    # 启动FFmpeg进程
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    # 启动stderr监控
    stderr_thread = threading.Thread(target=read_stderr, args=(process.stderr, "FFmpeg-H264"), daemon=True)
    stderr_thread.start()
    print("🔍 FFmpeg stderr监控线程已启动")

    print("📡 开始读取H.264裸流...")

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

            # H.264数据质量监控
            nal_units = 0
            keyframes = 0
            
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
                    
                    # H.264 NAL单元检测
                    nal_start_codes = chunk.count(b'\x00\x00\x00\x01')  # 4字节起始码
                    nal_start_codes += chunk.count(b'\x00\x00\x01')     # 3字节起始码
                    
                    if nal_start_codes > 0:
                        nal_units += nal_start_codes
                        
                        # 检查是否包含关键帧（IDR帧）
                        # NAL类型5是IDR帧
                        if b'\x00\x00\x00\x01\x65' in chunk or b'\x00\x00\x01\x65' in chunk:
                            keyframes += 1
                    
                    # 发送数据
                    try:
                        sock.sendall(chunk)
                        total_bytes_sent += len(chunk)
                        packet_count += 1
                        
                        # 统计信息
                        if packet_count % 100 == 0:
                            elapsed_time = time.time() - start_time
                            rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
                            
                            print(f"📊 包#{packet_count}: {total_bytes_sent:,}字节, {rate_kbps:.1f}Kbps")
                            print(f"   🎬 H.264统计: {nal_units}个NAL单元, {keyframes}个关键帧")
                            
                            # 检查数据包头部
                            if len(chunk) >= 8:
                                header_hex = ' '.join(f'{b:02x}' for b in chunk[:8])
                                print(f"   📄 数据包头: {header_hex}")
                                
                                # 检查是否为H.264起始码
                                if chunk.startswith(b'\x00\x00\x00\x01') or chunk.startswith(b'\x00\x00\x01'):
                                    print(f"   ✅ 检测到H.264起始码")
                                    
                        elif packet_count % 50 == 0:
                            print(f"📦 发送H.264数据包 #{packet_count}, 大小: {len(chunk)}字节")
                            
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
        
        # 最终统计
        elapsed_time = time.time() - start_time
        if total_bytes_sent > 0:
            avg_rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
            
            print(f"📈 最终统计:")
            print(f"   - 运行时间: {elapsed_time:.1f}秒")
            print(f"   - 总数据量: {total_bytes_sent:,}字节")
            print(f"   - 平均速率: {avg_rate_kbps:.1f}Kbps")
            print(f"   - 数据包数: {packet_count}")
            print(f"   - NAL单元: {nal_units}")
            print(f"   - 关键帧: {keyframes}")
        
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

    print("🏁 H.264裸流结束!")

if __name__ == '__main__':
    start_h264_raw() 