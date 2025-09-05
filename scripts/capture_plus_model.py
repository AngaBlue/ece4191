import cv2
import os
import time
from ultralytics import YOLO
# RTSP stream URL
# RTSP_URL = "rtsp://192.168.4.1:554/mjpeg/1"
CAMERA_INDEX = 0  # 0 = default laptop camera
# Load the trained model
model = YOLO(r"model-kctfpck.pt")  # path to your trained weights

# Folder where images will be saved
SAVE_DIR = "images"
os.makedirs(SAVE_DIR, exist_ok=True)

def main():
    # cap = cv2.VideoCapture(RTSP_URL)
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("Error: Unable to open RTSP stream")
        return

    print("Press SPACE to capture an image, ESC to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        results = model.predict(frame)  # or model(frame)
        # The first (and usually only) result in the batch
        r = results[0]

        # Bounding boxes: [x1, y1, x2, y2, confidence, class_id]
        boxes = r.boxes.xyxy.cpu().numpy()      # coordinates
        scores = r.boxes.conf.cpu().numpy()     # confidence
        class_ids = r.boxes.cls.cpu().numpy()   # class indices

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box[:4])
            conf = scores[i]
            cls_id = int(class_ids[i])
            class_names = ["kangaroo", "cockatoo", "tasmanian_devil", "frog", "platypus", "crocodile", "koala"]
            label = f"{class_names[cls_id]}: {conf:.2f}"
            
            # Draw rectangle and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

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
