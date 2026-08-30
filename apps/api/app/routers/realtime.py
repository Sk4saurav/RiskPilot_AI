from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict

router = APIRouter(
    prefix="/v1/cases",
    tags=["Realtime"],
)

class ConnectionManager:
    def __init__(self):
        # org_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: str):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)

    def disconnect(self, websocket: WebSocket, org_id: str):
        if org_id in self.active_connections:
            self.active_connections[org_id].remove(websocket)
            if not self.active_connections[org_id]:
                del self.active_connections[org_id]

    async def broadcast_to_org(self, org_id: str, message: dict):
        if org_id in self.active_connections:
            for connection in self.active_connections[org_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    # In a real app, validate the JWT token here
    # For now, we expect org_id passed via query param or simple token
    # Let's extract org_id from the token (mocking for simplicity in WS)
    # Proper implementation requires decoding the JWT.
    
    org_id = token # For now, we'll just pass org_id directly as the token
    
    if not org_id:
        await websocket.close(code=1008)
        return
        
    await manager.connect(websocket, org_id)
    try:
        while True:
            data = await websocket.receive_text()
            # We don't expect client messages, just keep connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket, org_id)

async def notify_case_update(org_id: str, case_id: str, status: str):
    await manager.broadcast_to_org(org_id, {
        "type": "CASE_UPDATE",
        "case_id": case_id,
        "status": status
    })
