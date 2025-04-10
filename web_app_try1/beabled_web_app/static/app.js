// App State
let aslEnabled = false;
let callActive = false;
let cameraEnabled = true;
let micEnabled = true;
let stream = null;
let predictionInterval = null;
let currentRoom = null;
let socket = null;

// DOM Elements
const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const joinBtn = document.getElementById("joinBtn");
const aslBtn = document.getElementById("aslBtn");
const micBtn = document.getElementById("micBtn");
const camBtn = document.getElementById("camBtn");
const roomBtn = document.getElementById("roomBtn");
const captionDisplay = document.getElementById("captionDisplay");
const localCameraOff = document.getElementById("localCameraOff");
const remoteCameraOff = document.getElementById("remoteCameraOff");
const roomModal = new bootstrap.Modal('#roomModal');
const createRoomBtn = document.getElementById("createRoomBtn");
const joinRoomBtn = document.getElementById("joinRoomBtn");
const roomIdInput = document.getElementById("roomIdInput");
const roomLinkContainer = document.getElementById("roomLinkContainer");
const roomLink = document.getElementById("roomLink");
const copyLinkBtn = document.getElementById("copyLinkBtn");
const toastContainer = document.getElementById("toastContainer");

// Initialize Socket.IO
function initSocket() {
    socket = io();
    
    socket.on('connect', () => {
        showToast('Connected to server', 'success');
    });
    
    socket.on('room_created', (data) => {
        roomLink.value = `${window.location.origin}?room=${data.room_id}`;
        roomLinkContainer.classList.remove('d-none');
        currentRoom = data.room_id;
        showToast('Room created! Share the link.', 'success');
    });
    
    socket.on('participant_joined', (data) => {
        showToast('New participant joined', 'info');
        // Here you would handle peer connection setup
    });
    
    socket.on('error', (data) => {
        showToast(data.message, 'danger');
    });
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    setupEventListeners();
    checkForRoomInURL();
});

function setupEventListeners() {
    // Call Controls
    joinBtn.addEventListener('click', toggleCall);
    aslBtn.addEventListener('click', toggleASL);
    micBtn.addEventListener('click', toggleMic);
    camBtn.addEventListener('click', toggleCamera);
    roomBtn.addEventListener('click', () => roomModal.show());
    
    // Room Controls
    createRoomBtn.addEventListener('click', createRoom);
    joinRoomBtn.addEventListener('click', joinRoom);
    copyLinkBtn.addEventListener('click', copyRoomLink);
}

// Room Functions
function createRoom() {
    socket.emit('create_room');
}

function joinRoom() {
    const roomId = roomIdInput.value.trim();
    if (roomId) {
        socket.emit('join_room', { room_id: roomId });
        currentRoom = roomId;
        roomModal.hide();
    } else {
        showToast('Please enter a room ID', 'warning');
    }
}

function copyRoomLink() {
    roomLink.select();
    document.execCommand('copy');
    showToast('Link copied to clipboard!', 'success');
}

function checkForRoomInURL() {
    const params = new URLSearchParams(window.location.search);
    const roomId = params.get('room');
    if (roomId) {
        roomIdInput.value = roomId;
        roomModal.show();
    }
}

// Call Functions
async function toggleCall() {
    if (!callActive) {
        await startCall();
    } else {
        endCall();
    }
    updateCallButton();
}

async function startCall() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: cameraEnabled,
            audio: micEnabled
        });
        
        localVideo.srcObject = stream;
        remoteVideo.srcObject = stream; // For demo, replace with actual remote stream
        
        callActive = true;
        updateCameraOffDisplays();
        
        localVideo.onloadeddata = () => {
            if (aslEnabled) startASLPrediction();
        };
        
        if (currentRoom) socket.emit('join_room', { room_id: currentRoom });
        
        showToast('Call started', 'success');
    } catch (error) {
        showToast(`Error: ${error.message}`, 'danger');
    }
}

