import sys
import cv2
import numpy as np
import json
import tensorflow as tf
import mediapipe as mp
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFrame)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter


class ASLDetector:
    def __init__(self):
        self.model = tf.keras.models.load_model('gesture_mobilenet_advanced2.h5')
        with open('class_indices.json') as f:
            self.class_indices = json.load(f)
        self.idx_to_class = {v: k for k, v in self.class_indices.items()}
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils
        self.img_size = (160, 160)
        self.current_gesture = ""
        
    def process_frame(self, frame):
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(image_rgb)
        
        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                h, w, _ = frame.shape
                x_min = int(min([lm.x for lm in hand_landmarks.landmark]) * w) - 20
                y_min = int(min([lm.y for lm in hand_landmarks.landmark]) * h) - 20
                x_max = int(max([lm.x for lm in hand_landmarks.landmark]) * w) + 20
                y_max = int(max([lm.y for lm in hand_landmarks.landmark]) * h) + 20

                x_min, y_min = max(x_min, 0), max(y_min, 0)
                x_max, y_max = min(x_max, w), min(y_max, h)

                cropped_hand = frame[y_min:y_max, x_min:x_max]
                if cropped_hand.size == 0:
                    continue

                img = cv2.resize(cropped_hand, self.img_size)
                img = img / 255.0
                img = np.expand_dims(img, axis=0)

                preds = self.model.predict(img, verbose=0)
                class_idx = np.argmax(preds)
                confidence = preds[0][class_idx]

                if class_idx in self.idx_to_class and confidence > 0.7:
                    self.current_gesture = self.idx_to_class[class_idx]
                else:
                    self.current_gesture = ""
                
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        return frame

class VideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QImage()
        self.setMinimumSize(640, 480)
        
    def set_image(self, image):
        self.image = image
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.image.isNull():
            painter.drawImage(self.rect(), self.image)

class VideoCallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASL Video Call")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize ASL detector
        self.asl_detector = ASLDetector()
        self.current_gesture = ""
        
        # Create main widgets
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layouts
        self.main_layout = QHBoxLayout()
        self.video_layout = QVBoxLayout()
        self.controls_layout = QVBoxLayout()
        
        # Video displays
        self.local_video = VideoWidget()
        self.remote_video = VideoWidget()
        
        # Gesture display
        self.gesture_label = QLabel("No gesture detected")
        self.gesture_label.setAlignment(Qt.AlignCenter)
        self.gesture_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 10px;
            }
        """)
        
        # Controls
        self.start_btn = QPushButton("Start Call")
        self.end_btn = QPushButton("End Call")
        self.enable_asl_btn = QPushButton("Enable ASL Detection")
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        self.start_btn.setStyleSheet(button_style)
        self.end_btn.setStyleSheet(button_style)
        self.enable_asl_btn.setStyleSheet(button_style)
        
        # Add widgets to layouts
        self.video_layout.addWidget(QLabel("Remote Video"))
        self.video_layout.addWidget(self.remote_video)
        self.video_layout.addWidget(QLabel("Local Video"))
        self.video_layout.addWidget(self.local_video)
        self.video_layout.addWidget(self.gesture_label)
        
        self.controls_layout.addWidget(self.start_btn)
        self.controls_layout.addWidget(self.end_btn)
        self.controls_layout.addWidget(self.enable_asl_btn)
        self.controls_layout.addStretch()
        
        self.main_layout.addLayout(self.video_layout, 4)
        self.main_layout.addLayout(self.controls_layout, 1)
        
        self.central_widget.setLayout(self.main_layout)
        
        # Video capture
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # Connect signals
        self.start_btn.clicked.connect(self.start_call)
        self.end_btn.clicked.connect(self.end_call)
        self.enable_asl_btn.clicked.connect(self.toggle_asl)
        
        # State
        self.asl_enabled = False
        self.call_active = False
        
    def toggle_asl(self):
        self.asl_enabled = not self.asl_enabled
        if self.asl_enabled:
            self.enable_asl_btn.setText("Disable ASL Detection")
            self.enable_asl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self.enable_asl_btn.setText("Enable ASL Detection")
            self.enable_asl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            self.gesture_label.setText("ASL detection disabled")
    
    def start_call(self):
        self.call_active = True
        self.timer.start(30)  # ~30fps
        self.start_btn.setEnabled(False)
        self.end_btn.setEnabled(True)
        
    def end_call(self):
        self.call_active = False
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.end_btn.setEnabled(False)
        
    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            # Process frame for ASL if enabled
            if self.asl_enabled:
                processed_frame = self.asl_detector.process_frame(frame)
                self.current_gesture = self.asl_detector.current_gesture
                self.gesture_label.setText(f"Detected: {self.current_gesture}" if self.current_gesture else "No gesture detected")
            else:
                processed_frame = frame
            
            # Convert to QImage and display
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.local_video.set_image(qt_image)
            
            # For demo purposes, just mirror the local video as remote
            # In a real app, this would be the actual remote stream
            self.remote_video.set_image(qt_image)
    
    def closeEvent(self, event):
        self.capture.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoCallApp()
    window.show()
    sys.exit(app.exec_())