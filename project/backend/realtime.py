from fastapi import WebSocket
import asyncio
import uuid
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.connection:dict[
            uuid.UUID,
            set[WebSocket],
        ]=defaultdict(set)
        self.lock= asyncio.Lock()
        
    async def connect(
        self,
        user_id:uuid.UUID,
        websocket:WebSocket
    ):
        async with self.lock:
            self.connection[user_id].add(websocket)
    
    async def disconnect(
        self,
        user_id:uuid.UUID,
        websocket:WebSocket
    ):
        async with self.lock:
            user_connection=self.connection.get(user_id)
            if not user_connection:
                return
            user_connection.discard(websocket)
            if not user_connection:
                self.connection.pop(user_id, None)
    
    async def send_to_user(
        self,
        user_id:uuid.UUID,
        event:dict
    )->None:
        async with self.lock:
            user_connections=list(
                self.connection.get(user_id,set())
            )
        
        disconnected_connections:list[WebSocket]=[]
        
        for websocket in user_connections:
            try:
                await websocket.send_json(event)
            except Exception:
                disconnected_connections.append(websocket)

        for websocket in disconnected_connections:
            await self.disconnect(user_id, websocket)
            
    async def send_to_users(
        self,
        user_ids: list[uuid.UUID],
        event: dict,
    ) -> None:
        """Send an event to several users concurrently."""

        unique_user_ids = set(user_ids)

        await asyncio.gather(
            *[
                self.send_to_user(user_id, event)
                for user_id in unique_user_ids
            ],
            return_exceptions=True,
        )
        
manager=ConnectionManager()
