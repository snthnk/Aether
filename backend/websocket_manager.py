from typing import Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def get_ws(self, client_id: str):
        return self.active_connections[client_id]

    async def send_json(self, client_id: str, event_dict: Dict[str, Any]):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(event_dict)


# Create a singleton instance
manager = ConnectionManager()
