<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

// 响应式数据
const isConnected = ref(false)
const isConnecting = ref(false)
const connectionStatus = ref('未连接')
const statusText = ref('点击开始播放按钮开始视频流')
const videoResolution = ref('--')
const videoElement = ref<HTMLVideoElement | null>(null)

// WebRTC 相关变量
let peerConnection: RTCPeerConnection | null = null
let websocket: WebSocket | null = null
let localStream: MediaStream | null = null

// STUN服务器配置
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

// WebSocket连接
async function connectWebSocket(): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      // 连接到WebRTC媒体服务器
      websocket = new WebSocket('ws://localhost:8765')
      
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
    case 'answer':
      await handleAnswer(data)
      break
    case 'ice-candidate':
      await handleIceCandidate(data)
      break
    case 'error':
      console.error('服务器错误:', data.message)
      statusText.value = `错误: ${data.message}`
      connectionStatus.value = '连接失败'
      break
    default:
      console.log('收到未知类型消息:', data.type)
  }
}

// 创建WebRTC连接
async function createPeerConnection(): Promise<void> {
  peerConnection = new RTCPeerConnection(rtcConfiguration)
  
  // 监听ICE候选
  peerConnection.onicecandidate = (event) => {
    if (event.candidate && websocket) {
      websocket.send(JSON.stringify({
        type: 'ice-candidate',
        candidate: event.candidate
      }))
    }
  }
  
  // 监听远程视频流
  peerConnection.ontrack = (event) => {
    console.log('收到远程视频流')
    if (videoElement.value) {
      videoElement.value.srcObject = event.streams[0]
      
      // 获取视频分辨率
      event.streams[0].getVideoTracks()[0].addEventListener('loadedmetadata', () => {
        if (videoElement.value) {
          videoResolution.value = `${videoElement.value.videoWidth}x${videoElement.value.videoHeight}`
        }
      })
    }
  }
  
  // 监听连接状态变化
  peerConnection.onconnectionstatechange = () => {
    const state = peerConnection?.connectionState
    console.log('WebRTC连接状态:', state)
    
    switch (state) {
      case 'connected':
        isConnected.value = true
        isConnecting.value = false
        connectionStatus.value = '已连接'
        statusText.value = '视频流已连接'
        break
      case 'connecting':
        connectionStatus.value = '连接中'
        break
      case 'disconnected':
      case 'failed':
      case 'closed':
        isConnected.value = false
        isConnecting.value = false
        connectionStatus.value = '连接失败'
        statusText.value = '连接已断开'
        break
    }
  }
  
  // 创建offer
  const offer = await peerConnection.createOffer({
    offerToReceiveVideo: true,
    offerToReceiveAudio: false
  })
  
  await peerConnection.setLocalDescription(offer)
  
  // 发送offer到服务器
  if (websocket) {
    websocket.send(JSON.stringify({
      type: 'offer',
      sdp: offer.sdp
    }))
  }
}

// 处理Answer
async function handleAnswer(data: any) {
  if (peerConnection) {
    const answer = new RTCSessionDescription({
      type: 'answer',
      sdp: data.sdp
    })
    await peerConnection.setRemoteDescription(answer)
    console.log('设置远程描述成功')
  }
}

// 处理ICE候选
async function handleIceCandidate(data: any) {
  if (peerConnection && data.candidate) {
    await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate))
  }
}

// 开始连接
async function startConnection() {
  try {
    isConnecting.value = true
    statusText.value = '正在连接WebSocket...'
    
    await connectWebSocket()
    
    statusText.value = '正在建立WebRTC连接...'
    await createPeerConnection()
    
  } catch (error) {
    console.error('连接失败:', error)
    statusText.value = '连接失败，请检查网络和服务器状态'
    connectionStatus.value = '连接失败'
    isConnecting.value = false
  }
}

// 停止连接
function stopConnection() {
  cleanup()
  statusText.value = '已断开连接'
  connectionStatus.value = '未连接'
}

// 清理资源
function cleanup() {
  if (peerConnection) {
    peerConnection.close()
    peerConnection = null
  }
  
  if (websocket) {
    websocket.close()
    websocket = null
  }
  
  if (videoElement.value) {
    videoElement.value.srcObject = null
  }
  
  isConnected.value = false
  isConnecting.value = false
  videoResolution.value = '--'
}

// 切换连接状态
async function toggleConnection() {
  if (isConnected.value || isConnecting.value) {
    stopConnection()
  } else {
    await startConnection()
  }
}

// 生命周期钩子
onMounted(() => {
  console.log('WebRTC视频监控系统已加载')
})

onUnmounted(() => {
  cleanup()
})
</script>

<template>
  <div id="app">
    <header class="header">
      <h1>WebRTC视频监控系统</h1>
    </header>
    
    <main class="main-content">
      <div class="video-container">
        <video
          ref="videoElement"
          autoplay
          playsinline
          muted
          class="video-player"
          :class="{ 'connected': isConnected }"
        ></video>
        
        <div v-if="!isConnected" class="video-overlay">
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
          :class="{ 'connecting': isConnecting, 'connected': isConnected }"
          :disabled="isConnecting"
        >
          <span v-if="!isConnected && !isConnecting">开始播放</span>
          <span v-else-if="isConnecting">连接中...</span>
          <span v-else>停止播放</span>
        </button>
        
        <div class="connection-info">
          <div class="info-item">
            <span class="label">连接状态:</span>
            <span class="value" :class="connectionStatusClass">{{ connectionStatus }}</span>
          </div>
          <div class="info-item" v-if="isConnected">
            <span class="label">视频分辨率:</span>
            <span class="value">{{ videoResolution }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

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
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.video-container {
  position: relative;
  width: 100%;
  max-width: 800px;
  margin: 0 auto 2rem;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.video-player {
  width: 100%;
  height: auto;
  min-height: 400px;
  display: block;
  background: #1a1a1a;
  transition: all 0.3s ease;
}

.video-player.connected {
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.5);
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
  min-width: 150px;
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
  background: linear-gradient(45deg, #e74c3c, #c0392b);
}

.connection-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
}
</style>
