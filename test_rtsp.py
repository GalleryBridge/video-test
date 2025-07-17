import cv2
from config import RTSP_URL

def test_rtsp_connection():
    print(f"测试RTSP连接: {RTSP_URL}")
    
    try:
        cap = cv2.VideoCapture(RTSP_URL)
        
        if cap.isOpened():
            print("✅ RTSP连接成功")
            
            # 尝试读取一帧
            ret, frame = cap.read()
            if ret:
                print(f"✅ 成功读取视频帧，尺寸: {frame.shape}")
                return True
            else:
                print("❌ 无法读取视频帧")
                return False
        else:
            print("❌ 无法连接RTSP流")
            return False
            
    except Exception as e:
        print(f"❌ RTSP连接出错: {e}")
        return False
    finally:
        if 'cap' in locals():
            cap.release()

if __name__ == "__main__":
    test_rtsp_connection() 