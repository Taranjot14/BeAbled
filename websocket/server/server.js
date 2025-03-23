// server.js
const WebSocket = require('ws');

const port = 8080;
const wss = new WebSocket.Server({ port }, () => {
  console.log(`Signaling server is running on ws://localhost:${port}`);
});

wss.on('connection', (ws) => {
  console.log('Client connected');
  
  // Notify all other clients that a new peer has connected.
  wss.clients.forEach((client) => {
    if (client !== ws && client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ new_peer: true }));
    }
  });

  ws.on('message', (message, isBinary) => {
    // Convert binary data to string if needed
    if (isBinary) {
      message = message.toString();
    }
    // Broadcast the message to all other clients
    wss.clients.forEach((client) => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(message.toString());
      }
    });
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});
