package com.zky.controller;

import com.zky.service.HlsCleanupService;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/hls")
@CrossOrigin(origins = "*")
public class HlsController {

    private final ResourceLoader resourceLoader;
    private final HlsCleanupService hlsCleanupService;

    public HlsController(ResourceLoader resourceLoader, HlsCleanupService hlsCleanupService) {
        this.resourceLoader = resourceLoader;
        this.hlsCleanupService = hlsCleanupService;
    }

    /**
     * 获取HLS流状态信息
     */
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStreamStatus() {
        Map<String, Object> status = new HashMap<>();
        
        try {
            Resource hlsDir = resourceLoader.getResource("classpath:static/hls/");
            File dir = hlsDir.getFile();
            
            status.put("isActive", dir.exists() && dir.isDirectory());
            
            if (dir.exists()) {
                File playlist = new File(dir, "stream.m3u8");
                status.put("playlistExists", playlist.exists());
                status.put("playlistUrl", "/hls/stream.m3u8");
                
                // 统计切片文件数量
                File[] segments = dir.listFiles((d, name) -> name.endsWith(".ts"));
                status.put("segmentCount", segments != null ? segments.length : 0);
                
                if (playlist.exists()) {
                    status.put("lastModified", playlist.lastModified());
                }
            }
            
            status.put("timestamp", System.currentTimeMillis());
            
        } catch (IOException e) {
            status.put("isActive", false);
            status.put("error", e.getMessage());
        }
        
        return ResponseEntity.ok(status);
    }

    /**
     * 清理HLS文件
     */
    @PostMapping("/cleanup")
    public ResponseEntity<Map<String, Object>> cleanupHlsFiles() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            int deletedCount = hlsCleanupService.cleanupAllFiles();
            result.put("success", true);
            result.put("deletedCount", deletedCount);
            result.put("message", "HLS文件清理完成");
            
        } catch (Exception e) {
            result.put("success", false);
            result.put("error", e.getMessage());
        }
        
        return ResponseEntity.ok(result);
    }

    /**
     * 获取播放列表内容
     */
    @GetMapping("/playlist")
    public ResponseEntity<String> getPlaylist() {
        try {
            Resource hlsDir = resourceLoader.getResource("classpath:static/hls/");
            File playlist = new File(hlsDir.getFile(), "stream.m3u8");
            
            if (playlist.exists()) {
                Path path = Paths.get(playlist.getAbsolutePath());
                // Java 8兼容：使用readAllBytes而不是readString
                byte[] bytes = Files.readAllBytes(path);
                String content = new String(bytes, "UTF-8");
                
                return ResponseEntity.ok()
                        .header(HttpHeaders.CONTENT_TYPE, "application/vnd.apple.mpegurl")
                        .body(content);
            } else {
                return ResponseEntity.notFound().build();
            }
            
        } catch (IOException e) {
            return ResponseEntity.internalServerError()
                    .body("Error reading playlist: " + e.getMessage());
        }
    }
} 