from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from transcription import RealtimeTranscriber
from main import analyze_transcript_with_ai

class ConnectionManager:
    """Manage WebSocket connections for real-time transcription"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.transcribers: Dict[str, RealtimeTranscriber] = {}
    
    async def connect(self, websocket: WebSocket, meeting_id: str):
        await websocket.accept()
        
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = set()
            self.transcribers[meeting_id] = RealtimeTranscriber()
        
        self.active_connections[meeting_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, meeting_id: str):
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].discard(websocket)
            
            # Clean up if no connections left
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]
                if meeting_id in self.transcribers:
                    del self.transcribers[meeting_id]
    
    async def broadcast(self, meeting_id: str, message: dict):
        """Send message to all connections in a meeting"""
        if meeting_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[meeting_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection, meeting_id)
    
    def get_transcriber(self, meeting_id: str) -> RealtimeTranscriber:
        """Get transcriber for a meeting"""
        return self.transcribers.get(meeting_id)

manager = ConnectionManager()

# Add this to your main.py
"""
from websocket import manager, websocket_endpoint

# Add WebSocket endpoint
@app.websocket("/ws/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    await manager.connect(websocket, meeting_id)
    
    try:
        while True:
            # Receive audio data or text from client
            data = await websocket.receive_json()
            
            if data["type"] == "audio_chunk":
                # Process audio chunk
                transcriber = manager.get_transcriber(meeting_id)
                
                if transcriber:
                    # Transcribe audio chunk
                    import base64
                    audio_bytes = base64.b64decode(data["audio"])
                    text = await transcriber.process_audio_chunk(audio_bytes)
                    
                    # Broadcast partial transcript
                    await manager.broadcast(meeting_id, {
                        "type": "partial_transcript",
                        "text": text,
                        "timestamp": data.get("timestamp")
                    })
            
            elif data["type"] == "finalize":
                # Get complete transcript and analyze
                transcriber = manager.get_transcriber(meeting_id)
                
                if transcriber:
                    full_transcript = transcriber.get_full_transcript()
                    
                    # Analyze with AI
                    analysis = await analyze_transcript_with_ai(full_transcript)
                    
                    # Broadcast final analysis
                    await manager.broadcast(meeting_id, {
                        "type": "analysis_complete",
                        "transcript": full_transcript,
                        "analysis": analysis.dict()
                    })
                    
                    # Clear buffer
                    transcriber.clear_buffer()
            
            elif data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)
        await manager.broadcast(meeting_id, {
            "type": "participant_left",
            "message": "A participant has left"
        })
"""

# WebSocket client example for React
websocket_client_example = """
// In your React component

const [ws, setWs] = useState(null);
const mediaRecorderRef = useRef(null);

const connectWebSocket = (meetingId) => {
  const socket = new WebSocket(`ws://localhost:8000/ws/${meetingId}`);
  
  socket.onopen = () => {
    console.log('WebSocket connected');
  };
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'partial_transcript') {
      setTranscript(prev => prev + ' ' + data.text);
    } else if (data.type === 'analysis_complete') {
      setAnalysis(data.analysis);
    }
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  socket.onclose = () => {
    console.log('WebSocket disconnected');
  };
  
  setWs(socket);
};

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && ws) {
        // Convert blob to base64 and send
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          ws.send(JSON.stringify({
            type: 'audio_chunk',
            audio: base64Audio,
            timestamp: Date.now()
          }));
        };
        reader.readAsDataURL(event.data);
      }
    };
    
    mediaRecorder.start(1000); // Send chunks every second
    setIsRecording(true);
  } catch (error) {
    console.error('Error starting recording:', error);
  }
};

const stopRecording = () => {
  if (mediaRecorderRef.current) {
    mediaRecorderRef.current.stop();
    setIsRecording(false);
    
    // Request final analysis
    if (ws) {
      ws.send(JSON.stringify({ type: 'finalize' }));
    }
  }
};
"""