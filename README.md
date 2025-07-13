# 视频流传输系统

基于Spring Boot + Netty + WebSocket + JSMpeg的实时视频流传输系统。

## 系统架构

```
FFmpeg脚本 --TCP--> Spring Boot后端 --WebSocket--> Vue前端
    |              (Netty服务器)               (JSMpeg播放器)
    |                   |                           |
视频采集           数据转发服务                 视频解码播放
```

## 功能特点

- **视频采集**: 使用FFmpeg从RTSP源获取H.264视频流
- **数据传输**: Netty TCP服务器(端口8101)接收视频数据
- **实时推送**: Netty WebSocket服务器(端口8103)向前端推送
- **视频播放**: 前端使用JSMpeg解码器实时播放视频

## 快速启动

### 1. 启动后端服务

```bash
cd video-test-backend
mvn spring-boot:run
```

服务启动后会自动开启:
- TCP服务器: 端口8101 (接收视频流)
- WebSocket服务器: 端口8103 (推送给前端)

### 2. 启动前端应用

```bash
cd video-test-frontend
npm install
npm run dev
```

前端将在 http://localhost:5173 运行

### 3. 启动视频推流

修改 `ffmpeg_linux.py` 中的目标IP地址:

```python
target_ip = '你的后端服务器IP'  # 默认: 192.168.1.196
target_port = 8101
```

然后运行:

```bash
python ffmpeg_linux.py
```

## 端口配置

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| TCP服务器 | 8101 | TCP | 接收FFmpeg视频流 |
| WebSocket服务器 | 8103 | WebSocket | 向前端推送视频 |
| 前端开发服务器 | 5173 | HTTP | Vue应用访问地址 |

## 视频参数

- **分辨率**: 640x480
- **帧率**: 15fps
- **编码**: H.264
- **格式**: MPEG-TS
- **传输**: 无音频，仅视频

## 故障排除

### 1. 连接失败
- 检查防火墙设置，确保端口8101和8103开放
- 确认IP地址配置正确
- 检查网络连通性

### 2. 视频无法播放
- 确认FFmpeg脚本正常运行
- 检查浏览器控制台错误信息
- 验证WebSocket连接状态

### 3. 性能问题
- 调整FFmpeg编码参数（码率、分辨率等）
- 检查网络带宽
- 监控服务器资源使用情况

## 技术栈

### 后端
- Spring Boot 2.7.6
- Netty (TCP/WebSocket服务器)
- Java 8

### 前端
- Vue 3
- TypeScript
- JSMpeg (视频解码)
- Vite (构建工具)

### 视频处理
- FFmpeg (视频采集和编码)
- H.264编码器
- MPEG-TS容器格式

## 开发说明

### 添加新功能
1. 后端扩展在 `com.zky.netty` 包下添加新的处理器
2. 前端功能在 `src/components` 下创建新组件
3. 修改 `VideoStreamManager` 来处理新的数据类型

### 自定义配置
- 后端配置: `application.properties`
- 前端配置: `vite.config.ts`
- 视频参数: 修改 `ffmpeg_linux.py` 中的FFmpeg参数