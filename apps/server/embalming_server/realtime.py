from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket

from embalming_server.rooms import RoomError, RoomService, room_service


class RealtimeHub:
    def __init__(self, rooms: RoomService) -> None:
        self.rooms = rooms
        self.connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)

    async def connect(self, room_id: str, token: str, socket: WebSocket) -> str:
        room = self.rooms.room(room_id)
        player = room.authenticate(token)
        await socket.accept()
        previous = self.connections[room_id].get(player.id)
        if previous is not None:
            await previous.close(code=4001, reason="reconnected")
        self.connections[room_id][player.id] = socket
        await socket.send_json({"type": "snapshot", "payload": self.rooms.snapshot(room_id, token)})
        return player.id

    def disconnect(self, room_id: str, player_id: str, socket: WebSocket) -> None:
        if self.connections.get(room_id, {}).get(player_id) is socket:
            del self.connections[room_id][player_id]

    async def broadcast(self, room_id: str) -> None:
        room = self.rooms.room(room_id)
        stale: list[str] = []
        for player_id, socket in self.connections.get(room_id, {}).items():
            player = next(player for player in room.players if player.id == player_id)
            try:
                await socket.send_json(
                    {
                        "type": "snapshot",
                        "payload": self.rooms.snapshot(room_id, player.token),
                    }
                )
            except RuntimeError:
                stale.append(player_id)
        for player_id in stale:
            self.connections[room_id].pop(player_id, None)

    async def handle(self, room_id: str, token: str, message: object) -> None:
        if not isinstance(message, dict):
            raise RoomError("INVALID_COMMAND", "message must be an object")
        payload = message.get("payload", message)
        if not isinstance(payload, dict):
            raise RoomError("INVALID_COMMAND", "command payload must be an object")
        if "expected_revision" not in payload and "expected_revision" in message:
            payload = {**payload, "expected_revision": message["expected_revision"]}
        await self.rooms.command(room_id, token, payload)
        await self.broadcast(room_id)


realtime_hub = RealtimeHub(room_service)
