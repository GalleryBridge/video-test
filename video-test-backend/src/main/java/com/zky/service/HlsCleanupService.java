package com.zky.service;

import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Service
public class HlsCleanupService {

    private final ResourceLoader resourceLoader;
    private static final long MAX_FILE_AGE_MS = 30 * 1000; // 30秒
    private static final int MAX_SEGMENT_COUNT = 10; // 最多保留10个切片

    public HlsCleanupService(ResourceLoader resourceLoader) {
        this.resourceLoader = resourceLoader;
    }

    /**
     * 定期清理过期的HLS切片文件
     * 每10秒执行一次
     */
    @Scheduled(fixedRate = 10000)
    public void cleanupOldSegments() {
        try {
            Resource hlsDir = resourceLoader.getResource("classpath:static/hls/");
            File dir = hlsDir.getFile();

            if (!dir.exists() || !dir.isDirectory()) {
                return;
            }

            // 获取所有.ts文件
            File[] segments = dir.listFiles((d, name) -> name.endsWith(".ts"));
            if (segments == null || segments.length <= MAX_SEGMENT_COUNT) {
                return;
            }

            // 按修改时间排序（最新的在前）
            java.util.Arrays.sort(segments, (a, b) -> 
                Long.compare(b.lastModified(), a.lastModified()));

            int deletedCount = 0;
            long currentTime = System.currentTimeMillis();

            // 删除过期文件（保留最新的MAX_SEGMENT_COUNT个文件）
            for (int i = MAX_SEGMENT_COUNT; i < segments.length; i++) {
                File segment = segments[i];
                if (currentTime - segment.lastModified() > MAX_FILE_AGE_MS) {
                    if (segment.delete()) {
                        deletedCount++;
                    }
                }
            }

            if (deletedCount > 0) {
                String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
                System.out.println(String.format("[%s] 清理了 %d 个过期的HLS切片文件", time, deletedCount));
            }

        } catch (IOException e) {
            System.err.println("清理HLS文件时出错: " + e.getMessage());
        }
    }

    /**
     * 手动清理所有HLS文件
     */
    public int cleanupAllFiles() {
        try {
            Resource hlsDir = resourceLoader.getResource("classpath:static/hls/");
            File dir = hlsDir.getFile();

            if (!dir.exists() || !dir.isDirectory()) {
                return 0;
            }

            File[] files = dir.listFiles();
            int deletedCount = 0;

            if (files != null) {
                for (File file : files) {
                    if (file.isFile() && file.delete()) {
                        deletedCount++;
                    }
                }
            }

            String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
            System.out.println(String.format("[%s] 手动清理了 %d 个HLS文件", time, deletedCount));
            return deletedCount;

        } catch (IOException e) {
            System.err.println("手动清理HLS文件时出错: " + e.getMessage());
            return 0;
        }
    }

    /**
     * 检查HLS目录状态
     */
    public boolean isHlsDirectoryReady() {
        try {
            Resource hlsDir = resourceLoader.getResource("classpath:static/hls/");
            File dir = hlsDir.getFile();
            return dir.exists() && dir.isDirectory();
        } catch (IOException e) {
            return false;
        }
    }
} 