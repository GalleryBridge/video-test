<template>
  <div id="app">
    <header class="header">
      <h1>WebRTC视频监控系统</h1>
      <div class="header-subtitle">实时RTSP视频流 (WebRTC P2P传输)</div>
    </header>
    
    <main class="main-content">
      <div class="video-container">
        <div class="video-display">
          <video
            v-if="isWebRTCConnected"
            ref="webrtcVideo"
            class="video-player webrtc"
            :class="{ 'connected': isConnected && isStreaming }"
            autoplay
            muted
            playsinline
          ></video>
          <img
            v-else-if="currentFrame"
            :src="currentFrame"
            class="video-player fallback"
            :class="{ 'connected': isConnected && isStreaming }"
            alt="视频流"
          />
          <canvas
            v-else
            ref="placeholderCanvas"
            class="video-player placeholder"
            width="960"
            height="540"
          ></canvas>
        </div>
        
        <div v-if="!isConnected || !isStreaming" class="video-overlay">
          <div class="status-indicator">
            <div class="loading-spinner" v-if="isConnecting"></div>
            <span class="status-text">{{ statusText }}</span>
          </div>
        </div>
      </div>
      
      <div class="controls">
        <button 
          @click="toggleConnection" 
          class="control-btn"
          :class="{ 
            'connecting': isConnecting, 
            'connected': isConnected,
            'webrtc': isWebRTCConnected 
          }"
          :disabled="isConnecting"
        >
          <span v-if="!isConnected && !isConnecting">连接WebRTC服务器</span>
          <span v-else-if="isConnecting">连接中...</span>
          <span v-else-if="!isStreaming">开始播放</span>
          <span v-else>停止播放</span>
        </button>
        
        <div class="connection-info">
          <div class="info-item">
            <span class="label">连接状态:</span>
            <span class="value" :class="connectionStatusClass">{{ connectionStatus }}</span>
          </div>
          <div class="info-item">
            <span class="label">传输模式:</span>
            <span class="value" :class="transportModeClass">{{ transportMode }}</span>
          </div>
          <div class="info-item">
            <span class="label">视频状态:</span>
            <span class="value" :class="streamingStatusClass">{{ streamingStatus }}</span>
          </div>
          <div class="info-item" v-if="videoInfo.width && videoInfo.height">
            <span class="label">视频分辨率:</span>
            <span class="value">{{ videoInfo.width }}x{{ videoInfo.height }}</span>
          </div>
          <div class="info-item" v-if="frameRate > 0">
            <span class="label">帧率:</span>
            <span class="value">{{ frameRate.toFixed(1) }} FPS</span>
          </div>
          <div class="info-item" v-if="isWebRTCConnected">
            <span class="label">连接质量:</span>
            <span class="value status-connected">优秀 (P2P)</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'

// 响应式数据
const isConnected = ref(false)
const isConnecting = ref(false)
const isStreaming = ref(false)
const isWebRTCConnected = ref(false)
const connectionStatus = ref('未连接')
const streamingStatus = ref('未开始')
const transportMode = ref('WebSocket备用')
const statusText = ref('点击连接WebRTC服务器按钮开始')
const currentFrame = ref<string | null>(null)
const videoInfo = ref({ width: 960, height: 540 })
const frameRate = ref(0)

// WebRTC和WebSocket相关
let websocket: WebSocket | null = null
let peerConnection: RTCPeerConnection | null = null
let dataChannel: RTCDataChannel | null = null
const webrtcVideo = ref<HTMLVideoElement | null>(null)
const placeholderCanvas = ref<HTMLCanvasElement | null>(null)

// 帧率计算
let frameCount = 0
let lastFrameTime = 0
let frameRateUpdateTime = 0

// 服务器URL
let mediaServerUrl = 'ws://localhost:8765'

// WebRTC配置
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
}

// 计算属性
const connectionStatusClass = computed(() => {
  switch (connectionStatus.value) {
    case '已连接': return 'status-connected'
    case '连接中': return 'status-connecting'
    case '连接失败': return 'status-error'
    default: return 'status-disconnected'
  }
})

const streamingStatusClass = computed(() => {
  switch (streamingStatus.value) {
    case '播放中': return 'status-connected'
    case '准备中': return 'status-connecting'
    case '已停止': return 'status-disconnected'
    default: return 'status-disconnected'
  }
})

const transportModeClass = computed(() => {
  return isWebRTCConnected.value ? 'status-connected' : 'status-disconnected'
})

// 获取系统配置
async function loadSystemConfig() {
  try {
    const response = await fetch('http://localhost:8080/api/config/webrtc')
    if (response.ok) {
      const config = await response.json()
      mediaServerUrl = config.mediaServerUrl
      console.log('系统配置加载成功:', config)
    }
  } catch (error) {
    console.warn('加载系统配置失败，使用默认配置:', error)
  }
}

