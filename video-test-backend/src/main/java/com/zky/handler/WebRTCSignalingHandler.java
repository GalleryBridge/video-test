package com.zky.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.socket.*;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class WebRTCSignalingHandler implements WebSocketHandler {
    
    private static final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String sessionId = session.getId();
        sessions.put(sessionId, session);
        System.out.println("WebRTC客户端连接: " + sessionId);
        
        // 发送欢迎消息
        sendMessage(session, "connected", "WebRTC信令服务器连接成功");
    }

    @Override
    public void handleMessage(WebSocketSession session, WebSocketMessage<?> message) throws Exception {
        String payload = message.getPayload().toString();
        System.out.println("收到信令消息: " + payload);
        
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> messageData = objectMapper.readValue(payload, Map.class);
            String type = (String) messageData.get("type");
            
            switch (type) {
                case "offer":
                    handleOffer(session, messageData);
                    break;
                case "answer": 
                    handleAnswer(session, messageData);
                    break;
                case "ice-candidate":
                    handleIceCandidate(session, messageData);
                    break;
                case "request-stream":
                    handleStreamRequest(session, messageData);
                    break;
                default:
                    System.out.println("未知消息类型: " + type);
            }
        } catch (Exception e) {
            System.err.println("处理信令消息时出错: " + e.getMessage());
            e.printStackTrace();
        }
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        System.err.println("WebSocket传输错误: " + exception.getMessage());
        exception.printStackTrace();
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus closeStatus) throws Exception {
        String sessionId = session.getId();
        sessions.remove(sessionId);
        System.out.println("WebRTC客户端断开连接: " + sessionId);
    }

    @Override
    public boolean supportsPartialMessages() {
        return false;
    }

    private void handleOffer(WebSocketSession session, Map<String, Object> messageData) {
        System.out.println("处理Offer消息");
        // 这里应该与媒体服务器交互，创建WebRTC连接
        // 暂时返回一个模拟的answer
        try {
            sendMessage(session, "answer", "模拟的SDP Answer");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void handleAnswer(WebSocketSession session, Map<String, Object> messageData) {
        System.out.println("处理Answer消息");
    }

    private void handleIceCandidate(WebSocketSession session, Map<String, Object> messageData) {
        System.out.println("处理ICE候选");
    }

    private void handleStreamRequest(WebSocketSession session, Map<String, Object> messageData) {
        System.out.println("处理视频流请求");
        try {
            // 通知客户端开始准备接收视频流
            sendMessage(session, "stream-ready", "视频流准备就绪");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void sendMessage(WebSocketSession session, String type, Object data) throws IOException {
        Map<String, Object> response = Map.of(
            "type", type,
            "data", data,
            "timestamp", System.currentTimeMillis()
        );
        String jsonResponse = objectMapper.writeValueAsString(response);
        session.sendMessage(new TextMessage(jsonResponse));
    }
} 