import subprocess
import socket

def byte_to_hex(byte_data):
    return ' '.join(format(b, '02x') for b in byte_data)

def start_video():
    ffmpeg_cmd = [
        "ffmpeg",  # 假设ffmpeg已安装并在PATH中
        "-rtsp_transport", "tcp",
        "-i", "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0",

        # 视频处理参数
        "-vcodec", "libx264",      # 使用H.264编码器
        "-preset", "ultrafast",    # 最快编码预设，减少延迟
        "-tune", "zerolatency",    # 零延迟调优
        "-crf", "23",              # 恒定质量因子
        "-maxrate", "1M",          # 最大比特率1Mbps
        "-bufsize", "2M",          # 缓冲区大小
        "-g", "30",                # GOP大小（关键帧间隔）
        "-keyint_min", "30",       # 最小关键帧间隔

        # 分辨率和帧率
        "-s", "640x480",           # 分辨率
        "-r", "15",                # 帧率15fps

        # 输出格式：MPEG-TS流
        "-f", "mpegts",            # 输出MPEG-TS格式，兼容JSMpeg解码器
        "-muxrate", "1M",          # 复用码率
        "-pcr_period", "20",       # PCR间隔
        "-pat_period", "0.1",      # PAT周期
        "-an",                     # 禁用音频
        "pipe:1"                   # 输出到stdout
    ]

    # 启动 ffmpeg 进程
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    print("start reading H.264 video stream...")

    target_ip = '192.168.1.196'
    target_port = 8101

    try:
        with socket.create_connection((target_ip, target_port), timeout=5) as sock:
            print("Connected to {}:{}".format(target_ip, target_port))

            while True:
                # 读取数据块
                chunk = process.stdout.read(4096)
                if not chunk:
                    print("No more data from ffmpeg")
                    break

                # 发送原始H.264数据
                sock.sendall(chunk)
                print("Sent {} bytes of H.264 data".format(len(chunk)))

                # 检查ffmpeg进程是否还在运行
                if process.poll() is not None:
                    print("FFmpeg process terminated")
                    break

    except socket.error as e:
        print("Socket error: {}".format(e))
    except Exception as e:
        print("Error: {}".format(e))
    finally:
        print("Terminating ffmpeg process...")
        process.terminate()

        # 等待进程结束（兼容低版本Python）
        import time
        wait_time = 0
        while process.poll() is None and wait_time < 5:
            time.sleep(0.1)
            wait_time += 0.1

        # 如果还没结束，强制终止
        if process.poll() is None:
            print("Force killing ffmpeg process...")
            process.kill()
            process.wait()

        # 打印ffmpeg错误信息（如果有）
        if process.stderr:
            stderr_output = process.stderr.read()
            if stderr_output:
                print("FFmpeg stderr: {}".format(stderr_output.decode('utf-8', errors='ignore')))

    print("video stream finished!")

if __name__ == '__main__':
    start_video()