function endCall() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        localVideo.srcObject = null;
        remoteVideo.srcObject = null;
    }
    
    stopASLPrediction();
    
    if (currentRoom) {
        socket.emit('leave_room', { room_id: currentRoom });
    }
    
    callActive = false;
    updateCameraOffDisplays();
    showToast('Call ended', 'info');
}

// ASL Functions
function toggleASL() {
    console.log("ASL button clicked. Current state:", aslEnabled);
    aslEnabled = !aslEnabled;
    aslBtn.classList.toggle("active", aslEnabled);
    
    if (aslEnabled) {
        if (!cameraEnabled) {
            showToast("Please enable camera for ASL detection", "warning");
            aslEnabled = false;
            aslBtn.classList.remove("active");
            return;
        }
        startASLPrediction();
    } else {
        stopASLPrediction();
    }
}

function startASLPrediction() {
    console.log("Starting ASL prediction");
    
    if (predictionInterval) clearInterval(predictionInterval);
    
    captionDisplay.style.display = "block";
    captionDisplay.textContent = "Detecting gestures...";
    
    predictionInterval = setInterval(async () => {
        if (!callActive || !aslEnabled || !cameraEnabled) return;
        
        try {
            const canvas = document.createElement('canvas');
            canvas.width = localVideo.videoWidth;
            canvas.height = localVideo.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(localVideo, 0, 0, canvas.width, canvas.height);
            
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: canvas.toDataURL('image/jpeg') })
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                const displayText = data.prediction === '-' ? 
                    'No gesture detected' : 
                    `✋ ${data.prediction} (${data.confidence})`;
                captionDisplay.textContent = displayText;
                speakText(data.prediction); // 🔊 Voice here
            } else {
                captionDisplay.textContent = "Detection error";
            }
        } catch (error) {
            console.error("ASL processing error:", error);
            captionDisplay.textContent = "Processing error";
        }
    }, 1000);
}

function stopASLPrediction() {
    console.log("Stopping ASL prediction");
    if (predictionInterval) {
        clearInterval(predictionInterval);
        predictionInterval = null;
    }
    captionDisplay.style.display = "none";
    captionDisplay.textContent = "";
}

// 🔊 Speak captions
let lastSpokenGesture = null;
let noGestureCount = 0;

function speakText(text) {
    if (!text || text === '-') {
        noGestureCount++;
        if (noGestureCount > 2) {
            lastSpokenGesture = null; // Reset after continuous no gestures
        }
        return;
    }
    
    // Only speak if different from last gesture
    if (text !== lastSpokenGesture) {
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'en-US';
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
        lastSpokenGesture = text;
        noGestureCount = 0;
    }
}

// UI Helpers
function updateCallButton() {
    if (callActive) {
        joinBtn.innerHTML = '<i class="bi bi-telephone-x-fill me-2"></i>Leave Call';
        joinBtn.classList.remove('btn-primary');
        joinBtn.classList.add('btn-danger');
    } else {
        joinBtn.innerHTML = '<i class="bi bi-camera-video-off-fill me-2"></i>Start Call';
        joinBtn.classList.remove('btn-danger');
        joinBtn.classList.add('btn-primary');
    }
}

function updateCameraOffDisplays() {
    const showLocalOff = !callActive || !cameraEnabled;
    const showRemoteOff = !callActive;
    
    localCameraOff.style.display = showLocalOff ? 'flex' : 'none';
    remoteCameraOff.style.display = showRemoteOff ? 'flex' : 'none';
}
function toggleMic() {
    micEnabled = !micEnabled;

    // Toggle classes for visual feedback
    micBtn.classList.toggle('active', micEnabled);
    micBtn.classList.toggle('disabled', !micEnabled);

    // Swap icon between mic and mic-mute
    micBtn.innerHTML = micEnabled
        ? '<i class="bi bi-mic-fill"></i>'
        : '<i class="bi bi-mic-mute-fill"></i>';

    // Actually toggle audio track
    if (stream && stream.getAudioTracks().length > 0) {
        stream.getAudioTracks()[0].enabled = micEnabled;
    }

    showToast(`Microphone ${micEnabled ? 'enabled' : 'muted'}`, 'info');
}