// 绘制占位符
function drawPlaceholder() {
  if (!placeholderCanvas.value) return
  
  const canvas = placeholderCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // 清空画布
  ctx.fillStyle = '#1a1a1a'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // 绘制文字
  ctx.fillStyle = '#ffffff'
  ctx.font = '24px Arial'
  ctx.textAlign = 'center'
  ctx.fillText('等待WebRTC连接...', canvas.width / 2, canvas.height / 2 - 40)
  ctx.font = '16px Arial'
  ctx.fillStyle = '#cccccc'
  ctx.fillText('P2P实时视频传输', canvas.width / 2, canvas.height / 2 - 10)
  ctx.fillStyle = '#999999'
  ctx.font = '14px Arial'
  ctx.fillText('备用: WebSocket JPEG流', canvas.width / 2, canvas.height / 2 + 20)
}

// 初始化WebRTC
async function initWebRTC() {
  try {
    peerConnection = new RTCPeerConnection(rtcConfiguration)
    
    // 处理ICE候选
    peerConnection.onicecandidate = (event) => {
      if (event.candidate && websocket) {
        websocket.send(JSON.stringify({
          type: 'ice_candidate',
          candidate: event.candidate
        }))
      }
    }
    
    // 处理远程流
    peerConnection.ontrack = (event) => {
      console.log('收到远程视频流')
      if (webrtcVideo.value && event.streams[0]) {
        webrtcVideo.value.srcObject = event.streams[0]
        isWebRTCConnected.value = true
        transportMode.value = 'WebRTC P2P'
      }
    }
    
    // 创建数据通道
    dataChannel = peerConnection.createDataChannel('video', {
      ordered: true
    })
    
    dataChannel.onopen = () => {
      console.log('WebRTC数据通道已打开')
      transportMode.value = 'WebRTC P2P'
    }
    
    dataChannel.onmessage = (event) => {
      console.log('收到WebRTC数据:', event.data)
    }
    
    return true
  } catch (error) {
    console.error('WebRTC初始化失败:', error)
    return false
  }
}

// 创建WebRTC Offer
async function createOffer() {
  if (!peerConnection || !websocket) return
  
  try {
    const offer = await peerConnection.createOffer({
      offerToReceiveVideo: true,
      offerToReceiveAudio: false
    })
    
    await peerConnection.setLocalDescription(offer)
    
    websocket.send(JSON.stringify({
      type: 'offer',
      sdp: offer
    }))
    
    console.log('WebRTC Offer已发送')
  } catch (error) {
    console.error('创建WebRTC Offer失败:', error)
  }
}

// WebSocket连接
async function connectWebSocket(): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      websocket = new WebSocket(mediaServerUrl)
      
      websocket.onopen = () => {
        console.log('WebSocket连接已建立')
        resolve()
      }
      
      websocket.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          await handleWebSocketMessage(data)
        } catch (error) {
          console.error('处理WebSocket消息时出错:', error)
        }
      }
      
      websocket.onclose = () => {
        console.log('WebSocket连接已关闭')
        cleanup()
      }
      
      websocket.onerror = (error) => {
        console.error('WebSocket错误:', error)
        reject(error)
      }
      
    } catch (error) {
      reject(error)
    }
  })
}

// 处理WebSocket消息
async function handleWebSocketMessage(data: any) {
  switch (data.type) {
    case 'connected':
      console.log('WebRTC信令服务器连接成功:', data.data.message)
      isConnected.value = true
      isConnecting.value = false
      connectionStatus.value = '已连接'
      statusText.value = '已连接，正在建立WebRTC连接...'
      
      if (data.data.video_config) {
        videoInfo.value = {
          width: data.data.video_config.width,
          height: data.data.video_config.height
        }
      }
      
      // 初始化WebRTC连接
      if (await initWebRTC()) {
        await createOffer()
      }
      break
      
    case 'answer':
      console.log('收到WebRTC Answer')
      if (peerConnection && data.data.sdp) {
        try {
          await peerConnection.setRemoteDescription(data.data.sdp)
          console.log('WebRTC连接建立成功')
        } catch (error) {
          console.error('设置远程描述失败:', error)
        }
      }
      break
      
    case 'ice_candidate':
      console.log('收到ICE候选')
      if (peerConnection && data.data.candidate) {
        try {
          await peerConnection.addIceCandidate(data.data.candidate)
        } catch (error) {
          console.error('添加ICE候选失败:', error)
        }
      }
      break
      
    case 'video_frame':
      // WebRTC备用方案：使用WebSocket传输JPEG
      if (!isWebRTCConnected.value) {
        handleVideoFrame(data.data)
        transportMode.value = 'WebSocket备用'
      }
      break
      
    case 'video_started':
      console.log('视频已开始:', data.data.message)
      isStreaming.value = true
      streamingStatus.value = '播放中'
      statusText.value = isWebRTCConnected.value ? 'WebRTC视频流播放中' : '备用视频流播放中'
      break
      
    case 'video_stopped':
      console.log('视频已停止:', data.data.message)
      isStreaming.value = false
      streamingStatus.value = '已停止'
      statusText.value = '视频流已停止'
      currentFrame.value = null
      break
      
    case 'status':
      console.log('服务器状态:', data.data)
      break
      
    case 'error':
      console.error('服务器错误:', data.data.message)
      statusText.value = `错误: ${data.data.message}`
      connectionStatus.value = '连接失败'
      break
      
    default:
      console.log('收到未知类型消息:', data.type, data)
  }
}

