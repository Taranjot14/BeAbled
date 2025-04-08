# ✋ BeAbled – Where Hands Speak Louder

BeAbled is an accessibility-focused video communication web app designed to **bridge communication gaps** for the Deaf and Hard of Hearing community. It integrates real-time **ASL gesture detection** with **speech synthesis**, video calling, and room-based interaction — all wrapped in a sleek, modern UI.

---

## 🌟 Features

- 🎥 **Video Calling** with remote and local stream views  
- ✋ **ASL Gesture Detection** using TensorFlow + MediaPipe  
- 🔊 **Caption-to-Voice** with built-in text-to-speech  
- 🧠 **Real-time prediction** with confidence overlay  
- 🏠 **Custom Room System** for private communication  
- 🎨 **Modern, Animated UI** built with Bootstrap & CSS3  
- 🌐 **Socket.IO powered** for real-time sync

---

## 🧠 Tech Stack

- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript  
- **Backend**: Python, Flask, Flask-SocketIO  
- **AI/ML**: TensorFlow, MediaPipe, MobileNetV2  
- **TTS**: Web Speech API (Client-side)  
- **Live Video**: WebRTC via `getUserMedia()`  
- **Deployment**: Localhost or cloud-ready

---

## 🖼️ UI Preview

![BeAbled Preview](docs/ui-preview.png)

---

## ⚙️ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/your-username/beabled.git
cd beabled
```

### 2. Set up the virtual environment
- Install Requirements

### 3. Run the Flask server
```bash
python app.py
```

### 4. Open your browser
```
http://localhost:5500
```

---

## 🤖 Model & Data

- **Model**: `gesture_mobilenet_advanced2.h5`  
- **Labels**: `class_indices.json`  
- Based on custom ASL training dataset (MobileNet backbone)

---

## 📁 Project Structure

```
├── app.py
├── static/
│   └── app.js
├── templates/
│   └── index.html
├── gesture_mobilenet_advanced2.h5
├── class_indices.json

```

---

## 📢 Voice Integration

Uses the browser's **Web Speech API** to speak out ASL predictions as they are detected. Requires mic & speaker access.

---

## 💜 UI Themes

- Dark purple navbar with animated gradient logo
- Soft lavender body background
- Live caption display with subtle animations

---

## 📌 TODO / Future Work

- Add **multilingual TTS** support  
- Enable **voice-to-ASL recognition**  
- Implement **user auth** and persistent rooms  
- Extend gesture set (fingerspelling A–Z, more words)

---

