from typing import List
from fastapi import WebSocket

class ConnectionManager:
    """
    Manages active WebSocket connections and handles broadcasting messages.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        Sends a JSON message to all connected clients.
        """
        # Iterate over a copy to avoid modification issues during iteration (though disconnect handles remove)
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except:
                # If sending fails, assume disconnected
                self.disconnect(connection)

# Global instance
manager = ConnectionManager()
