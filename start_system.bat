@echo off
chcp 65001 > nul
echo ====================================
echo WebRTC视频监控系统启动脚本
echo ====================================
echo.

echo 正在检查环境...
echo.

REM 检查Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Java
java -version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Java，请先安装Java 8+
    pause
    exit /b 1
)

REM 检查Node.js
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo [信息] 环境检查通过
echo.

REM 安装Python依赖
echo 正在安装Python依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] Python依赖安装失败
    pause
    exit /b 1
)

REM 安装前端依赖
echo 正在安装前端依赖...
cd video-test-frontend
call npm install
if %errorlevel% neq 0 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
)
cd ..

echo.
echo ====================================
echo 开始启动服务
echo ====================================
echo.

REM 启动WebRTC媒体服务器
echo 启动WebRTC媒体服务器（端口8765）...
start "WebRTC媒体服务器" cmd /k "python webrtc_media_server.py"
timeout /t 3 > nul

REM 启动Spring Boot后端
echo 启动Spring Boot后端（端口8080）...
cd video-test-backend
start "Spring Boot后端" cmd /k "mvn spring-boot:run"
cd ..
timeout /t 5 > nul

REM 启动Vue前端
echo 启动Vue前端（端口5173）...
cd video-test-frontend
start "Vue前端" cmd /k "npm run dev"
cd ..

echo.
echo ====================================
echo 系统启动完成！
echo ====================================
echo.
echo 请等待几秒钟让所有服务完全启动，然后：
echo 1. 打开浏览器访问: http://localhost:5173
echo 2. 点击"开始播放"按钮开始视频流
echo.
echo 按任意键退出启动脚本（服务将继续运行）...
pause > nul 