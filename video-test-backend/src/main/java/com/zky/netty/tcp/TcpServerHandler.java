package com.zky.netty.tcp;

import com.zky.netty.VideoStreamManager;
import io.netty.buffer.ByteBuf;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;

public class TcpServerHandler extends ChannelInboundHandlerAdapter {
    
    private final VideoStreamManager videoStreamManager;
    
    public TcpServerHandler(VideoStreamManager videoStreamManager) {
        this.videoStreamManager = videoStreamManager;
    }
    
    @Override
    public void channelActive(ChannelHandlerContext ctx) {
        System.out.println("TCP client connected: " + ctx.channel().remoteAddress());
    }
    
    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        if (msg instanceof ByteBuf) {
            ByteBuf buf = (ByteBuf) msg;
            try {
                byte[] data = new byte[buf.readableBytes()];
                buf.readBytes(data);
                
                System.out.println("Received video data: " + data.length + " bytes");
                
                videoStreamManager.broadcastVideoData(data);
                
            } finally {
                buf.release();
            }
        }
    }
    
    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        System.out.println("TCP client disconnected: " + ctx.channel().remoteAddress());
    }
    
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        cause.printStackTrace();
        ctx.close();
    }
}