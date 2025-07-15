# Vue3 + HLS 实时视频流播放系统

基于 **Vue3 + HLS + Spring Boot** 的高性能实时视频流传输和播放系统。

## 🏗️ 系统架构

```
🎥 RTSP视频源 ──→ FFmpeg ──→ HLS切片文件 ──→ Spring Boot HTTP服务器 ──→ Vue3前端
   摄像头/设备      编码器     (m3u8+ts)        静态资源托管          HLS.js播放器
```

## ✨ 特性亮点

- **🚀 低延迟**: HLS优化配置，延迟降至2-4秒
- **📱 跨平台**: 支持所有现代浏览器，包括移动端
- **🔄 自动清理**: 智能清理过期切片文件，节省存储空间
- **📊 实时监控**: 流状态实时监控和错误恢复
- **🎛️ 灵活配置**: 支持多种分辨率和比特率设置
- **💻 现代化UI**: 基于Vue3的响应式播放界面

## 🛠️ 技术栈

### 后端
- **Spring Boot 2.7.6** - 应用框架
- **Spring Web** - HTTP服务器和API
- **定时任务** - 自动清理过期文件
- **Java 8** - 运行环境

### 前端
- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **HLS.js** - HLS流播放器
- **Vite** - 构建工具

### 流媒体
- **FFmpeg** - 视频编码和处理
- **HLS (HTTP Live Streaming)** - 流媒体协议
- **H.264** - 视频编码格式

## 🚀 快速开始

### 前置要求

```bash
# 检查必要的软件是否已安装
ffmpeg -version    # FFmpeg 4.0+
java -version      # Java 8+
node --version     # Node.js 16+
mvn --version      # Maven 3.6+
```

### 一键启动

```bash
# Windows用户
start-hls-system.bat

# Linux/Mac用户  
chmod +x start-hls-system.sh
./start-hls-system.sh
```

### 手动启动

#### 1. 启动后端服务

```bash
cd video-test-backend
mvn spring-boot:run
```

#### 2. 启动前端应用

```bash
cd video-test-frontend
npm install
npm run dev
```

#### 3. 开始视频推流

```bash
# 修改 ffmpeg_hls.py 中的RTSP地址
python ffmpeg_hls.py
```

#### 4. 访问应用

- 🌐 **前端播放器**: http://localhost:5173
- 🚀 **后端API**: http://localhost:8080
- 📺 **HLS播放列表**: http://localhost:8080/hls/stream.m3u8

## 📋 详细配置

### FFmpeg推流配置

编辑 `ffmpeg_hls.py` 中的参数：

```python
# 视频源配置
rtsp_url = "rtsp://username:password@ip:port/path"

# 视频质量配置
resolution = "1280x720"  # 分辨率
frame_rate = "25"        # 帧率
bit_rate = "2M"          # 比特率

# HLS切片配置
segment_time = "2"       # 每个切片时长(秒)
playlist_size = "5"      # 播放列表保留切片数量
```

### 前端播放器配置

编辑 `video-test-frontend/src/components/VideoPlayer.vue`：

```typescript
// 服务器配置
const serverHost = ref('192.168.1.196')  // 修改为你的服务器IP

// HLS播放器配置
const hlsConfig = {
  lowLatencyMode: true,        // 低延迟模式
  maxBufferLength: 30,         // 最大缓冲长度
  liveSyncDurationCount: 3,    // 直播同步
}
```

### 后端服务配置

编辑 `video-test-backend/src/main/resources/application.properties`：

```properties
# 服务器端口
server.port=8080

# 静态资源配置
spring.web.resources.static-locations=classpath:/static/
spring.web.resources.cache.period=0

# 文件上传大小限制
spring.servlet.multipart.max-file-size=100MB
spring.servlet.multipart.max-request-size=100MB
```

## 🔧 API文档

### HLS状态检查

```bash
GET /api/hls/status
```

响应示例：
```json
{
  "isActive": true,
  "playlistExists": true,
  "playlistUrl": "/hls/stream.m3u8",
  "segmentCount": 5,
  "lastModified": 1703123456789,
  "timestamp": 1703123456789
}
```

### 清理HLS文件

```bash
POST /api/hls/cleanup
```

响应示例：
```json
{
  "success": true,
  "deletedCount": 12,
  "message": "HLS文件清理完成"
}
```

### 获取播放列表

```bash
GET /api/hls/playlist
# 或直接访问
GET /hls/stream.m3u8
```

## 📊 性能优化

### 延迟优化

| 配置项 | 值 | 说明 |
|--------|----|----|
| hls_time | 2 | 切片时长，越小延迟越低 |
| hls_list_size | 5 | 播放列表大小 |
| lowLatencyMode | true | HLS.js低延迟模式 |
| maxBufferLength | 30 | 最大缓冲区长度 |

### 质量设置

| 分辨率 | 比特率 | 适用场景 |
|--------|--------|----------|
| 640x480 | 1M | 低带宽环境 |
| 1280x720 | 2M | 标准质量 |
| 1920x1080 | 4M | 高清质量 |

## 🐛 故障排除

### 常见问题

#### 1. 播放器无法加载

```bash
# 检查HLS流状态
curl http://localhost:8080/api/hls/status

# 检查播放列表是否存在
curl http://localhost:8080/hls/stream.m3u8
```

#### 2. FFmpeg推流失败

```bash
# 检查RTSP源是否可访问
ffplay rtsp://your-rtsp-url

# 检查FFmpeg版本
ffmpeg -version
```

#### 3. CORS错误

确保 `WebConfig.java` 中的CORS配置正确：

```java
@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/hls/**")
            .allowedOriginPatterns("*")
            .allowedMethods("GET", "HEAD", "OPTIONS");
}
```

#### 4. 文件权限问题

```bash
# 确保HLS目录有写权限
chmod 755 video-test-backend/src/main/resources/static/hls/
```

### 日志调试

```bash
# 查看后端日志
tail -f video-test-backend/logs/spring.log

# 查看FFmpeg输出
python ffmpeg_hls.py 2>&1 | tee ffmpeg.log

# 浏览器控制台查看前端日志
```

## 📈 监控和维护

### 自动清理策略

系统会自动清理过期的HLS切片文件：

- **清理间隔**: 每10秒检查一次
- **保留策略**: 最多保留10个切片文件
- **过期时间**: 30秒未访问的文件

### 性能监控

监控指标：
- 切片文件生成速度
- 播放器缓冲状态
- 网络带宽使用
- 服务器CPU和内存使用

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [HLS.js](https://github.com/video-dev/hls.js/) - HLS播放器库
- [FFmpeg](https://ffmpeg.org/) - 视频处理工具
- [Vue.js](https://vuejs.org/) - 前端框架
- [Spring Boot](https://spring.io/projects/spring-boot) - 后端框架

---

**📞 技术支持**: 如有问题，请提交 [Issue](../../issues)

**🌟 给个Star**: 如果这个项目对你有帮助，请给个星标支持一下！