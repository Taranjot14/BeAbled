// src/VideoCall.tsx
import React, { useEffect, useRef, useState } from 'react';
import './VideoCall.css';

const VideoCall: React.FC = () => {
  const params = new URLSearchParams(window.location.search);
  const isCaller = params.get('caller') === '1';

  const localVideoRef = useRef<HTMLVideoElement | null>(null);
  const remoteVideoRef = useRef<HTMLVideoElement | null>(null);

  const [peerConnection, setPeerConnection] = useState<RTCPeerConnection | null>(null);
  const ws = useRef<WebSocket | null>(null);

  // Are we currently connected in a call?
  const [isConnected, setIsConnected] = useState(false);
  // Has local camera started?
  const [localStreamStarted, setLocalStreamStarted] = useState(false);

  // NEW: State to track whether ASL detection is on
  const [aslDetectionOn, setAslDetectionOn] = useState(false);

  useEffect(() => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    });
    setPeerConnection(pc);

    pc.ontrack = (event) => {
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = event.streams[0];
      }
    };

    ws.current = new WebSocket('ws://localhost:8080');
    ws.current.onmessage = async (event) => {
      if (typeof event.data !== 'string') return;
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

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        ws.current?.send(JSON.stringify({ ice: event.candidate }));
      }
    };

    return () => {
      pc.close();
      ws.current?.close();
    };
  }, []);

  // Start local camera if not already
  const startLocalStream = async () => {
    if (localStreamStarted) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      peerConnection?.getSenders().forEach(sender => peerConnection?.removeTrack(sender));
      stream.getTracks().forEach(track => {
        peerConnection?.addTrack(track, stream);
      });
      setLocalStreamStarted(true);
    } catch (err) {
      console.error('Error accessing camera:', err);
    }
  };

  // Connect button
  const handleConnect = async () => {
    if (!peerConnection || !ws.current) return;
    await startLocalStream();
    if (isCaller) {
      try {
        if (peerConnection.signalingState === 'stable') {
          const offer = await peerConnection.createOffer();
          await peerConnection.setLocalDescription(offer);
          ws.current.send(JSON.stringify({ offer }));
          console.log('Offer sent:', offer);
        }
      } catch (err) {
        console.error('Error creating offer:', err);
      }
    }
    setIsConnected(true);
  };

  // End call button
  const handleEndCall = () => {
    console.log('Ending call...');
    peerConnection?.close();
    setIsConnected(false);
    setLocalStreamStarted(false);

    // Stop local video
    if (localVideoRef.current) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      localVideoRef.current.srcObject = null;
    }
    // Clear remote
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null;
    }
  };

  // NEW: Toggle ASL detection
  const handleToggleASL = () => {
    const newValue = !aslDetectionOn;
    setAslDetectionOn(newValue);

    if (newValue) {
      // If the user is turning ASL ON, you might instruct them to run the Python script
      // or send a message to the server to start capturing frames, etc.
      console.log('ASL detection ON - run Python or other logic here.');
    } else {
      // If the user is turning ASL OFF
      console.log('ASL detection OFF - stop Python or other logic here.');
    }
  };

  return (
    <div className="video-call-container">
      <div className="header">
        <h2>Two-Tab Video Call Demo with ASL Detection</h2>
        <p><strong>Role:</strong> {isCaller ? 'Caller' : 'Callee'}</p>
      </div>

      <div className="button-group">
        {!isConnected && (
          <button className="connect-btn" onClick={handleConnect}>
            {isCaller ? 'Connect as Caller' : 'Connect as Callee'}
          </button>
        )}
        {isConnected && (
          <>
            <button className="end-btn" onClick={handleEndCall}>
              End Call
            </button>
            <button
              className="connect-btn"
              style={{ backgroundColor: aslDetectionOn ? '#FF9800' : '#4CAF50' }}
              onClick={handleToggleASL}
            >
              {aslDetectionOn ? 'Stop ASL Detection' : 'Start ASL Detection'}
            </button>
          </>
        )}
      </div>

      <div className="video-container">
        <div className="video-box">
          <h3>Local Video</h3>
          <video ref={localVideoRef} autoPlay playsInline muted />
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
