<script setup lang="ts">
import VideoPlayer from './components/VideoPlayer.vue'
</script>

<template>
  <div id="app">
    <header>
      <h1>实时视频流播放器</h1>
      <p>基于WebSocket + JSMpeg的H.264视频流播放</p>
    </header>
    <main>
      <VideoPlayer />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f5f5;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
}

header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  padding: 2rem 1rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  font-weight: 300;
}

header p {
  font-size: 1.1rem;
  opacity: 0.9;
}

main {
  padding: 2rem 1rem;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
