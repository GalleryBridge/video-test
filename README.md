# 实时视频监控系统

支持WebSocket和WebRTC两种传输模式的实时RTSP视频流监控系统，兼容Python 3.7+，采用前后端分离架构。

## 🔀 传输模式选择

### WebSocket模式 (默认)
- **高兼容性**：支持所有现代浏览器
- **稳定可靠**：基于TCP协议，数据传输可靠
- **JPEG传输**：使用JPEG压缩，带宽友好
- **简单部署**：无需复杂配置

### WebRTC模式 (P2P)
- **超低延迟**：P2P直连，延迟最小化
- **高效传输**：原生视频编码，质量更高
- **自适应码率**：根据网络状况自动调整
- **NAT穿透**：支持复杂网络环境

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
├── webrtc_server.py             # WebRTC信令服务器
├── switch_mode.py               # 模式切换工具
├── config.py                    # 系统配置文件
├── requirements.txt             # Python依赖包
├── README.md                    # 项目文档
├── video-test-frontend/         # Vue.js前端应用
│   ├── src/
│   │   ├── App.vue             # WebSocket模式前端
│   │   ├── App_webrtc.vue      # WebRTC模式前端
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

### 3. 选择传输模式并启动服务器

#### WebSocket模式 (推荐)
```bash
python websocket_video_server.py
```

#### WebRTC模式 (低延迟)
```bash
python webrtc_server.py
```

### 4. 启动前端应用
```bash
cd video-test-frontend
npm install
npm run dev
```

**前端模式切换：**
- WebSocket模式：使用 `src/App.vue`
- WebRTC模式：将 `src/App_webrtc.vue` 重命名为 `src/App.vue`

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

### WebSocket模式
1. **启动系统**：启动 `websocket_video_server.py` 和前端应用
2. **打开浏览器**：访问前端应用地址（通常是 http://localhost:5173）
3. **连接服务器**：点击"连接服务器"按钮建立WebSocket连接
4. **开始播放**：连接成功后点击"开始播放"按钮启动视频流
5. **实时监控**：观看实时视频流和系统状态信息

### WebRTC模式
1. **启动系统**：启动 `webrtc_server.py` 和前端应用（使用App_webrtc.vue）
2. **打开浏览器**：访问前端应用地址
3. **连接WebRTC**：点击"连接WebRTC服务器"按钮
4. **P2P握手**：系统自动建立WebRTC P2P连接
5. **开始播放**：连接建立后启动超低延迟视频流
6. **备用模式**：如果WebRTC失败，自动降级到WebSocket模式

### 快速模式切换
使用提供的切换脚本快速切换模式：

```bash
# 查看当前状态
python switch_mode.py status

# 切换到WebSocket模式
python switch_mode.py websocket

# 切换到WebRTC模式
python switch_mode.py webrtc
```

**手动切换方法：**
- **运行时切换**：重启服务器即可切换模式
- **前端切换**：替换App.vue文件或修改import路径
- **配置保持**：两种模式使用相同的config.py配置

## 🔧 技术特点

### 双模式对比

| 特性 | WebSocket模式 | WebRTC模式 |
|------|---------------|------------|
| **延迟** | 100-300ms | 50-100ms |
| **视频质量** | JPEG压缩 | 原生H.264 |
| **CPU占用** | 低 | 中等 |
| **网络适应** | 固定码率 | 自适应码率 |
| **浏览器兼容** | 99% | 95% |
| **NAT穿透** | 不需要 | 自动处理 |
| **部署复杂度** | 简单 | 中等 |

### 性能优化
- **异步处理**：使用asyncio提升并发性能
- **帧率控制**：智能帧率控制避免资源浪费
- **数据压缩**：JPEG/H.264双重编码选择
- **缓冲优化**：最小化视频延迟
- **P2P传输**：WebRTC直连减少服务器负载

### 兼容性
- **Python 3.7+支持**：兼容较老版本Python
- **跨平台**：支持Windows、Linux、macOS
- **标准协议**：RTSP、WebSocket、WebRTC标准
- **浏览器兼容**：支持现代主流浏览器
- **备用机制**：WebRTC自动降级到WebSocket

### 可扩展性
- **模块化设计**：清晰的代码结构便于扩展
- **配置驱动**：通过配置文件轻松调整参数
- **API接口**：RESTful API支持系统集成
- **多客户端**：支持多个浏览器同时连接
- **传输选择**：运行时动态选择最佳传输方式

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