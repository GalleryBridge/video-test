#!/usr/bin/env python3
"""
视频监控系统模式切换脚本
支持WebSocket和WebRTC模式快速切换
"""

import os
import shutil
import argparse
import sys

def get_frontend_path():
    """获取前端目录路径"""
    return os.path.join(os.path.dirname(__file__), 'video-test-frontend', 'src')

def check_files_exist(frontend_path):
    """检查必要文件是否存在"""
    app_vue = os.path.join(frontend_path, 'App.vue')
    app_webrtc_vue = os.path.join(frontend_path, 'App_webrtc.vue')
    
    if not os.path.exists(frontend_path):
        print("❌ 错误: 找不到前端目录")
        return False
    
    if not os.path.exists(app_webrtc_vue):
        print("❌ 错误: 找不到WebRTC前端文件 (App_webrtc.vue)")
        return False
    
    return True

def get_current_mode(frontend_path):
    """检测当前模式"""
    app_vue = os.path.join(frontend_path, 'App.vue')
    
    if not os.path.exists(app_vue):
        return "unknown"
    
    try:
        with open(app_vue, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'WebRTC视频监控系统' in content:
                return "webrtc"
            elif 'WebSocket视频监控系统' in content:
                return "websocket"
            else:
                return "unknown"
    except Exception:
        return "unknown"

def backup_current_app(frontend_path):
    """备份当前App.vue"""
    app_vue = os.path.join(frontend_path, 'App.vue')
    backup_path = os.path.join(frontend_path, 'App_backup.vue')
    
    if os.path.exists(app_vue):
        try:
            shutil.copy2(app_vue, backup_path)
            print(f"✅ 已备份当前文件到: App_backup.vue")
            return True
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False
    return True

def switch_to_websocket(frontend_path):
    """切换到WebSocket模式"""
    app_vue = os.path.join(frontend_path, 'App.vue')
    app_websocket_vue = os.path.join(frontend_path, 'App_websocket.vue')
    
    # 如果存在WebSocket版本，直接复制
    if os.path.exists(app_websocket_vue):
        try:
            shutil.copy2(app_websocket_vue, app_vue)
            print("✅ 已切换到WebSocket模式")
            return True
        except Exception as e:
            print(f"❌ 切换失败: {e}")
            return False
    
    # 如果不存在，检查当前是否已经是WebSocket模式
    current_mode = get_current_mode(frontend_path)
    if current_mode == "websocket":
        print("ℹ️ 当前已经是WebSocket模式")
        return True
    
    print("❌ 错误: 找不到WebSocket前端文件")
    return False

def switch_to_webrtc(frontend_path):
    """切换到WebRTC模式"""
    app_vue = os.path.join(frontend_path, 'App.vue')
    app_webrtc_vue = os.path.join(frontend_path, 'App_webrtc.vue')
    
    try:
        shutil.copy2(app_webrtc_vue, app_vue)
        print("✅ 已切换到WebRTC模式")
        return True
    except Exception as e:
        print(f"❌ 切换失败: {e}")
        return False

def show_status():
    """显示当前状态"""
    frontend_path = get_frontend_path()
    
    if not check_files_exist(frontend_path):
        return
    
    current_mode = get_current_mode(frontend_path)
    
    print("📊 当前系统状态:")
    print(f"   前端目录: {frontend_path}")
    
    if current_mode == "websocket":
        print("   当前模式: 🔵 WebSocket (高兼容性)")
        print("   服务器文件: websocket_video_server.py")
    elif current_mode == "webrtc":
        print("   当前模式: 🔴 WebRTC (低延迟)")
        print("   服务器文件: webrtc_server.py")
    else:
        print("   当前模式: ❓ 未知")
    
    print("\n📁 可用文件:")
    files = [
        ("App.vue", "当前使用的前端文件"),
        ("App_webrtc.vue", "WebRTC模式前端"),
    ]
    
    app_websocket = os.path.join(frontend_path, 'App_websocket.vue')
    if os.path.exists(app_websocket):
        files.append(("App_websocket.vue", "WebSocket模式前端"))
    
    app_backup = os.path.join(frontend_path, 'App_backup.vue')
    if os.path.exists(app_backup):
        files.append(("App_backup.vue", "备份文件"))
    
    for filename, description in files:
        filepath = os.path.join(frontend_path, filename)
        status = "✅" if os.path.exists(filepath) else "❌"
        print(f"   {status} {filename:<20} - {description}")

def main():
    parser = argparse.ArgumentParser(
        description="视频监控系统模式切换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python switch_mode.py status          # 查看当前状态
  python switch_mode.py websocket       # 切换到WebSocket模式
  python switch_mode.py webrtc          # 切换到WebRTC模式
  
模式说明:
  WebSocket: 高兼容性，稳定可靠，JPEG传输
  WebRTC:    超低延迟，P2P传输，原生H.264编码
        """
    )
    
    parser.add_argument('mode', 
                       choices=['status', 'websocket', 'webrtc'], 
                       help='操作模式')
    
    args = parser.parse_args()
    
    frontend_path = get_frontend_path()
    
    if args.mode == 'status':
        show_status()
        return
    
    if not check_files_exist(frontend_path):
        sys.exit(1)
    
    current_mode = get_current_mode(frontend_path)
    print(f"🔄 当前模式: {current_mode}")
    
    # 备份当前文件
    if not backup_current_app(frontend_path):
        print("⚠️ 警告: 备份失败，继续操作可能丢失当前配置")
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    # 执行切换
    if args.mode == 'websocket':
        if switch_to_websocket(frontend_path):
            print(f"\n🎯 切换完成!")
            print(f"   启动命令: python websocket_video_server.py")
            print(f"   特点: 高兼容性、稳定可靠、JPEG传输")
    
    elif args.mode == 'webrtc':
        if switch_to_webrtc(frontend_path):
            print(f"\n🎯 切换完成!")
            print(f"   启动命令: python webrtc_server.py")
            print(f"   特点: 超低延迟、P2P传输、原生H.264")
    
    print("\n📝 下一步:")
    print("   1. 重启前端应用 (npm run dev)")
    print("   2. 启动对应的Python服务器")
    print("   3. 在浏览器中测试新模式")

if __name__ == "__main__":
    main() 