// 处理视频帧 (备用方案)
function handleVideoFrame(frameData: any) {
  if (frameData.image) {
    currentFrame.value = `data:image/jpeg;base64,${frameData.image}`
    
    // 更新视频信息
    if (frameData.width && frameData.height) {
      videoInfo.value = {
        width: frameData.width,
        height: frameData.height
      }
    }
    
    // 计算帧率
    updateFrameRate()
  }
}

// 更新帧率计算
function updateFrameRate() {
  const now = performance.now()
  frameCount++
  
  if (now - frameRateUpdateTime > 1000) {
    frameRate.value = frameCount / ((now - frameRateUpdateTime) / 1000)
    frameCount = 0
    frameRateUpdateTime = now
  }
}

// 开始视频流
async function startVideoStream() {
  if (websocket && isConnected.value) {
    websocket.send(JSON.stringify({
      type: 'start_video'
    }))
    streamingStatus.value = '准备中'
    statusText.value = '正在启动视频流...'
  }
}

// 停止视频流
async function stopVideoStream() {
  if (websocket && isConnected.value) {
    websocket.send(JSON.stringify({
      type: 'stop_video'
    }))
  }
}

// 开始连接
async function startConnection() {
  try {
    isConnecting.value = true
    statusText.value = '正在连接WebRTC信令服务器...'
    
    await connectWebSocket()
    
  } catch (error) {
    console.error('连接失败:', error)
    statusText.value = '连接失败，请检查服务器状态'
    connectionStatus.value = '连接失败'
    isConnecting.value = false
  }
}

// 停止连接
function stopConnection() {
  cleanup()
  statusText.value = '已断开连接'
  connectionStatus.value = '未连接'
  streamingStatus.value = '未开始'
  transportMode.value = 'WebSocket备用'
}

// 清理资源
function cleanup() {
  if (websocket) {
    websocket.close()
    websocket = null
  }
  
  if (peerConnection) {
    peerConnection.close()
    peerConnection = null
  }
  
  if (dataChannel) {
    dataChannel.close()
    dataChannel = null
  }
  
  if (webrtcVideo.value) {
    webrtcVideo.value.srcObject = null
  }
  
  isConnected.value = false
  isConnecting.value = false
  isStreaming.value = false
  isWebRTCConnected.value = false
  currentFrame.value = null
  frameRate.value = 0
  frameCount = 0
}

// 切换连接状态
async function toggleConnection() {
  if (isConnected.value) {
    if (isStreaming.value) {
      await stopVideoStream()
    } else {
      await startVideoStream()
    }
  } else {
    await startConnection()
  }
}

// 生命周期钩子
onMounted(async () => {
  console.log('WebRTC视频监控系统已加载')
  await loadSystemConfig()
  
  // 绘制初始占位符
  await nextTick()
  drawPlaceholder()
})

onUnmounted(() => {
  cleanup()
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  font-family: 'Arial', sans-serif;
}

.header {
  text-align: center;
  padding: 2rem 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

.header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
  font-weight: 300;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.header-subtitle {
  font-size: 1.1rem;
  color: #e0e0e0;
  font-weight: 300;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.video-container {
  position: relative;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto 2rem;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.video-display {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 宽高比 */
}

.video-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #1a1a1a;
  transition: all 0.3s ease;
}

.video-player.connected {
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.5);
}

.video-player.webrtc {
  box-shadow: 0 0 20px rgba(76, 175, 80, 0.6);
}

.video-player.fallback {
  box-shadow: 0 0 20px rgba(255, 193, 7, 0.5);
}

.video-player.placeholder {
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
}

.status-indicator {
  text-align: center;
  padding: 2rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(74, 144, 226, 0.3);
  border-top: 3px solid #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.status-text {
  font-size: 1.1rem;
  color: #e0e0e0;
}

.controls {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
}

.control-btn {
  background: linear-gradient(45deg, #4a90e2, #357abd);
  border: none;
  color: white;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 2rem;
  min-width: 180px;
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(74, 144, 226, 0.4);
}

.control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.control-btn.connecting {
  background: linear-gradient(45deg, #f39c12, #e67e22);
}

.control-btn.connected {
  background: linear-gradient(45deg, #27ae60, #2ecc71);
}

.control-btn.webrtc {
  background: linear-gradient(45deg, #4caf50, #45a049);
  box-shadow: 0 0 15px rgba(76, 175, 80, 0.4);
}

.connection-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.info-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-weight: 600;
  color: #b0b0b0;
}

.value {
  font-weight: 600;
}

.status-connected { color: #2ecc71; }
.status-connecting { color: #f39c12; }
.status-error { color: #e74c3c; }
.status-disconnected { color: #95a5a6; }

@media (max-width: 768px) {
  .header h1 {
    font-size: 2rem;
  }
  
  .main-content {
    padding: 1rem;
  }
  
  .connection-info {
    grid-template-columns: 1fr;
  }
  
  .info-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .control-btn {
    min-width: 150px;
  }
}
</style> 