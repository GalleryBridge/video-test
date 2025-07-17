# WebRTC视频监控系统启动指南

## 系统架构说明

本系统采用WebRTC架构，包含以下组件：
1. **Python WebRTC媒体服务器** - 处理RTSP到WebRTC的转换
2. **Spring Boot信令服务器** - 提供WebSocket信令服务
3. **Vue前端客户端** - 显示实时视频流

## 环境要求

### Python环境
- Python 3.8+
- FFmpeg（用于视频处理）

### Java环境  
- Java 8+
- Maven 3.6+

### Node.js环境
- Node.js 16+
- npm 或 yarn

## 启动步骤

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 启动WebRTC媒体服务器
```bash
python webrtc_media_server.py
```
服务器将在 `ws://localhost:8765` 启动

### 3. 启动Spring Boot后端
```bash
cd video-test-backend
mvn spring-boot:run
```
后端将在 `http://localhost:8080` 启动

### 4. 启动Vue前端
```bash
cd video-test-frontend
npm install
npm run dev
```
前端将在 `http://localhost:5173` 启动

## 访问系统

1. 打开浏览器访问 `http://localhost:5173`
2. 点击"开始播放"按钮
3. 系统将自动建立WebRTC连接并显示视频流

## 配置说明

### RTSP摄像头配置
在 `webrtc_media_server.py` 中修改RTSP URL：
```python
self.rtsp_url = "rtsp://username:password@camera_ip:port/stream_path"
```

### STUN/TURN服务器配置
在 `video-test-frontend/src/App.vue` 中修改：
```javascript
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    // 添加你的TURN服务器
    // { urls: 'turn:your-turn-server.com', username: 'user', credential: 'pass' }
  ]
}
```

## 故障排除

### 1. Python媒体服务器无法启动
- 检查Python依赖是否安装完整
- 确认端口8765未被占用
- 检查RTSP摄像头是否可访问

### 2. WebRTC连接失败
- 检查防火墙设置
- 确认STUN服务器可访问
- 在复杂网络环境下可能需要TURN服务器

### 3. 视频无法显示
- 检查摄像头RTSP地址是否正确
- 确认摄像头支持的编码格式
- 查看浏览器控制台错误信息

## 性能优化建议

1. **网络优化**
   - 使用有线网络连接
   - 配置QoS确保视频流优先级

2. **服务器优化**
   - 增加服务器CPU和内存
   - 使用SSD存储提升I/O性能

3. **视频编码优化**
   - 调整视频分辨率和帧率
   - 优化H.264编码参数

## 生产环境部署

### 1. 使用HTTPS
- 配置SSL证书
- WebRTC要求HTTPS环境（localhost除外）

### 2. 使用专业媒体服务器
- 推荐使用Kurento Media Server
- 或者Janus WebRTC Gateway

### 3. 负载均衡
- 配置Nginx反向代理
- 实现多实例负载均衡

## 技术栈说明

- **前端**: Vue 3 + TypeScript + WebRTC API
- **后端**: Spring Boot + WebSocket
- **媒体服务**: Python + aiortc + OpenCV
- **视频协议**: RTSP → WebRTC

## 许可证

本项目仅供学习和研究使用。 