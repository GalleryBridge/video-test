<template>
  <div class="video-player">
    <div class="video-container">
      <video
        ref="videoElement"
        :width="1280"
        :height="720"
        controls
        autoplay
        muted
        playsinline
        preload="none"
        class="video-element"
      >
        <p>您的浏览器不支持HTML5视频播放。</p>
      </video>
      
      <div class="video-overlay">
        <div class="status-info">
          <div :class="['connection-status', connectionStatus]">
            {{ connectionStatusText }}
          </div>
          <div class="video-info">
            <span>分辨率: {{ videoResolution }}</span>
            <span>编码: H.264/HLS</span>
            <span>延迟: {{ streamDelay }}s</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="controls">
      <button @click="toggleStream" :disabled="isLoading" class="stream-button">
        {{ isPlaying ? '停止播放' : '开始播放' }}
      </button>
      
      <button @click="refreshStream" :disabled="isLoading" class="refresh-button">
        刷新流
      </button>
      
      <button @click="checkStreamStatus" class="status-button">
        检查状态
      </button>
    </div>
    
    <div class="stream-info">
      <div class="info-row">
        <span class="label">HLS地址:</span>
        <code class="url">{{ hlsUrl }}</code>
      </div>
      <div class="info-row">
        <span class="label">服务器:</span>
        <span>{{ serverHost }}:8080</span>
      </div>
      <div class="info-row" v-if="streamInfo.segmentCount !== undefined">
        <span class="label">切片数量:</span>
        <span>{{ streamInfo.segmentCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import Hls from 'hls.js'

const videoElement = ref<HTMLVideoElement>()
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error' | 'loading'>('disconnected')
const isLoading = ref(false)
const isPlaying = ref(false)
const serverHost = ref('192.168.1.196')
const videoResolution = ref('1280x720')
const streamDelay = ref(2)

// HLS相关
let hls: Hls | null = null
const hlsUrl = computed(() => `http://${serverHost.value}:8080/hls/stream.m3u8`)

// 流信息
const streamInfo = ref({
  segmentCount: 0,
  lastModified: 0,
  isActive: false
})

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'disconnected': return '未连接'
    case 'connecting': return '连接中...'
    case 'connected': return '已连接'
    case 'loading': return '加载中...'
    case 'error': return '连接错误'
    default: return '未知状态'
  }
})

// 检查浏览器HLS支持
const checkHlsSupport = () => {
  if (Hls.isSupported()) {
    console.log('✅ 浏览器支持HLS.js')
    return true
  } else if (videoElement.value?.canPlayType('application/vnd.apple.mpegurl')) {
    console.log('✅ 浏览器原生支持HLS')
    return true
  } else {
    console.error('❌ 浏览器不支持HLS播放')
    connectionStatus.value = 'error'
    return false
  }
}

// 初始化HLS播放器
const initializeHlsPlayer = () => {
  if (!videoElement.value) return

  // 清理现有播放器
  if (hls) {
    hls.destroy()
    hls = null
  }

  if (Hls.isSupported()) {
    // 使用HLS.js
    hls = new Hls({
      debug: false,
      enableWorker: true,
      lowLatencyMode: true,
      backBufferLength: 90,
      maxBufferLength: 30,
      maxMaxBufferLength: 60,
      liveSyncDurationCount: 3,
      liveMaxLatencyDurationCount: 5
    })

    hls.loadSource(hlsUrl.value)
    hls.attachMedia(videoElement.value)

    // HLS事件监听
    hls.on(Hls.Events.MEDIA_ATTACHED, () => {
      console.log('HLS媒体已附加')
      connectionStatus.value = 'connecting'
    })

    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      console.log('HLS清单解析完成')
      connectionStatus.value = 'connected'
      isPlaying.value = true
      
      // 开始播放
      videoElement.value?.play().catch(error => {
        console.error('播放失败:', error)
        connectionStatus.value = 'error'
      })
    })

    hls.on(Hls.Events.ERROR, (event, data) => {
      console.error('HLS错误:', data)
      
      if (data.fatal) {
        connectionStatus.value = 'error'
        isPlaying.value = false
        
        switch (data.type) {
          case Hls.ErrorTypes.NETWORK_ERROR:
            console.error('网络错误，尝试恢复...')
            hls?.startLoad()
            break
          case Hls.ErrorTypes.MEDIA_ERROR:
            console.error('媒体错误，尝试恢复...')
            hls?.recoverMediaError()
            break
          default:
            console.error('无法恢复的错误')
            hls?.destroy()
            hls = null
            break
        }
      }
    })

  } else if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
    // 使用原生HLS支持(Safari)
    videoElement.value.src = hlsUrl.value
    connectionStatus.value = 'connecting'
    
    videoElement.value.addEventListener('loadstart', () => {
      connectionStatus.value = 'connected'
      isPlaying.value = true
    })
  }
}

