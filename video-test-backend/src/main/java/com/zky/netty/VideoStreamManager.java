package com.zky.netty;

import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.handler.codec.http.websocketx.BinaryWebSocketFrame;
import org.springframework.stereotype.Component;

import java.util.concurrent.CopyOnWriteArrayList;
import java.util.List;
import java.nio.ByteBuffer;

@Component
public class VideoStreamManager {
    
    private final List<Channel> webSocketChannels = new CopyOnWriteArrayList<>();
    
    // MPEG-TS包重组缓冲区
    private ByteBuffer mpegtsBuffer = ByteBuffer.allocate(64 * 1024); // 64KB缓冲区
    private static final int MPEGTS_PACKET_SIZE = 188; // MPEG-TS标准包大小
    private static final byte MPEGTS_SYNC_BYTE = 0x47; // MPEG-TS同步字节
    
    public void addWebSocketChannel(Channel channel) {
        webSocketChannels.add(channel);
        System.out.println("WebSocket client connected: " + channel.remoteAddress() + 
                          ", Total clients: " + webSocketChannels.size());
    }
    
    public void removeWebSocketChannel(Channel channel) {
        webSocketChannels.remove(channel);
        System.out.println("WebSocket client disconnected: " + channel.remoteAddress() + 
                          ", Total clients: " + webSocketChannels.size());
    }
    
    public void broadcastVideoData(byte[] data) {
        if (webSocketChannels.isEmpty()) {
            return;
        }
        
        System.out.println("Received video data: " + data.length + " bytes");
        
        // 根据数据特征选择处理方式
        byte[] processedData;
        if (isH264RawStream(data)) {
            // 如果是H.264裸流，直接发送（需要客户端支持）
            processedData = data;
            System.out.println("Detected H.264 raw stream");
        } else if (isMpegtsStream(data)) {
            // 如果是MPEG-TS流，重组包边界
            processedData = processMpegtsData(data);
            System.out.println("Processing MPEG-TS stream, output: " + 
                              (processedData != null ? processedData.length : 0) + " bytes");
        } else {
            // 默认直接发送
            processedData = data;
            System.out.println("Unknown stream format, sending as-is");
        }
        
        // 广播到所有WebSocket客户端
        if (processedData != null && processedData.length > 0) {
            broadcastToClients(processedData);
        }
    }
    
    private boolean isH264RawStream(byte[] data) {
        // 检查H.264起始码
        if (data.length >= 4) {
            return (data[0] == 0x00 && data[1] == 0x00 && 
                   data[2] == 0x00 && data[3] == 0x01) ||
                   (data[0] == 0x00 && data[1] == 0x00 && data[2] == 0x01);
        }
        return false;
    }
    
    private boolean isMpegtsStream(byte[] data) {
        // 检查MPEG-TS同步字节
        for (int i = 0; i < Math.min(data.length, 512); i++) {
            if (data[i] == MPEGTS_SYNC_BYTE) {
                return true;
            }
        }
        return false;
    }
    
    private byte[] processMpegtsData(byte[] newData) {
        // 将新数据添加到缓冲区
        if (mpegtsBuffer.remaining() < newData.length) {
            // 缓冲区不够，压缩现有数据
            mpegtsBuffer.compact();
        }
        
        try {
            mpegtsBuffer.put(newData);
        } catch (Exception e) {
            // 缓冲区溢出，重置
            System.out.println("Buffer overflow, resetting MPEG-TS buffer");
            mpegtsBuffer.clear();
            mpegtsBuffer.put(newData);
        }
        
        // 提取完整的MPEG-TS包
        return extractMpegtsPackets();
    }
    
    private byte[] extractMpegtsPackets() {
        mpegtsBuffer.flip(); // 切换到读模式
        
        ByteBuffer outputBuffer = ByteBuffer.allocate(mpegtsBuffer.capacity());
        int validPackets = 0;
        
        // 查找并提取完整的MPEG-TS包
        while (mpegtsBuffer.remaining() >= MPEGTS_PACKET_SIZE) {
            // 查找同步字节
            boolean syncFound = false;
            int syncPosition = mpegtsBuffer.position();
            
            // 在当前位置查找同步字节
            for (int i = 0; i < mpegtsBuffer.remaining(); i++) {
                if (mpegtsBuffer.get(mpegtsBuffer.position() + i) == MPEGTS_SYNC_BYTE) {
                    syncPosition = mpegtsBuffer.position() + i;
                    syncFound = true;
                    break;
                }
            }
            
            if (!syncFound) {
                // 没找到同步字节，清空缓冲区
                break;
            }
            
            // 移动到同步字节位置
            mpegtsBuffer.position(syncPosition);
            
            // 检查是否有完整的包
            if (mpegtsBuffer.remaining() >= MPEGTS_PACKET_SIZE) {
                // 提取一个完整的MPEG-TS包
                byte[] packet = new byte[MPEGTS_PACKET_SIZE];
                mpegtsBuffer.get(packet);
                
                // 验证包的有效性
                if (packet[0] == MPEGTS_SYNC_BYTE) {
                    outputBuffer.put(packet);
                    validPackets++;
                } else {
                    // 同步字节不匹配，回退一个字节继续搜索
                    mpegtsBuffer.position(syncPosition + 1);
                }
            } else {
                // 数据不够一个完整包，跳出循环
                break;
            }
        }
        
        // 将剩余数据移到缓冲区开头
        mpegtsBuffer.compact();
        
        // 返回提取的完整包
        if (validPackets > 0) {
            outputBuffer.flip();
            byte[] result = new byte[outputBuffer.remaining()];
            outputBuffer.get(result);
            
            System.out.println("Extracted " + validPackets + " valid MPEG-TS packets (" + 
                              result.length + " bytes)");
            return result;
        }
        
        return null; // 没有完整的包
    }
    
    private void broadcastToClients(byte[] data) {
        if (webSocketChannels.isEmpty()) {
            return;
        }
        
        // 创建WebSocket二进制帧
        BinaryWebSocketFrame frame = new BinaryWebSocketFrame(Unpooled.wrappedBuffer(data));
        
        // 广播到所有活跃的客户端
        List<Channel> disconnectedChannels = new CopyOnWriteArrayList<>();
        
        for (Channel channel : webSocketChannels) {
            if (channel.isActive()) {
                try {
                    // 为每个客户端创建独立的帧副本
                    BinaryWebSocketFrame clientFrame = new BinaryWebSocketFrame(
                        Unpooled.wrappedBuffer(data)
                    );
                    channel.writeAndFlush(clientFrame);
                } catch (Exception e) {
                    System.err.println("Error sending data to client: " + e.getMessage());
                    disconnectedChannels.add(channel);
                }
            } else {
                disconnectedChannels.add(channel);
            }
        }
        
        // 清理断开的连接
        for (Channel channel : disconnectedChannels) {
            removeWebSocketChannel(channel);
        }
        
        System.out.println("Broadcasted " + data.length + " bytes to " + 
                          (webSocketChannels.size()) + " clients");
    }
}