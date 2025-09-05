import cv2
import os
import time

# RTSP stream URL
RTSP_URL = "rtsp://192.168.4.1:554/mjpeg/1"

# Folder where images will be saved
SAVE_DIR = "images"
os.makedirs(SAVE_DIR, exist_ok=True)

def main():
    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("Error: Unable to open RTSP stream")
        return

    print("Press SPACE to capture an image, ESC to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Show the frame
        cv2.imshow("RTSP Stream", frame)

        # Wait for a key press for 1ms
        key = cv2.waitKey(1) & 0xFF

        # Space bar pressed
        if key == 32:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(SAVE_DIR, f"frame_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")

        # ESC pressed
        elif key == 27:
            print("Exiting...")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
