// src/VideoCall.tsx
import React, { useEffect, useRef, useState } from 'react';
import './VideoCall.css'; // optional: for styling

// Placeholder function to simulate ASL detection
function runASLDetection(frame: HTMLCanvasElement) {
  // Here you would extract the frame, process it with your model,
  // and overlay results on the canvas or update state.
  console.log('Running ASL detection on frame...');
  // For example, you might draw some text on the canvas:
  const ctx = frame.getContext('2d');
  if (ctx) {
    ctx.font = '24px Arial';
    ctx.fillStyle = 'red';
    ctx.fillText('ASL Detected', 10, 30);
  }
}

const VideoCall: React.FC = () => {
  // Determine role via URL parameter: ?caller=1 means caller, otherwise callee.
  const params = new URLSearchParams(window.location.search);
  const isCaller = params.get('caller') === '1';

  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null); // Canvas for ASL overlay
  const [peerConnection, setPeerConnection] = useState<RTCPeerConnection | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const [aslActive, setAslActive] = useState(false); // Toggle for ASL detection

  useEffect(() => {
    // 1. Create RTCPeerConnection with a public STUN server.
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    });
    setPeerConnection(pc);

    // 2. Handle remote stream.
    pc.ontrack = (event) => {
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = event.streams[0];
      }
    };

    // 3. Connect to the WebSocket signaling server.
    ws.current = new WebSocket('ws://localhost:8080');

    ws.current.onmessage = async (event) => {
      if (typeof event.data !== 'string') {
        console.warn('Received non-text message, ignoring:', event.data);
        return;
      }
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.error('Failed to parse JSON:', event.data, e);
        return;
      }
      if (data.offer) {
        console.log('Got offer:', data.offer);
        if (pc.signalingState !== 'stable') {
          console.warn('Received offer while not stable.');
          return;
        }
        await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        ws.current?.send(JSON.stringify({ answer }));
      } else if (data.answer) {
        console.log('Got answer:', data.answer);
        await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
      } else if (data.ice) {
        try {
          await pc.addIceCandidate(data.ice);
        } catch (err) {
          console.error('Error adding ICE candidate', err);
        }
      }
    };

    // 4. Send ICE candidates as they are gathered.
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        ws.current?.send(JSON.stringify({ ice: event.candidate }));
      }
    };

    // 5. Get the local media stream (video only) and add tracks to the RTCPeerConnection.
    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
        stream.getTracks().forEach((track) => {
          pc.addTrack(track, stream);
        });
      })
      .catch((error) => {
        console.error('Error accessing camera:', error);
      });

    // 6. If this peer is the caller, create an offer when WebSocket is open.
    ws.current.onopen = () => {
      console.log('WebSocket onopen! isCaller =', isCaller);
      if (isCaller) {
        setTimeout(async () => {
          if (pc.signalingState === 'stable') {
            try {
              const offer = await pc.createOffer();
              await pc.setLocalDescription(offer);
              ws.current?.send(JSON.stringify({ offer }));
              console.log('Offer sent:', offer);
            } catch (error) {
              console.error('Error creating offer:', error);
            }
          }
        }, Math.random() * 500);
      }
    };

    // Cleanup on unmount.
    return () => {
      pc.close();
      ws.current?.close();
    };
  }, [isCaller]);

  // ASL Detection: If activated, periodically process the local video frame.
  useEffect(() => {
    let intervalId: number;
    if (aslActive && localVideoRef.current && canvasRef.current) {
      // Set up a canvas overlay on top of the local video.
      intervalId = window.setInterval(() => {
        const video = localVideoRef.current!;
        const canvas = canvasRef.current!;
        // Set canvas dimensions to match video.
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          // Draw current video frame onto the canvas.
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          // Run ASL detection on the canvas.
          runASLDetection(canvas);
        }
      }, 1000); // Process frame every second.
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [aslActive]);

  return (
    <div className="video-call-container">
      <div className="header">
        <h2>Two-Tab Video Call Demo with ASL Detection</h2>
        <p>
          <strong>Role:</strong> {isCaller ? 'Caller' : 'Callee'}
        </p>
        <button onClick={() => setAslActive(prev => !prev)}>
          {aslActive ? 'Stop ASL Detection' : 'Start ASL Detection'}
        </button>
      </div>
      <div className="video-container">
        <div className="video-box">
          <h3>Local Video</h3>
          <video ref={localVideoRef} autoPlay playsInline muted />
          {/* Canvas overlay for ASL detection results */}
          {aslActive && <canvas ref={canvasRef} style={{ position: 'absolute', top: 0, left: 0 }} />}
        </div>
        <div className="video-box">
          <h3>Remote Video</h3>
          <video ref={remoteVideoRef} autoPlay playsInline />
        </div>
      </div>
    </div>
  );
};

export default VideoCall;
