import asyncio
from typing import Any

from embalming_server.realtime import RealtimeHub
from embalming_server.rooms import RoomService


class FakeSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.closed: tuple[int, str] | None = None
        self.messages: list[dict[str, Any]] = []

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int, reason: str) -> None:
        self.closed = (code, reason)

    async def send_json(self, message: dict[str, Any]) -> None:
        self.messages.append(message)


def test_reconnect_replaces_old_socket_and_restores_snapshot() -> None:
    async def scenario() -> None:
        rooms = RoomService()
        credentials = rooms.create_room("Host")
        hub = RealtimeHub(rooms)
        first = FakeSocket()
        second = FakeSocket()

        await hub.connect(credentials.room_id, credentials.player_token, first)  # type: ignore[arg-type]
        await hub.connect(credentials.room_id, credentials.player_token, second)  # type: ignore[arg-type]

        assert first.closed == (4001, "reconnected")
        assert second.accepted
        assert second.messages[-1]["type"] == "snapshot"
        assert second.messages[-1]["payload"]["viewer_player_id"] == credentials.player_id

    asyncio.run(scenario())


def test_websocket_command_envelope_broadcasts_personalized_snapshots() -> None:
    async def scenario() -> None:
        rooms = RoomService()
        host = rooms.create_room("Host")
        guest_one = rooms.join_room(host.room_id, "One")
        guest_two = rooms.join_room(host.room_id, "Two")
        for item in (host, guest_one, guest_two):
            rooms.set_ready(host.room_id, item.player_token, True)
        state = await rooms.start(host.room_id, host.player_token, 51)

        hub = RealtimeHub(rooms)
        sockets = {}
        for item in (host, guest_one, guest_two):
            socket = FakeSocket()
            sockets[item.player_id] = socket
            await hub.connect(host.room_id, item.player_token, socket)  # type: ignore[arg-type]

        active = state.active_player_id
        assert active is not None
        active_credentials = next(
            item for item in (host, guest_one, guest_two) if item.player_id == active
        )
        card = next(
            card_id
            for card_id in state.player(active).hand
            if state.card(card_id).definition_id != "criminal"
        )
        await hub.handle(
            host.room_id,
            active_credentials.player_token,
            {
                "type": "command",
                "expected_revision": state.revision,
                "payload": {
                    "command": "play_embalming",
                    "card_instance_id": card,
                },
            },
        )

        assert all(socket.messages[-1]["type"] == "snapshot" for socket in sockets.values())
        assert all(
            socket.messages[-1]["payload"]["game"]["revision"] > state.revision
            for socket in sockets.values()
        )

    asyncio.run(scenario())
