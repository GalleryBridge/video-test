@echo off
chcp 65001 > nul
echo ====================================
echo WebRTC真实视频监控系统启动脚本
echo ====================================
echo.

echo 正在安装Python依赖...
pip install aiortc websockets opencv-python numpy av
if %errorlevel% neq 0 (
    echo [错误] Python依赖安装失败
    echo 请确保已安装Python 3.8+和pip
    pause
    exit /b 1
)

echo.
echo 启动WebRTC媒体服务器（端口8765）...
start "WebRTC媒体服务器" cmd /k "python webrtc_media_server.py"
timeout /t 3 > nul

echo 启动Spring Boot后端（端口8080）...
cd video-test-backend
start "Spring Boot后端" cmd /k "mvn spring-boot:run"
cd ..
timeout /t 5 > nul

echo 启动Vue前端（端口5173）...
cd video-test-frontend
start "Vue前端" cmd /k "npm run dev"
cd ..

echo.
echo ====================================
echo 真实WebRTC系统启动完成！
echo ====================================
echo.
echo 系统功能：
echo - 真实RTSP摄像头视频流
echo - WebRTC实时传输
echo - 低延迟视频监控
echo.
echo 请等待几秒钟让所有服务完全启动，然后：
echo 1. 打开浏览器访问: http://localhost:5173
echo 2. 点击"开始播放"建立WebRTC连接
echo 3. 等待RTSP摄像头连接成功
echo.
echo 注意事项：
echo - 确保RTSP摄像头地址正确且可访问
echo - 网络防火墙可能需要配置
echo - 复杂网络环境建议配置TURN服务器
echo.
pause 