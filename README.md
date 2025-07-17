# WebSocket视频监控系统

基于WebSocket的实时RTSP视频流监控系统，支持Python 3.7+，采用前后端分离架构。

## 🎯 系统功能

- **实时视频流传输**：通过WebSocket协议传输JPEG格式视频流
- **RTSP摄像头支持**：连接标准RTSP协议摄像头设备  
- **Web端监控**：现代化Vue.js前端界面，支持实时视频显示
- **配置管理**：Spring Boot后端提供配置API接口
- **高兼容性**：兼容Python 3.7+，无需复杂WebRTC环境

## 🏗️ 系统架构

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    RTSP    ┌─────────────────┐
│   Vue.js 前端   │ ←────────────→ │ Python视频服务器 │ ←────────→ │   RTSP摄像头     │
│  (用户界面)     │                │  (视频流处理)   │            │   (视频源)      │
└─────────────────┘                └─────────────────┘            └─────────────────┘
        │                                   ↑
        │ HTTP API                          │ 配置
        ↓                                   │
┌─────────────────┐                ┌─────────────────┐
│ Spring Boot后端 │                │   config.py     │
│  (配置管理)     │                │   (配置文件)    │
└─────────────────┘                └─────────────────┘
```

## 🛠️ 技术栈

### 后端技术
- **Python 3.7+**：主要开发语言
- **WebSocket**：实时双向通信协议  
- **OpenCV (cv2)**：视频处理和RTSP连接
- **asyncio**：异步IO处理，提升性能
- **Spring Boot**：配置管理API服务

### 前端技术
- **Vue.js 3**：现代前端框架
- **TypeScript**：类型安全的JavaScript
- **WebSocket API**：原生WebSocket连接
- **CSS3**：现代样式和动画效果

### 视频技术
- **RTSP协议**：实时流传输协议
- **JPEG编码**：实时图像压缩
- **Base64编码**：二进制数据传输
- **帧率控制**：可配置的视频帧率

## 📦 项目结构

```
video-test/
├── websocket_video_server.py    # WebSocket视频服务器
├── config.py                    # 系统配置文件
├── requirements.txt             # Python依赖包
├── video-test-frontend/         # Vue.js前端应用
│   ├── src/
│   │   ├── App.vue             # 主要Vue组件
│   │   └── main.ts             # 应用入口
│   └── package.json            # 前端依赖配置
└── video-test-backend/          # Spring Boot后端
    ├── src/main/java/          # Java源码
    └── pom.xml                 # Maven配置
```

## 🚀 快速开始

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 配置摄像头
编辑 `config.py` 文件，设置RTSP摄像头URL：
```python
RTSP_URL = "rtsp://用户名:密码@摄像头IP:端口/路径"
```

### 3. 启动视频服务器
```bash
python websocket_video_server.py
```

### 4. 启动前端应用
```bash
cd video-test-frontend
npm install
npm run dev
```

### 5. 启动后端服务（可选）
```bash
cd video-test-backend
mvn spring-boot:run
```

## ⚙️ 配置说明

### 视频参数 (config.py)
```python
VIDEO_WIDTH = 960        # 视频宽度（像素）
VIDEO_HEIGHT = 540       # 视频高度（像素） 
VIDEO_FPS = 15          # 目标帧率
```

### 服务器配置
```python
WEBRTC_SERVER_HOST = "0.0.0.0"  # 服务器地址
WEBRTC_SERVER_PORT = 8765       # WebSocket端口
```

## 🎮 使用方法

1. **启动系统**：按顺序启动视频服务器和前端应用
2. **打开浏览器**：访问前端应用地址（通常是 http://localhost:5173）
3. **连接服务器**：点击"连接服务器"按钮建立WebSocket连接
4. **开始播放**：连接成功后点击"开始播放"按钮启动视频流
5. **实时监控**：观看实时视频流和系统状态信息

## 🔧 技术特点

### 性能优化
- **异步处理**：使用asyncio提升并发性能
- **帧率控制**：智能帧率控制避免资源浪费
- **数据压缩**：JPEG压缩降低带宽需求
- **缓冲优化**：最小化视频延迟

### 兼容性
- **Python 3.7+支持**：兼容较老版本Python
- **跨平台**：支持Windows、Linux、macOS
- **标准协议**：使用标准RTSP和WebSocket协议
- **浏览器兼容**：支持现代主流浏览器

### 可扩展性
- **模块化设计**：清晰的代码结构便于扩展
- **配置驱动**：通过配置文件轻松调整参数
- **API接口**：RESTful API支持系统集成
- **多客户端**：支持多个浏览器同时连接

## 📋 系统要求

- **Python**: 3.7+
- **Node.js**: 16+  
- **Java**: 11+ (后端服务)
- **摄像头**: 支持RTSP协议的网络摄像头
- **浏览器**: Chrome 88+, Firefox 85+, Safari 14+

## 🐛 故障排除

### 常见问题
1. **无法连接摄像头**：检查RTSP URL和网络连接
2. **视频卡顿**：适当降低帧率或分辨率
3. **连接失败**：确认防火墙和端口配置
4. **画面黑屏**：检查摄像头权限和视频格式支持

### 调试工具
- 浏览器开发者工具查看WebSocket连接状态
- Python控制台查看详细日志信息
- 网络工具检查RTSP连通性

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

---
*构建现代化的实时视频监控解决方案* 🎥✨ 