import json
import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp
import time

class ASLDetector:
    def __init__(self):
        self.model = tf.keras.models.load_model('gesture_mobilenet_advanced2.h5')
        with open('class_indices.json') as f:
            self.class_indices = json.load(f)
        self.idx_to_class = {v: k for k, v in self.class_indices.items()}
        
        # Mediapipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils
        
        # Caption system
        self.current_caption = ""
        self.last_caption_time = 0
        self.caption_timeout = 2.0
        self.caption_history = []
        self.img_size = (160, 160)
        
    def process_frame(self, frame):
        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(image_rgb)
        
        # Clear caption if timeout has passed
        if time.time() - self.last_caption_time > self.caption_timeout:
            self.current_caption = ""
            
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
                    label = self.idx_to_class[class_idx]
                    
                    if label != self.current_caption:
                        self.current_caption = label
                        self.caption_history.append(label)
                        if len(self.caption_history) > 5:
                            self.caption_history.pop(0)
                    
                    self.last_caption_time = time.time()
                    
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                
        return self.add_caption_bar(frame)
    
    def add_caption_bar(self, frame):
        # Draw caption bar at bottom
        caption_bar_height = 80
        cv2.rectangle(frame, (0, frame.shape[0] - caption_bar_height), 
                     (frame.shape[1], frame.shape[0]), (50, 50, 50), -1)
        
        # Display current caption
        if self.current_caption:
            text_size = cv2.getTextSize(self.current_caption, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            text_x = (frame.shape[1] - text_size[0]) // 2
            text_y = frame.shape[0] - (caption_bar_height // 2) + (text_size[1] // 2)
            cv2.putText(frame, self.current_caption, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Display recent history
        history_y = frame.shape[0] - caption_bar_height - 10
        for i, caption in enumerate(reversed(self.caption_history[-3:])):
            cv2.putText(frame, caption, (20, history_y - (i * 30)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        return frame

def main():
    detector = ASLDetector()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        frame = detector.process_frame(frame)
        cv2.imshow('ASL Detection (MobileNetV2)', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()