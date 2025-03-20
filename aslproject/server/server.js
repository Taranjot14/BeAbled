// server.js
const WebSocket = require('ws');

const port = 8080;
const wss = new WebSocket.Server({ port });
console.log(`Signaling server is running on ws://localhost:${port}`);
wss.on('connection', (ws) => {
  console.log('Client connected. Total clients:', wss.clients.size);
  console.log(`Signaling server is running on ws://localhost:${port}`);

  ws.on('message', (message) => {
    // Broadcast received message to all other connected clients
    wss.clients.forEach((client) => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  });

  ws.on('close', () => {
    console.log('Client disconnected. Total clients:', wss.clients.size);
  });
});


