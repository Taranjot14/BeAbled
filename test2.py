import json
import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp
import time

# Load model
model = tf.keras.models.load_model('gesture_mobilenet_advanced2.h5')

# Load class indices
with open('class_indices.json') as f:
    class_indices = json.load(f)
# Reverse class_indices to get correct index to label map
idx_to_class = {v: k for k, v in class_indices.items()}

# Mediapipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
img_size = (160, 160)

# Caption system variables
current_caption = ""
last_caption_time = 0
caption_timeout = 2.0  # seconds to keep caption visible after no detection
caption_history = []

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(image_rgb)

    # Clear caption if timeout has passed
    if time.time() - last_caption_time > caption_timeout:
        current_caption = ""

    detection_made = False
    current_time = time.time()

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

            img = cv2.resize(cropped_hand, img_size)
            img = img / 255.0
            img = np.expand_dims(img, axis=0)

            preds = model.predict(img)
            class_idx = np.argmax(preds)
            confidence = preds[0][class_idx]

            if class_idx in idx_to_class and confidence > 0.7:  # Confidence threshold
                label = idx_to_class[class_idx]
                detection_made = True
                
                # Update caption only if we have a new detection
                if label != current_caption:
                    current_caption = label
                    caption_history.append(label)
                    if len(caption_history) > 5:  # Keep last 5 captions
                        caption_history.pop(0)
                
                last_caption_time = current_time
                print(f"Detected: {label} | Confidence: {confidence:.2f}")

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    # Draw caption bar at bottom
    caption_bar_height = 80
    cv2.rectangle(frame, (0, frame.shape[0] - caption_bar_height), 
                  (frame.shape[1], frame.shape[0]), (50, 50, 50), -1)
    
    # Display current caption
    if current_caption:
        text_size = cv2.getTextSize(current_caption, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = frame.shape[0] - (caption_bar_height // 2) + (text_size[1] // 2)
        cv2.putText(frame, current_caption, (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    
    history_y = frame.shape[0] - caption_bar_height - 10
    for i, caption in enumerate(reversed(caption_history[-3:])):
        cv2.putText(frame, caption, (20, history_y - (i * 30)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

    cv2.imshow('ASL Detection (MobileNetV2)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()