#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的FFmpeg视频流推送脚本
专门针对JSMpeg播放器优化
"""

import subprocess
import socket
import time
import errno
import threading

def byte_to_hex(byte_data):
    return ' '.join(format(b, '02x') for b in byte_data)

def read_stderr(stderr_pipe, process_name="FFmpeg"):
    """实时读取FFmpeg的stderr输出"""
    try:
        for line in iter(stderr_pipe.readline, b''):
            error_msg = line.decode('utf-8', errors='ignore').strip()
            if error_msg:
                print(f"🔍 {process_name} stderr: {error_msg}")
    except Exception as e:
        print(f"❌ 读取{process_name} stderr时出错: {e}")

def start_optimized_video():
    """启动优化的视频流"""
    
    # JSMpeg优化的FFmpeg配置
    ffmpeg_cmd = [
        "ffmpeg",
        
        # 输入源配置
        "-rtsp_transport", "tcp",
        "-i", "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0",
        
        # 基础优化参数
        "-timeout", "10000000",      # 10秒超时
        "-fflags", "nobuffer",       # 禁用缓冲，减少延迟
        
        # H.264编码优化 - JSMpeg兼容配置
        "-vcodec", "libx264",
        "-profile:v", "baseline",    # 基线档次，最佳兼容性
        "-level", "3.0",             # H.264级别3.0
        "-pix_fmt", "yuv420p",       # 标准像素格式
        
        # 编码性能优化
        "-preset", "ultrafast",      # 最快编码
        "-tune", "zerolatency",      # 零延迟调优
        
        # 码率和质量控制
        "-b:v", "800k",              # 固定码率800kbps
        "-maxrate", "800k",          # 最大码率
        "-bufsize", "800k",          # 缓冲区大小等于码率
        "-crf", "28",                # 恒定质量因子
        
        # GOP和关键帧设置
        "-g", "15",                  # GOP大小15帧(1秒1个关键帧)
        "-keyint_min", "15",         # 最小关键帧间隔
        "-force_key_frames", "expr:gte(t,n_forced*1)",  # 强制每秒一个关键帧
        
        # 分辨率和帧率
        "-s", "640x480",             # 分辨率
        "-r", "15",                  # 帧率15fps
        
        # MPEG-TS容器优化 - 关键配置
        "-f", "mpegts",              # MPEG-TS格式
        "-mpegts_m2ts_mode", "0",    # 标准MPEG-TS模式(非M2TS)
        "-mpegts_copyts", "1",       # 复制时间戳
        "-mpegts_start_pid", "256",  # 起始PID
        "-muxrate", "1000000",       # 复用码率1Mbps，确保数据连续性
        
        # 禁用音频
        "-an",
        
        # 输出配置
        "-flush_packets", "1",       # 立即刷新数据包
        "pipe:1"                     # 输出到stdout
    ]

    print(f"🚀 启动JSMpeg优化FFmpeg:")
    print("🎯 关键优化项:")
    print("   - H.264基线档次(最佳兼容性)")
    print("   - 标准MPEG-TS格式")
    print("   - 固定码率和GOP")
    print("   - 强制关键帧和时间戳")
    print("   - 连续数据流保证")
    
    for i, param in enumerate(ffmpeg_cmd):
        if i % 6 == 0:
            print(f"\n   {param}", end="")
        else:
            print(f" {param}", end="")
    print("\n")
    
    # 启动FFmpeg进程
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    # 启动stderr监控
    stderr_thread = threading.Thread(target=read_stderr, args=(process.stderr, "FFmpeg-Optimized"), daemon=True)
    stderr_thread.start()
    print("🔍 FFmpeg stderr监控线程已启动")

    print("📡 开始读取优化的H.264视频流...")

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

            # 数据质量监控变量
            mpeg_ts_packets = 0
            invalid_packets = 0
            
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
                    # 读取数据 - 使用较小的缓冲区确保及时性
                    chunk = process.stdout.read(1024)
                    if not chunk:
                        print("❌ 从FFmpeg读取不到数据")
                        break

                    last_data_time = current_time

                    # MPEG-TS包质量检查
                    if len(chunk) > 0:
                        # 检查MPEG-TS同步字节
                        sync_byte_count = chunk.count(0x47)  # MPEG-TS同步字节
                        if sync_byte_count > 0:
                            mpeg_ts_packets += sync_byte_count
                        else:
                            invalid_packets += 1
                    
                    # 发送数据
                    try:
                        sock.sendall(chunk)
                        total_bytes_sent += len(chunk)
                        packet_count += 1
                        
                        # 详细统计信息
                        if packet_count % 100 == 0:
                            elapsed_time = time.time() - start_time
                            rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
                            quality_ratio = mpeg_ts_packets / (mpeg_ts_packets + invalid_packets) if (mpeg_ts_packets + invalid_packets) > 0 else 0
                            
                            print(f"📊 包#{packet_count}: {total_bytes_sent:,}字节, {rate_kbps:.1f}Kbps")
                            print(f"   📺 MPEG-TS质量: {mpeg_ts_packets}个同步包, 质量比{quality_ratio:.1%}")
                            
                            # 检查数据包头部(调试用)
                            if len(chunk) >= 4:
                                header_hex = ' '.join(f'{b:02x}' for b in chunk[:4])
                                print(f"   📄 数据包头: {header_hex}")
                        
                        elif packet_count % 50 == 0:
                            print(f"📦 发送数据包 #{packet_count}, 大小: {len(chunk)}字节")
                            
                    except socket.error as send_error:
                        print(f"❌ Socket发送错误: {send_error}")
                        if hasattr(send_error, 'errno'):
                            if send_error.errno == errno.ECONNRESET:
                                print("🔴 远程服务器重置连接")
                            elif send_error.errno == errno.EPIPE:
                                print("🔴 管道断开")
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

    print("🏁 优化视频流结束!")

if __name__ == '__main__':
    start_optimized_video() 