from flask import Flask, render_template, request, jsonify
import numpy as np
import cv2
import base64
import json
import tensorflow as tf
import mediapipe as mp

app = Flask(__name__)

model = tf.keras.models.load_model('gesture_mobilenet_advanced2.h5')
with open('class_indices.json') as f:
    class_indices = json.load(f)
idx_to_class = {v: k for k, v in class_indices.items()}

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json['image']
    image_data = base64.b64decode(data.split(',')[1])
    frame = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

    img_size = (160, 160)
    label = "-"
    confidence = 0.0

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

            preds = model.predict(img, verbose=0)
            class_idx = np.argmax(preds)
            confidence = float(preds[0][class_idx])

            if class_idx in idx_to_class:
                label = idx_to_class[class_idx]

    return jsonify({'prediction': label, 'confidence': f"{confidence:.2f}"})

if __name__ == "__main__":
    app.run(debug=True)
