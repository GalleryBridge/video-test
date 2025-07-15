import subprocess
import os
import time
import shutil

def setup_hls_directory():
    """设置HLS输出目录"""
    hls_dir = "video-test-backend/src/main/resources/static/hls"
    
    # 如果目录存在，清空它
    if os.path.exists(hls_dir):
        shutil.rmtree(hls_dir)
    
    # 创建新目录
    os.makedirs(hls_dir, exist_ok=True)
    print(f"HLS目录创建完成: {hls_dir}")
    return hls_dir

def start_hls_stream():
    """启动HLS视频流"""
    hls_dir = setup_hls_directory()
    playlist_path = os.path.join(hls_dir, "stream.m3u8")
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0",
        
        # 视频编码参数
        "-vcodec", "libx264",          # H.264编码器
        "-preset", "faster",            # 编码速度预设
        "-tune", "zerolatency",        # 零延迟调优
        "-crf", "28",                  # 恒定质量因子(质量较高)
        "-maxrate", "2M",              # 最大比特率
        "-bufsize", "4M",              # 缓冲区大小
        "-g", "30",                    # GOP大小
        "-keyint_min", "30",           # 最小关键帧间隔
        
        # 分辨率和帧率
        "-s", "1280x720",              # 分辨率
        "-r", "25",                    # 帧率25fps
        
        # HLS专用参数
        "-f", "hls",                   # 输出HLS格式
        "-hls_time", "2",              # 每个切片2秒
        "-hls_list_size", "5",         # 播放列表保留5个切片
        "-hls_flags", "delete_segments+append_list", # 删除旧切片，追加到播放列表
        "-hls_allow_cache", "0",       # 禁用缓存
        "-hls_segment_filename", os.path.join(hls_dir, "segment_%03d.ts"), # 切片文件名格式
        
        # 禁用音频
        "-an",
        
        # 输出播放列表文件
        playlist_path
    ]
    
    print("启动HLS视频流...")
    print(f"播放列表将保存到: {playlist_path}")
    print("FFmpeg命令:", " ".join(ffmpeg_cmd))
    
    try:
        # 启动ffmpeg进程
        process = subprocess.Popen(
            ffmpeg_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        
        print("HLS流媒体服务器启动成功!")
        print("等待切片文件生成...")
        
        # 监控进程
        while True:
            # 检查播放列表文件是否生成
            if os.path.exists(playlist_path):
                with open(playlist_path, 'r') as f:
                    content = f.read()
                    if content and "#EXTINF" in content:
                        print("✅ HLS播放列表已生成，流媒体开始工作")
                        break
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                print("❌ FFmpeg进程异常退出")
                stderr_output = process.stderr.read()
                print(f"错误信息: {stderr_output}")
                break
                
            time.sleep(1)
        
        # 持续运行
        print("🎥 HLS流媒体服务正在运行...")
        print("📺 可以通过以下地址访问:")
        print("   - 本地: http://localhost:8080/hls/stream.m3u8")
        print("   - 网络: http://192.168.1.196:8080/hls/stream.m3u8")
        print("按 Ctrl+C 停止...")
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n收到停止信号，正在关闭...")
        process.terminate()
        
        # 等待进程结束
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("强制终止FFmpeg进程...")
            process.kill()
            process.wait()
            
    except Exception as e:
        print(f"错误: {e}")
        if 'process' in locals():
            process.terminate()
    
    print("HLS流媒体服务已停止")

if __name__ == '__main__':
    start_hls_stream() 