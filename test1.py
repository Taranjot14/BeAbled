import json
import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp

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

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(image_rgb)

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

            if class_idx in idx_to_class:
                label = idx_to_class[class_idx]
                cv2.putText(frame, f"{label} ({confidence:.2f})",
                            (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 255, 0), 2)
                print(f"Detected: {label} | Confidence: {confidence:.2f}")

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    cv2.imshow('ASL Detection (MobileNetV2)', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
