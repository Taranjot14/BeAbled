import sys
import cv2
import numpy as np
import json
import tensorflow as tf
import mediapipe as mp
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QIcon, QFont, QColor

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
            # Scale image to fit widget while maintaining aspect ratio
            img_ratio = self.image.width() / self.image.height()
            widget_ratio = self.width() / self.height()
            
            if widget_ratio > img_ratio:
                target_width = int(self.height() * img_ratio)
                target_height = self.height()
                x = (self.width() - target_width) // 2
                y = 0
            else:
                target_width = self.width()
                target_height = int(self.width() / img_ratio)
                x = 0
                y = (self.height() - target_height) // 2
                
            painter.drawImage(x, y, self.image.scaled(
                target_width, target_height, 
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

class BeAbledApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BeAbled Video Call")
        self.setGeometry(100, 100, 1200, 800)
        
        # App state
        self.asl_enabled = False
        self.call_active = False
        self.current_gesture = ""
        
        # Initialize UI
        self.init_ui()
        
        # Initialize ASL detector
        self.init_asl_detector()
        
        # Initialize video capture
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
    def init_ui(self):
        """Initialize the Google Meet-style interface"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout - vertical stack
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.central_widget.setLayout(self.main_layout)
        
        # Video area - takes most of the space
        self.video_area = QWidget()
        self.video_area.setStyleSheet("background-color: #202124;")
        self.video_layout = QHBoxLayout(self.video_area)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Remote video (main display)
        self.remote_video = VideoWidget()
        self.remote_video.setStyleSheet("background-color: #202124;")
        
        # Local video (thumbnail)
        self.local_video = VideoWidget()
        self.local_video.setFixedSize(240, 135)  # 16:9 aspect ratio
        self.local_video.setStyleSheet("""
            background-color: #3c4043;
            border-radius: 8px;
            border: 2px solid #4285F4;
        """)
        
        # Add videos to layout
        self.video_layout.addWidget(self.remote_video)
        
        # Bottom control bar (Google Meet style)
        self.control_bar = QFrame()
        self.control_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #dadce0;
                padding: 12px 0;
            }
        """)
        
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(20, 0, 20, 0)
        
        # ASL Toggle Button
        self.asl_btn = QPushButton()
        self.asl_btn.setIcon(self.create_hand_icon())
        self.asl_btn.setToolTip("Toggle ASL Detection")
        self.asl_btn.setCheckable(True)
        self.asl_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f1f3f4;
            }
            QPushButton:checked {
                background-color: #e8f0fe;
            }
        """)
        
        # Standard call controls
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setCheckable(True)
        self.mic_btn.setChecked(True)
        
        self.cam_btn = QPushButton("📷")
        self.cam_btn.setCheckable(True)
        self.cam_btn.setChecked(True)
        
        # Join/Leave button
        self.call_btn = QPushButton("Join")
        self.call_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        
        # ASL Translation Panel (speech bubble)
        self.asl_panel = QLabel("ASL detection ready")
        self.asl_panel.setAlignment(Qt.AlignCenter)
        self.asl_panel.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 16px;
                padding: 8px 16px;
                border: 1px solid #dadce0;
                color: #3c4043;
                font-size: 14px;
                min-width: 200px;
            }
        """)
        self.asl_panel.setVisible(False)
        
        # Add controls to layout
        control_layout.addWidget(self.asl_btn)
        control_layout.addWidget(self.mic_btn)
        control_layout.addWidget(self.cam_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.call_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.asl_panel)
        
        self.control_bar.setLayout(control_layout)
        
        # Compose main layout
        self.main_layout.addWidget(self.video_area, 1)
        self.main_layout.addWidget(self.control_bar)
        
        # Local video overlay (bottom-right corner)
        self.local_video_overlay = QWidget(self.remote_video)
        self.local_video_overlay.setGeometry(
            self.remote_video.width() - 250, 
            self.remote_video.height() - 155, 
            240, 135
        )
        overlay_layout = QVBoxLayout(self.local_video_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addWidget(self.local_video)
        
        # Connect signals
        self.asl_btn.toggled.connect(self.toggle_asl)
        self.call_btn.clicked.connect(self.toggle_call)
        self.mic_btn.toggled.connect(lambda: self.update_button_style(self.mic_btn))
        self.cam_btn.toggled.connect(lambda: self.update_button_style(self.cam_btn))
        
    def create_hand_icon(self):
        """Create a simple hand icon for the ASL button"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw hand shape
        painter.setBrush(QColor(95, 99, 104))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(6, 6, 12, 12)  # Palm
        # Fingers
        painter.drawEllipse(4, 2, 6, 6)
        painter.drawEllipse(10, 2, 6, 6)
        painter.drawEllipse(16, 4, 6, 6)
        
        painter.end()
        return QIcon(pixmap)
    
    def update_button_style(self, button):
        """Update style when buttons are toggled"""
        if button.isChecked():
            button.setStyleSheet("background-color: transparent;")
        else:
            button.setStyleSheet("background-color: #f1f3f4; color: #d93025;")
    
    def init_asl_detector(self):
        """Initialize the ASL detection model"""
        try:
            self.model = tf.keras.models.load_model('gesture_mobilenet_advanced2.h5')
            with open('class_indices.json') as f:
                self.class_indices = json.load(f)
            self.idx_to_class = {v: k for k, v in self.class_indices.items()}
            
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils
            self.img_size = (160, 160)
        except Exception as e:
            print(f"Error loading ASL model: {e}")
            self.asl_btn.setEnabled(False)
    
    def toggle_asl(self, checked):
        """Toggle ASL detection on/off"""
        self.asl_enabled = checked
        self.asl_panel.setVisible(checked)
        if not checked:
            self.asl_panel.setText("ASL detection off")
    
    def toggle_call(self):
        """Start/end the video call"""
        if self.call_active:
            self.timer.stop()
            self.call_btn.setText("Join")
            self.asl_panel.setText("Call ended")
            self.call_active = False
        else:
            self.timer.start(30)  # ~30fps
            self.call_btn.setText("Leave")
            self.call_active = True
    
    def update_frame(self):
        """Process each video frame"""
        ret, frame = self.capture.read()
        if not ret:
            return
            
        # Mirror the frame for more natural view
        frame = cv2.flip(frame, 1)
        
        # Process ASL if enabled
        if self.asl_enabled:
            frame = self.process_asl(frame)
        
        # Convert to QImage
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Update displays
        self.local_video.set_image(qt_image)
        
        # For demo purposes, mirror local video as remote
        self.remote_video.set_image(qt_image)
        
        # Update local video overlay position
        self.local_video_overlay.setGeometry(
            self.remote_video.width() - 250, 
            self.remote_video.height() - 155, 
            240, 135
        )
    
    def process_asl(self, frame):
        """Process frame for ASL detection"""
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get hand bounding box
                h, w, _ = frame.shape
                x_min = int(min([lm.x for lm in hand_landmarks.landmark]) * w) - 20
                y_min = int(min([lm.y for lm in hand_landmarks.landmark]) * h) - 20
                x_max = int(max([lm.x for lm in hand_landmarks.landmark]) * w) + 20
                y_max = int(max([lm.y for lm in hand_landmarks.landmark]) * h) + 20
                
                # Ensure coordinates are within frame bounds
                x_min, y_min = max(x_min, 0), max(y_min, 0)
                x_max, y_max = min(x_max, w), min(y_max, h)
                
                # Crop and process hand region
                cropped_hand = frame[y_min:y_max, x_min:x_max]
                if cropped_hand.size == 0:
                    continue
                
                # Prepare image for model
                img = cv2.resize(cropped_hand, self.img_size)
                img = img / 255.0
                img = np.expand_dims(img, axis=0)
                
                # Predict gesture
                preds = self.model.predict(img, verbose=0)
                class_idx = np.argmax(preds)
                confidence = preds[0][class_idx]
                
                if confidence > 0.7 and class_idx in self.idx_to_class:
                    self.current_gesture = self.idx_to_class[class_idx]
                    self.asl_panel.setText(f"✋ {self.current_gesture} ({confidence:.1%})")
                
                # Draw landmarks and bounding box
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.mp_draw.DrawingSpec(
                        color=(121, 44, 250), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_draw.DrawingSpec(
                        color=(164, 119, 248), thickness=2, circle_radius=2)
                )
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        return frame
    
    def closeEvent(self, event):
        """Clean up resources when closing"""
        self.capture.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Google-style font
    font = QFont("Segoe UI", 10)  # Fallback to Arial if Google Sans not available
    app.setFont(font)
    
    window = BeAbledApp()
    window.show()
    sys.exit(app.exec_())