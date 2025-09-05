import sys
import cv2
import time
import numpy as np
from ultralytics import YOLO
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QGroupBox
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import QTimer, Qt
CAMERA_INDEX = 0
model = YOLO(r"model-kctfpck.pt") 

class PayloadGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Payload Control")
        self.resize(1000, 600)

        #self.RTSP_Stream = "rtsp://192.168.4.1:554/mjpeg/1"
        #self.stream_url = "rtsp://192.168.4.1:554/stream"

        # Layouts
        main_layout = QHBoxLayout(self)

        # Left: Video feed
        self.video_label = QLabel("Video Stream")
        self.video_label.setFixedSize(640, 480)
        main_layout.addWidget(self.video_label)

        # Right: Controls + Info
        right_layout = QVBoxLayout()

        # Camera orientation info - generic text display for now
        self.orientation_label = QLabel("Camera Orientation: H: 0 V: 0")
        right_layout.addWidget(self.orientation_label)

        # Control buttons - Generic buttons for now -  no function
        control_box = QGroupBox("Mount Control")
        control_layout = QGridLayout()
        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.left_btn = QPushButton("←")
        self.right_btn = QPushButton("→")
        control_layout.addWidget(self.up_btn, 0, 1)
        control_layout.addWidget(self.left_btn, 1, 0)
        control_layout.addWidget(self.right_btn, 1, 2)
        control_layout.addWidget(self.down_btn, 2, 1)
        control_box.setLayout(control_layout)
        right_layout.addWidget(control_box)

        # Audio detection
        self.audio_label = QLabel("Audio Detected: None")
        right_layout.addWidget(self.audio_label)

        # Visual detection
        self.Visual_label = QLabel("Visual Detected: None")
        right_layout.addWidget(self.Visual_label)
        # System info
        self.info_label = QLabel("Frame Rate: -- FPS | Delay: -- ms")
        right_layout.addWidget(self.info_label)

        # Save frame button
        self.save_btn = QPushButton("Save Frame")
        right_layout.addWidget(self.save_btn)

        main_layout.addLayout(right_layout)

        # Video capture
        #self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Windows fix
        # self.cap = cv2.VideoCapture(self.RTSP_Stream)
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.last_time = time.time()

        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.frame = None
        self.save_btn.clicked.connect(self.save_frame)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame = frame
        fps = 1 / (time.time() - self.last_time)
        self.last_time = time.time()

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
            if conf > 0.5:
                cls_id = int(class_ids[i])
                class_names = ["kangaroo", "cockatoo", "tasmanian_devil", "frog", "platypus", "crocodile", "koala"]
                label = f"{class_names[cls_id]}: {conf:.2f}"
                # # Visual detection
                # self.Visual_label = QLabel(f"Visual Detected: {label}")
                # self.right_layout.addWidget(self.Visual_label)
                # Draw rectangle and label
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

        # Example detections (replace with your ML model)
        #detections = [
        #    {"label": "Frog", "conf": 40, "box": (50, 200, 150, 300)},
        #    {"label": "Koala", "conf": 70, "box": (300, 100, 450, 250)}
        #]

        # Draw bounding boxes
        #for det in detections:
        #    x1, y1, x2, y2 = det["box"]
        #    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
        #    cv2.putText(frame, f"{det['label']} --- {det['conf']}%", 
        #                (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 
        #                0.6, (0,0,255), 2)

        # Convert frame to Qt format
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

        # Update info
        self.info_label.setText(f"Frame Rate: {fps:.1f} FPS | Delay: {int(1000/fps)} ms")

    def save_frame(self):
        if self.frame is not None:
            cv2.imwrite("saved_frame.jpg", self.frame)
            print("Frame saved!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PayloadGUI()
    gui.show()
    sys.exit(app.exec_())