function toggleCamera() {
    cameraEnabled = !cameraEnabled;
    camBtn.classList.toggle('active', cameraEnabled);
    camBtn.classList.toggle('disabled', !cameraEnabled);
    if (stream) stream.getVideoTracks()[0].enabled = cameraEnabled;
    updateCameraOffDisplays();
    if (!cameraEnabled && aslEnabled) toggleASL();
    showToast(`Camera ${cameraEnabled ? 'enabled' : 'disabled'}`, 'info');
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type}`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}


// Add to your existing JS
let handRaised = false;
const raiseHandBtn = document.getElementById('raiseHandBtn');

raiseHandBtn.addEventListener('click', toggleRaiseHand);

function toggleRaiseHand() {
    handRaised = !handRaised;
    raiseHandBtn.classList.toggle('active', handRaised);
    
    // Visual indicator
    const indicator = document.createElement('div');
    indicator.className = 'raise-hand-indicator';
    indicator.innerHTML = '<i class="bi bi-hand-raised-fill"></i> Hand Raised';
    
    if (handRaised) {
        document.body.appendChild(indicator);
        socket.emit('raise_hand', { room: currentRoom, state: true });
    } else {
        document.querySelector('.raise-hand-indicator')?.remove();
        socket.emit('raise_hand', { room: currentRoom, state: false });
    }
}

// Socket.IO handler
socket.on('hand_raised', (data) => {
    showToast(`${data.userId} ${data.state ? 'raised' : 'lowered'} their hand`, 'info');
});

// Add to your DOM elements
const chatBtn = document.getElementById("chatBtn");
const chatModal = new bootstrap.Modal('#chatModal');

// Add to your setupEventListeners()
chatBtn.addEventListener('click', () => {
    chatModal.show();
    unreadCount = 0;
    document.getElementById('unreadCount').textContent = '0';
});

// Update your chat message handler
socket.on('chat_message', (data) => {
    addMessage(data.message, false, data.sender);
    if (!chatModal._element.classList.contains('show')) {
        unreadCount++;
        document.getElementById('unreadCount').textContent = unreadCount;
        // Add visual notification dot
        chatBtn.innerHTML = '<i class="bi bi-chat-left-text-fill"></i><span class="chat-notification"></span>';
        document.querySelector('.chat-notification').style.display = 'block';
    }
});

// Update your sendMessage function
function sendMessage() {
    const message = chatInput.value.trim();
    if (message && currentRoom) {
        socket.emit('chat_message', {
            room: currentRoom,
            message: message,
            sender: 'You'
        });
        addMessage(message, true);
        chatInput.value = '';
    }
}

// Update your addMessage function
function addMessage(text, isLocal, sender = 'Participant') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isLocal ? 'local' : 'remote'}`;
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// Recording functionality
let mediaRecorder;
let recordedChunks = [];
const recordBtn = document.getElementById('recordBtn');

recordBtn.addEventListener('click', toggleRecording);

async function toggleRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    try {
        recordedChunks = [];
        const stream = localVideo.srcObject;
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) recordedChunks.push(e.data);
        };
        
        mediaRecorder.onstop = saveRecording;
        mediaRecorder.start(100); // Collect data every 100ms
        recordBtn.classList.add('recording');
        showToast('Recording started', 'info');
    } catch (error) {
        showToast(`Recording error: ${error}`, 'danger');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        recordBtn.classList.remove('recording');
        showToast('Recording stopped', 'info');
    }
}

function saveRecording() {
    const blob = new Blob(recordedChunks, { type: 'video/webm' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `beabled-recording-${new Date().toISOString()}.webm`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 100);
}

// CSS for recording state


// Cleanup
window.addEventListener('beforeunload', () => {
    if (callActive) endCall();
});
