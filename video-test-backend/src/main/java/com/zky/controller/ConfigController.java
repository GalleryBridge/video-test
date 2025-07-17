package com.zky.controller;

import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;

@RestController
@RequestMapping("/api/config")
@CrossOrigin(origins = "*")
public class ConfigController {

    @GetMapping("/webrtc")
    public Map<String, Object> getWebRTCConfig() {
        Map<String, Object> config = new HashMap<>();
        
        // STUN服务器配置
        config.put("iceServers", Arrays.asList(
            Map.of("urls", "stun:stun.l.google.com:19302"),
            Map.of("urls", "stun:stun1.l.google.com:19302")
        ));
        
        // WebRTC媒体服务器地址
        config.put("mediaServerUrl", "ws://localhost:8765");
        
        // 视频配置
        Map<String, Object> videoConfig = new HashMap<>();
        videoConfig.put("width", 640);
        videoConfig.put("height", 480);
        videoConfig.put("fps", 30);
        config.put("video", videoConfig);
        
        return config;
    }
    
    @GetMapping("/status")
    public Map<String, Object> getSystemStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("signaling", "online");
        status.put("timestamp", System.currentTimeMillis());
        status.put("version", "1.0.0");
        return status;
    }
} 