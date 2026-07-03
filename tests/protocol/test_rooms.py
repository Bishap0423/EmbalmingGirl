import asyncio
import json

import pytest
from embalming_server.main import app
from embalming_server.rooms import RoomError, RoomService, room_service
from httpx import ASGITransport, AsyncClient


async def _started_room() -> tuple[RoomService, str, list[str]]:
    service = RoomService()
    host = service.create_room("Host")
    guests = [
        service.join_room(host.room_id, "Guest 1"),
        service.join_room(host.room_id, "Guest 2"),
    ]
    credentials = [host, *guests]
    for item in credentials:
        service.set_ready(host.room_id, item.player_token, True)
    await service.start(host.room_id, host.player_token, seed=21)
    return service, host.room_id, [item.player_token for item in credentials]


def test_room_requires_host_ready_players_and_supported_count() -> None:
    async def scenario() -> None:
        service = RoomService()
        host = service.create_room("Host")
        guest = service.join_room(host.room_id, "Guest")

        with pytest.raises(RoomError, match="3 to 6"):
            await service.start(host.room_id, host.player_token, seed=1)

        third = service.join_room(host.room_id, "Third")
        for item in (host, guest, third):
            service.set_ready(host.room_id, item.player_token, True)

        with pytest.raises(RoomError, match="only the host"):
            await service.start(host.room_id, guest.player_token, seed=1)

        state = await service.start(host.room_id, host.player_token, seed=1)
        assert len(state.players) == 3

    asyncio.run(scenario())


def test_player_projection_never_contains_other_hands() -> None:
    async def scenario() -> None:
        service, room_id, tokens = await _started_room()
        room = service.room(room_id)
        assert room.game is not None
        snapshot = service.snapshot(room_id, tokens[0])
        encoded = json.dumps(snapshot)

        own_id = room.authenticate(tokens[0]).id
        for player in room.game.players:
            projected = next(
                item for item in snapshot["game"]["players"] if item["id"] == player.id
            )
            if player.id == own_id:
                assert projected["hand"] is not None
            else:
                assert projected["hand"] is None
                for card_id in player.hand:
                    assert card_id not in encoded

    asyncio.run(scenario())


def test_command_uses_token_identity_and_revision_control() -> None:
    async def scenario() -> None:
        service, room_id, tokens = await _started_room()
        room = service.room(room_id)
        assert room.game is not None
        active = room.game.active_player_id
        token = next(player.token for player in room.players if player.id == active)
        card = next(
            card_id
            for card_id in room.game.player(active).hand
            if room.game.card(card_id).definition_id != "criminal"
        )
        revision = room.game.revision
        payload = {
            "command": "play_embalming",
            "expected_revision": revision,
            "card_instance_id": card,
        }

        await service.command(room_id, token, payload)
        with pytest.raises(RoomError, match="stale revision"):
            await service.command(room_id, token, payload)

    asyncio.run(scenario())


def test_http_room_lifecycle_and_reconnect_snapshot() -> None:
    async def scenario() -> None:
        room_service.reset()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            created = await client.post("/api/rooms", json={"name": "Host"})
            host = created.json()
            room_id = host["room_id"]
            guests = []
            for name in ("Guest 1", "Guest 2"):
                response = await client.post(
                    f"/api/rooms/{room_id}/players",
                    json={"name": name},
                )
                guests.append(response.json())

            for item in (host, *guests):
                response = await client.put(
                    f"/api/rooms/{room_id}/ready",
                    headers={"X-Player-Token": item["player_token"]},
                    json={"ready": True},
                )
                assert response.status_code == 200

            started = await client.post(
                f"/api/rooms/{room_id}/start",
                headers={"X-Player-Token": host["player_token"]},
                json={"seed": 44},
            )
            reconnect = await client.get(
                f"/api/rooms/{room_id}",
                headers={"X-Player-Token": host["player_token"]},
            )

        assert started.status_code == 200
        assert reconnect.status_code == 200
        assert reconnect.json()["game"]["revision"] == started.json()["game"]["revision"]

    asyncio.run(scenario())