// 开始播放流
const startStream = async () => {
  if (!checkHlsSupport()) return

  connectionStatus.value = 'loading'
  isLoading.value = true

  try {
    // 等待下一帧确保DOM已更新
    await nextTick()
    
    // 初始化播放器
    initializeHlsPlayer()

  } catch (error) {
    console.error('启动流失败:', error)
    connectionStatus.value = 'error'
  } finally {
    isLoading.value = false
  }
}

// 停止播放流
const stopStream = () => {
  isLoading.value = true

  if (videoElement.value) {
    videoElement.value.pause()
    videoElement.value.src = ''
  }

  if (hls) {
    hls.destroy()
    hls = null
  }

  connectionStatus.value = 'disconnected'
  isPlaying.value = false
  isLoading.value = false

  console.log('HLS流已停止')
}

// 切换播放状态
const toggleStream = () => {
  if (isPlaying.value) {
    stopStream()
  } else {
    startStream()
  }
}

// 刷新流
const refreshStream = async () => {
  if (isPlaying.value) {
    stopStream()
    // 短暂延迟后重新开始
    setTimeout(() => {
      startStream()
    }, 1000)
  }
}

// 检查流状态
const checkStreamStatus = async () => {
  try {
    const response = await fetch(`http://${serverHost.value}:8080/api/hls/status`)
    const data = await response.json()
    
    streamInfo.value = {
      segmentCount: data.segmentCount || 0,
      lastModified: data.lastModified || 0,
      isActive: data.isActive || false
    }
    
    console.log('流状态:', data)
    
    if (!data.isActive || !data.playlistExists) {
      connectionStatus.value = 'error'
      console.warn('HLS流不可用，请检查FFmpeg是否正在运行')
    }
    
  } catch (error) {
    console.error('检查流状态失败:', error)
    connectionStatus.value = 'error'
  }
}

// 组件挂载时检查状态
onMounted(() => {
  console.log('HLS视频播放器已挂载')
  checkStreamStatus()
})

// 组件卸载时清理资源
onUnmounted(() => {
  stopStream()
  console.log('HLS视频播放器已卸载')
})
</script>

<style scoped>
.video-player {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.video-container {
  position: relative;
  display: inline-block;
  border: 2px solid #ddd;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

.video-element {
  display: block;
  width: 100%;
  height: auto;
  background: #000;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
  padding: 15px;
  pointer-events: none;
}

.status-info {
  color: white;
  font-size: 13px;
}

.connection-status {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 14px;
}

.connection-status.connected {
  color: #4CAF50;
}

.connection-status.connecting, .connection-status.loading {
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
  gap: 3px;
  opacity: 0.9;
}

.controls {
  margin-top: 20px;
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.stream-button, .refresh-button, .status-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.stream-button {
  background: linear-gradient(135deg, #4CAF50 0%, #45A049 100%);
  color: white;
}

.stream-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #45A049 0%, #3D8B40 100%);
  transform: translateY(-1px);
}

.refresh-button {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
}

.refresh-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
  transform: translateY(-1px);
}

.status-button {
  background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
  color: white;
}

.status-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #F57C00 0%, #E65100 100%);
  transform: translateY(-1px);
}

button:disabled {
  background: #BDBDBD !important;
  cursor: not-allowed;
  transform: none;
}

.stream-info {
  margin-top: 25px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 600;
  color: #495057;
  min-width: 100px;
  margin-right: 10px;
}

.url {
  background: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #495057;
  word-break: break-all;
}

@media (max-width: 768px) {
  .video-player {
    padding: 10px;
  }
  
  .controls {
    flex-direction: column;
    align-items: center;
  }
  
  .stream-button, .refresh-button, .status-button {
    width: 100%;
    max-width: 200px;
  }
}</style>