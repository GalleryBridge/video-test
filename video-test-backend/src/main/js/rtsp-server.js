const Stream = require("node-rtsp-stream");

// 配置RTSP流转WebSocket
const stream = new Stream({
  name: 'test-stream',
  streamUrl: 'rtsp://127.0.0.1/test', // 你的RTSP流地址
  wsPort: 8888, // WebSocket端口
  ffmpegOptions: {
    '-stats': '', // 显示统计信息
    '-r': 30, // 帧率
    '-s': '640x480', // 分辨率
    '-f': 'mpegts', // 输出格式
    '-codec:v': 'mpeg1video', // 视频编码器
    '-b:v': '1000k', // 视频比特率
    '-bf': 0, // B帧数量
    '-muxdelay': 0.001, // 复用延迟
    '-an': '' // 禁用音频
  }
});

// 监听事件
stream.on('camdata', (data) => {
  console.log('收到摄像头数据:', data.length, '字节');
});

stream.on('exitWithError', (error) => {
  console.error('FFmpeg错误:', error);
});

console.log('RTSP-WebSocket服务器启动在端口8888');
console.log('WebSocket地址: ws://localhost:8888'); 