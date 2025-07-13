package com.zky.netty.websocket;

import com.zky.netty.VideoStreamManager;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.http.websocketx.BinaryWebSocketFrame;
import io.netty.handler.codec.http.websocketx.CloseWebSocketFrame;
import io.netty.handler.codec.http.websocketx.PingWebSocketFrame;
import io.netty.handler.codec.http.websocketx.PongWebSocketFrame;
import io.netty.handler.codec.http.websocketx.TextWebSocketFrame;
import io.netty.handler.codec.http.websocketx.WebSocketFrame;

public class WebSocketServerHandler extends SimpleChannelInboundHandler<WebSocketFrame> {
    
    private final VideoStreamManager videoStreamManager;
    
    public WebSocketServerHandler(VideoStreamManager videoStreamManager) {
        this.videoStreamManager = videoStreamManager;
    }
    
    @Override
    public void channelActive(ChannelHandlerContext ctx) {
        videoStreamManager.addWebSocketChannel(ctx.channel());
    }
    
    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        videoStreamManager.removeWebSocketChannel(ctx.channel());
    }
    
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, WebSocketFrame frame) {
        if (frame instanceof TextWebSocketFrame) {
            String text = ((TextWebSocketFrame) frame).text();
            System.out.println("Received text message: " + text);
            
            if ("ping".equals(text)) {
                ctx.writeAndFlush(new TextWebSocketFrame("pong"));
            }
            
        } else if (frame instanceof PingWebSocketFrame) {
            ctx.writeAndFlush(new PongWebSocketFrame(frame.content().retain()));
            
        } else if (frame instanceof CloseWebSocketFrame) {
            ctx.close();
        }
    }
    
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        cause.printStackTrace();
        ctx.close();
    }
    
    public void sendVideoData(ChannelHandlerContext ctx, byte[] data) {
        if (ctx.channel().isActive()) {
            ctx.writeAndFlush(new BinaryWebSocketFrame(Unpooled.wrappedBuffer(data)));
        }
    }
}