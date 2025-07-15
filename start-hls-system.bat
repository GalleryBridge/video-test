@echo off
echo ====================================
echo       HLS视频流媒体系统启动脚本
echo ====================================
echo.

echo [1/3] 检查系统环境...

:: 检查FFmpeg是否安装
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到FFmpeg，请先安装FFmpeg并添加到PATH环境变量
    pause
    exit /b 1
)
echo ✅ FFmpeg已安装

:: 检查Java是否安装
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Java，请先安装Java
    pause
    exit /b 1
)
echo ✅ Java已安装

:: 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)
echo ✅ Node.js已安装

echo.
echo [2/3] 启动后端服务器...
start "Spring Boot Backend" cmd /k "cd video-test-backend && mvn spring-boot:run"

echo 等待后端服务器启动...
timeout /t 10 /nobreak >nul

echo.
echo [3/3] 启动前端开发服务器...
start "Vue Frontend" cmd /k "cd video-test-frontend && npm run dev"

echo 等待前端服务器启动...
timeout /t 5 /nobreak >nul

echo.
echo ====================================
echo        系统启动完成！
echo ====================================
echo.
echo 🌐 前端地址: http://localhost:5173
echo 🚀 后端API: http://localhost:8080
echo 📺 HLS播放列表: http://localhost:8080/hls/stream.m3u8
echo.
echo 📋 接下来的步骤:
echo    1. 运行 python ffmpeg_hls.py 开始推流
echo    2. 打开浏览器访问前端地址
echo    3. 点击"开始播放"按钮
echo.
echo 按任意键继续，或者Ctrl+C退出...
pause >nul

:: 可选：自动启动FFmpeg推流
set /p start_ffmpeg="是否现在启动FFmpeg推流? (y/n): "
if /i "%start_ffmpeg%"=="y" (
    echo.
    echo 启动FFmpeg HLS推流...
    python ffmpeg_hls.py
)

echo.
echo 所有服务已启动完成！
pause 