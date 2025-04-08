import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import numpy as np
import cv2
import base64
import json
import tensorflow as tf
import mediapipe as mp
import secrets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Load ASL model
try:
    model = tf.keras.models.load_model('gesture_mobilenet_advanced2.h5')
    with open('class_indices.json') as f:
        class_indices = json.load(f)
    idx_to_class = {v: k for k, v in class_indices.items()}
    logger.info("ASL model loaded successfully")
except Exception as e:
    logger.error(f"Error loading ASL model: {e}")
    raise

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,  # critical for per-frame images
    max_num_hands=1,
    min_detection_confidence=0.5,  # slightly lower to allow more detections
    min_tracking_confidence=0.5
)

# Room management
active_rooms = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json['image']
        image_data = base64.b64decode(data.split(',')[1])
        frame = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        # ASL Detection
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        label = "-"
        confidence = 0.0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                h, w, _ = frame.shape
                x_min = int(min([lm.x for lm in hand_landmarks.landmark]) * w)
                y_min = int(min([lm.y for lm in hand_landmarks.landmark]) * h)
                x_max = int(max([lm.x for lm in hand_landmarks.landmark]) * w)
                y_max = int(max([lm.y for lm in hand_landmarks.landmark]) * h)

                # Add 20% padding
                x_min = max(0, x_min - int(0.2 * (x_max - x_min)))
                y_min = max(0, y_min - int(0.2 * (y_max - y_min)))
                x_max = min(w, x_max + int(0.2 * (x_max - x_min)))
                y_max = min(h, y_max + int(0.2 * (y_max - y_min)))

                cropped_hand = frame[y_min:y_max, x_min:x_max]
                if cropped_hand.size == 0:
                    logger.warning("Detected hand had invalid crop region.")
                    continue

                img = cv2.resize(cropped_hand, (160, 160))
                img = img / 255.0
                preds = model.predict(np.expand_dims(img, axis=0), verbose=0)
                class_idx = np.argmax(preds)
                confidence = float(preds[0][class_idx])

                if confidence > 0.7 and class_idx in idx_to_class:
                    label = idx_to_class[class_idx]

        else:
            logger.warning("No hand landmarks detected.")

        return jsonify({
            'prediction': label,
            'confidence': f"{confidence:.2f}",
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('create_room')
def handle_create_room():
    room_id = secrets.token_urlsafe(6)
    active_rooms[room_id] = {'participants': [request.sid]}
    join_room(room_id)
    emit('room_created', {'room_id': room_id})
    logger.info(f"Room created: {room_id}")

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    if room_id in active_rooms:
        join_room(room_id)
        active_rooms[room_id]['participants'].append(request.sid)
        emit('participant_joined', {'sid': request.sid}, room=room_id)
        logger.info(f"Client {request.sid} joined room {room_id}")
    else:
        emit('error', {'message': 'Room not found'})
        logger.warning(f"Attempt to join non-existent room: {room_id}")

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id')
    if room_id in active_rooms:
        leave_room(room_id)
        active_rooms[room_id]['participants'].remove(request.sid)
        if not active_rooms[room_id]['participants']:
            del active_rooms[room_id]
        logger.info(f"Client {request.sid} left room {room_id}")


# Add these Socket.IO handlers
@socketio.on('raise_hand')
def handle_raise_hand(data):
    room = data['room']
    emit('hand_raised', {
        'userId': request.sid,
        'state': data['state']
    }, room=room)

@socketio.on('chat_message')
def handle_chat_message(data):
    room = data['room']
    emit('chat_message', {
        'message': data['message'],
        'sender': data.get('sender', 'Anonymous')
    }, room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
