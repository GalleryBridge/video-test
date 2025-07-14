<template>
  <div class="video-player">
    <div class="video-container">
      <canvas ref="videoCanvas" :width="640" :height="480"></canvas>
      <div class="video-overlay">
        <div class="status-info">
          <div :class="['connection-status', connectionStatus]">
            {{ connectionStatusText }}
          </div>
          <div class="video-info">
            <span>分辨率: 640x480</span>
            <span>帧率: ~15fps</span>
            <span>编码: H.264/MPEG-TS</span>
          </div>
        </div>
      </div>
    </div>
    <div class="controls">
      <button @click="toggleConnection" :disabled="isConnecting">
        {{ isConnected ? '断开连接' : '连接视频流' }}
      </button>
      <div class="connection-info">
        <span>WebSocket地址: ws://{{ serverHost }}:8103/video</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

// 声明全局JSMpeg类型
declare global {
  interface Window {
    JSMpeg: any;
  }
}

const videoCanvas = ref<HTMLCanvasElement>()
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
const isConnecting = ref(false)
const isConnected = ref(false)
const serverHost = ref('192.168.1.196')

let webSocket: WebSocket | null = null
let player: any = null

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'disconnected': return '未连接'
    case 'connecting': return '连接中...'
    case 'connected': return '已连接'
    case 'error': return '连接错误'
    default: return '未知状态'
  }
})

const connectToVideoStream = () => {
  if (isConnected.value || isConnecting.value) return
  
  connectionStatus.value = 'connecting'
  isConnecting.value = true
  
  try {
    const wsUrl = `ws://${serverHost.value}:8103/video`
    webSocket = new WebSocket(wsUrl)
    webSocket.binaryType = 'arraybuffer'
    
    webSocket.onopen = () => {
      console.log('WebSocket连接成功')
      connectionStatus.value = 'connected'
      isConnected.value = true
      isConnecting.value = false
      
      if (videoCanvas.value && window.JSMpeg) {
        // 使用全局JSMpeg对象
        player = new window.JSMpeg.Player(null, {
          canvas: videoCanvas.value,
          autoplay: true,
          audio: false,
          loop: false,
          streaming: true
        })
      } else if (!window.JSMpeg) {
        console.error('JSMpeg未加载')
        connectionStatus.value = 'error'
      }
    }
    
    webSocket.onmessage = (event) => {
      if (player && event.data) {
        const uint8Array = new Uint8Array(event.data)
        player.write(uint8Array)
      }
    }
    
    webSocket.onclose = () => {
      console.log('WebSocket连接关闭')
      connectionStatus.value = 'disconnected'
      isConnected.value = false
      isConnecting.value = false
      
      if (player) {
        player.destroy()
        player = null
      }
    }
    
    webSocket.onerror = (error) => {
      console.error('WebSocket错误:', error)
      connectionStatus.value = 'error'
      isConnected.value = false
      isConnecting.value = false
    }
    
  } catch (error) {
    console.error('连接失败:', error)
    connectionStatus.value = 'error'
    isConnecting.value = false
  }
}

const disconnectFromVideoStream = () => {
  if (webSocket) {
    webSocket.close()
    webSocket = null
  }
  
  if (player) {
    player.destroy()
    player = null
  }
  
  connectionStatus.value = 'disconnected'
  isConnected.value = false
  isConnecting.value = false
}

const toggleConnection = () => {
  if (isConnected.value) {
    disconnectFromVideoStream()
  } else {
    connectToVideoStream()
  }
}

onMounted(() => {
  console.log('VideoPlayer组件已挂载')
})

onUnmounted(() => {
  disconnectFromVideoStream()
})

</script>

<style scoped>
.video-player {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.video-container {
  position: relative;
  display: inline-block;
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

canvas {
  display: block;
  width: 100%;
  height: auto;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7), transparent);
  padding: 10px;
  pointer-events: none;
}

.status-info {
  color: white;
  font-size: 12px;
}

.connection-status {
  font-weight: bold;
  margin-bottom: 5px;
}

.connection-status.connected {
  color: #4CAF50;
}

.connection-status.connecting {
  color: #FF9800;
}

.connection-status.disconnected {
  color: #9E9E9E;
}

.connection-status.error {
  color: #F44336;
}

.video-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  opacity: 0.8;
}

.controls {
  margin-top: 15px;
  text-align: center;
}

button {
  background: #2196F3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 10px;
}

button:hover:not(:disabled) {
  background: #1976D2;
}

button:disabled {
  background: #BDBDBD;
  cursor: not-allowed;
}

.connection-info {
  font-size: 12px;
  color: #666;
}
</style>