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
            if error_msg:  # 只打印非空行
                print(f"🔍 {process_name} stderr: {error_msg}")
    except Exception as e:
        print(f"❌ 读取{process_name} stderr时出错: {e}")

def start_video():
    ffmpeg_cmd = [
        "ffmpeg",  # 假设ffmpeg已安装并在PATH中
        "-rtsp_transport", "tcp",
        "-i", "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0",
        
        # 基础网络参数 (广泛兼容)
        "-timeout", "10000000",      # 设置超时时间 (10秒，以微秒计)
        "-buffer_size", "1024000",   # 增加缓冲区大小
        
        # 低延迟视频处理参数
        "-vcodec", "libx264",        # 使用H.264编码器
        "-preset", "ultrafast",      # 最快编码预设
        "-tune", "zerolatency",      # 零延迟调优
        
        # 关键帧和码率设置 - 重点优化
        "-g", "15",                  # GOP大小改为15 (1秒一个关键帧)
        "-keyint_min", "15",         # 最小关键帧间隔15
        "-crf", "28",                # 提高CRF值，减少码率
        "-maxrate", "800k",          # 降低最大码率到800k
        "-bufsize", "1600k",         # 缓冲区大小为码率的2倍
        
        # 实时流优化 (基础参数)
        "-fflags", "nobuffer",       # 禁用缓冲

        # 分辨率和帧率
        "-s", "640x480",             # 分辨率
        "-r", "15",                  # 帧率15fps

        # 输出格式：MPEG-TS流 (简化参数)
        "-f", "mpegts",              # 输出MPEG-TS格式
        "-muxrate", "800k",          # 复用码率与视频码率一致
        "-an",                       # 禁用音频
        "pipe:1"                     # 输出到stdout
    ]

    print(f"🚀 启动FFmpeg命令: {' '.join(ffmpeg_cmd)}")
    print("🎯 优化参数 (兼容版本):")
    print("   - GOP大小: 15 (1秒1个关键帧)")
    print("   - 码率: 800k (降低带宽需求)")
    print("   - 延迟优化: 禁用缓冲")
    print("   - 移除了不兼容的高级参数")
    
    # 启动 ffmpeg 进程
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    # 启动stderr监控线程
    stderr_thread = threading.Thread(target=read_stderr, args=(process.stderr, "FFmpeg"), daemon=True)
    stderr_thread.start()
    print("🔍 FFmpeg stderr监控线程已启动")

    print("start reading H.264 video stream...")

    target_ip = '192.168.1.196'
    target_port = 8101

    total_bytes_sent = 0
    packet_count = 0
    start_time = time.time()
    last_data_time = time.time()  # 记录最后一次收到数据的时间

    try:
        print(f"🔗 尝试连接到 {target_ip}:{target_port}...")
        with socket.create_connection((target_ip, target_port), timeout=10) as sock:
            print("✅ Socket连接成功: {}:{}".format(target_ip, target_port))
            
            # 设置socket选项 - 优化网络传输
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 禁用Nagle算法

            while True:
                # 检查ffmpeg进程状态
                poll_result = process.poll()
                if poll_result is not None:
                    print(f"❌ FFmpeg进程已退出，返回码: {poll_result}")
                    if poll_result != 0:
                        print("⚠️  FFmpeg异常退出，可能原因:")
                        print("   - RTSP源断开连接")
                        print("   - 网络连接超时")
                        print("   - 摄像头访问被限制")
                        print("   - 认证失败")
                        print("   - FFmpeg参数不兼容")
                    else:
                        print("✅ FFmpeg正常退出")
                    break
                
                # 检查数据流超时
                current_time = time.time()
                if current_time - last_data_time > 30:  # 30秒没有数据
                    print(f"⏰ 数据流超时: {current_time - last_data_time:.1f}秒没有收到数据")
                    break
                
                try:
                    # 读取数据块 - 使用更小的缓冲区减少延迟
                    chunk = process.stdout.read(1024)  # 从4096改为1024
                    if not chunk:
                        print("❌ 从FFmpeg读取不到数据，流可能已结束")
                        print("💡 可能原因:")
                        print("   - FFmpeg进程正常结束")
                        print("   - RTSP流结束")
                        print("   - 管道被关闭")
                        print("   - FFmpeg启动失败(参数错误)")
                        break

                    last_data_time = current_time  # 更新最后数据时间

                    # 发送原始H.264数据
                    try:
                        sock.sendall(chunk)
                        total_bytes_sent += len(chunk)
                        packet_count += 1
                        
                        # 每200个包显示一次统计信息，每100个包显示简要信息
                        if packet_count % 200 == 0:
                            elapsed_time = time.time() - start_time
                            rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
                            print(f"📊 已发送: {packet_count}包, {total_bytes_sent:,}字节, 速率: {rate_kbps:.1f}Kbps")
                        elif packet_count % 100 == 0:
                            print(f"📦 数据包 #{packet_count}, 大小: {len(chunk)}字节")
                        else:
                            print("Sent {} bytes of H.264 data".format(len(chunk)))
                            
                    except socket.error as send_error:
                        print(f"❌ Socket发送错误: {send_error}")
                        if hasattr(send_error, 'errno'):
                            if send_error.errno == errno.ECONNRESET:
                                print("🔴 远程服务器重置了连接 (ECONNRESET)")
                                print("💡 可能原因: 后端服务器崩溃或重启")
                            elif send_error.errno == errno.EPIPE:
                                print("🔴 管道断开，远程服务器关闭了连接 (EPIPE)")
                                print("💡 可能原因: 后端服务器主动关闭连接")
                            elif send_error.errno == errno.ECONNABORTED:
                                print("🔴 连接被中止 (ECONNABORTED)")
                            else:
                                print(f"🔴 其他Socket错误: errno={send_error.errno}")
                        break
                        
                except IOError as read_error:
                    print(f"❌ 从FFmpeg读取数据时出错: {read_error}")
                    print("💡 可能原因:")
                    print("   - FFmpeg进程崩溃")
                    print("   - 管道被意外关闭")
                    break

    except socket.timeout:
        print("❌ Socket连接超时")
        print("💡 检查项目:")
        print(f"   - 目标服务器 {target_ip}:{target_port} 是否运行")
        print("   - 防火墙是否阻止连接")
        print("   - 网络是否通畅")
    except ConnectionRefusedError:
        print("❌ 连接被拒绝")
        print("💡 检查项目:")
        print(f"   - 后端服务器 {target_ip}:{target_port} 是否启动")
        print("   - 端口号是否正确")
        print("   - 服务是否正在监听该端口")
    except ConnectionResetError:
        print("❌ 连接被重置")
        print("💡 可能原因: 网络中断或服务器强制断开")
    except socket.error as e:
        print("❌ Socket错误: {}".format(e))
        print("💡 建议检查网络连接和服务器状态")
    except Exception as e:
        print("❌ 未知错误: {}".format(e))
        import traceback
        traceback.print_exc()
        print("💡 请将错误信息提供给开发者")
    finally:
        print("🔄 正在清理资源...")
        
        # 显示最终统计
        elapsed_time = time.time() - start_time
        if total_bytes_sent > 0:
            avg_rate_kbps = (total_bytes_sent * 8) / (elapsed_time * 1024) if elapsed_time > 0 else 0
            print(f"📈 传输统计:")
            print(f"   - 运行时间: {elapsed_time:.1f}秒")
            print(f"   - 总数据量: {total_bytes_sent:,}字节 ({total_bytes_sent/1024/1024:.2f}MB)")
            print(f"   - 平均速率: {avg_rate_kbps:.1f}Kbps")
            print(f"   - 数据包数: {packet_count}")
        
        print("🛑 正在终止FFmpeg进程...")
        if process.poll() is None:
            process.terminate()

            # 等待进程结束
            wait_time = 0
            while process.poll() is None and wait_time < 5:
                time.sleep(0.1)
                wait_time += 0.1

            # 如果还没结束，强制终止
            if process.poll() is None:
                print("🔨 强制终止FFmpeg进程...")
                process.kill()
                process.wait()
        
        print("✅ FFmpeg进程已结束")

    print("🏁 video stream finished!")

if __name__ == '__main__':
    start_video()