# WebRTC视频监控系统配置文件

# RTSP摄像头配置
RTSP_URL = "rtsp://admin:zky2025...@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0"

# 视频参数配置 (针对4K摄像头优化)
VIDEO_WIDTH = 960
VIDEO_HEIGHT = 540
VIDEO_FPS = 15

# WebRTC服务器配置
WEBRTC_SERVER_HOST = "0.0.0.0"
WEBRTC_SERVER_PORT = 8765

# STUN服务器配置（用于NAT穿透）
STUN_SERVERS = [
    "stun:stun.l.google.com:19302",
    "stun:stun1.l.google.com:19302"
]

# 日志级别
LOG_LEVEL = "INFO"

# 摄像头重连设置
CAMERA_RECONNECT_INTERVAL = 5  # 秒
CAMERA_BUFFER_SIZE = 1  # 降低延迟

# WebRTC连接超时设置
CONNECTION_TIMEOUT = 30  # 秒 