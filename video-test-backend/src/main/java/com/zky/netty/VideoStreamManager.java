package com.zky.netty;

import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.channel.group.ChannelGroup;
import io.netty.channel.group.DefaultChannelGroup;
import io.netty.handler.codec.http.websocketx.BinaryWebSocketFrame;
import io.netty.util.concurrent.GlobalEventExecutor;
import org.springframework.stereotype.Component;

@Component
public class VideoStreamManager {
    
    private final ChannelGroup webSocketChannels = new DefaultChannelGroup(GlobalEventExecutor.INSTANCE);
    
    public void addWebSocketChannel(Channel channel) {
        webSocketChannels.add(channel);
        System.out.println("WebSocket client connected. Total clients: " + webSocketChannels.size());
    }
    
    public void removeWebSocketChannel(Channel channel) {
        webSocketChannels.remove(channel);
        System.out.println("WebSocket client disconnected. Total clients: " + webSocketChannels.size());
    }
    
    public void broadcastVideoData(byte[] data) {
        if (!webSocketChannels.isEmpty()) {
            BinaryWebSocketFrame frame = new BinaryWebSocketFrame(Unpooled.wrappedBuffer(data));
            webSocketChannels.writeAndFlush(frame);
            System.out.println("Broadcasted " + data.length + " bytes to " + webSocketChannels.size() + " clients");
        }
    }
    
    public int getWebSocketClientCount() {
        return webSocketChannels.size();
    }
}