from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from typing import Any

from embalming_game import (
    InvalidCommand,
    PlaySpecial,
    PlaySuspicion,
    PlayToEmbalming,
    execute,
    start_game,
)
from embalming_game.commands import GameCommand, SubmitDecision
from embalming_game.events import GameEvent
from embalming_game.models import GameState

from embalming_server.views import project_game


class RoomError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(slots=True)
class RoomPlayer:
    id: str
    name: str
    token: str
    ready: bool = False


@dataclass(slots=True)
class Room:
    id: str
    host_player_id: str
    players: list[RoomPlayer]
    game: GameState | None = None
    events: list[GameEvent] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def authenticate(self, token: str) -> RoomPlayer:
        try:
            return next(player for player in self.players if player.token == token)
        except StopIteration as error:
            raise RoomError("UNAUTHORIZED", "invalid player token") from error


@dataclass(frozen=True, slots=True)
class Credentials:
    room_id: str
    player_id: str
    player_token: str


class RoomService:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def reset(self) -> None:
        self.rooms.clear()

    def create_room(self, player_name: str) -> Credentials:
        room_id = secrets.token_urlsafe(5)
        player = RoomPlayer("player_1", player_name, secrets.token_urlsafe(24))
        self.rooms[room_id] = Room(room_id, player.id, [player])
        return Credentials(room_id, player.id, player.token)

    def room(self, room_id: str) -> Room:
        try:
            return self.rooms[room_id]
        except KeyError as error:
            raise RoomError("ROOM_NOT_FOUND", "room does not exist") from error

    def join_room(self, room_id: str, player_name: str) -> Credentials:
        room = self.room(room_id)
        if room.game is not None:
            raise RoomError("GAME_ALREADY_STARTED", "game already started")
        if len(room.players) >= 6:
            raise RoomError("ROOM_FULL", "room is full")
        player = RoomPlayer(
            f"player_{len(room.players) + 1}",
            player_name,
            secrets.token_urlsafe(24),
        )
        room.players.append(player)
        return Credentials(room.id, player.id, player.token)

    def set_ready(self, room_id: str, token: str, ready: bool) -> None:
        room = self.room(room_id)
        room.authenticate(token).ready = ready

    async def start(self, room_id: str, token: str, seed: int) -> GameState:
        room = self.room(room_id)
        player = room.authenticate(token)
        async with room.lock:
            if player.id != room.host_player_id:
                raise RoomError("HOST_REQUIRED", "only the host can start")
            if room.game is not None:
                raise RoomError("GAME_ALREADY_STARTED", "game already started")
            if not 3 <= len(room.players) <= 6:
                raise RoomError("INVALID_PLAYER_COUNT", "3 to 6 players are required")
            if not all(candidate.ready for candidate in room.players):
                raise RoomError("PLAYERS_NOT_READY", "all players must be ready")
            state, event = start_game(
                room.id,
                tuple(candidate.id for candidate in room.players),
                seed,
            )
            room.game = state
            room.events.append(event)
            return state

    def snapshot(self, room_id: str, token: str) -> dict[str, Any]:
        room = self.room(room_id)
        viewer = room.authenticate(token)
        lobby: dict[str, Any] = {
            "room_id": room.id,
            "host_player_id": room.host_player_id,
            "viewer_player_id": viewer.id,
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "ready": player.ready,
                }
                for player in room.players
            ],
        }
        if room.game is not None:
            lobby["game"] = project_game(room.game, viewer.id)
        return lobby

    async def command(
        self,
        room_id: str,
        token: str,
        payload: dict[str, Any],
    ) -> GameState:
        room = self.room(room_id)
        player = room.authenticate(token)
        async with room.lock:
            if room.game is None:
                raise RoomError("GAME_NOT_STARTED", "game has not started")
            command = self._parse_command(player.id, payload)
            try:
                state, events = execute(room.game, command)
            except InvalidCommand as error:
                code = {
                    "stale revision": "STALE_REVISION",
                    "not your turn": "NOT_YOUR_TURN",
                    "card is not in actor hand": "CARD_NOT_IN_HAND",
                }.get(str(error), "ACTION_NOT_ALLOWED")
                raise RoomError(code, str(error)) from error
            except (ValueError, KeyError) as error:
                raise RoomError("ACTION_NOT_ALLOWED", str(error)) from error
            room.game = state
            room.events.extend(events)
            return state

    @staticmethod
    def _parse_command(actor_id: str, payload: dict[str, Any]) -> GameCommand:
        try:
            name = str(payload["command"])
            revision = int(payload["expected_revision"])
        except (KeyError, TypeError, ValueError) as error:
            raise RoomError("INVALID_COMMAND", "invalid command envelope") from error
        if name == "play_special":
            return PlaySpecial(actor_id, revision, str(payload["card_instance_id"]))
        if name == "play_embalming":
            return PlayToEmbalming(actor_id, revision, str(payload["card_instance_id"]))
        if name == "play_suspicion":
            return PlaySuspicion(
                actor_id,
                revision,
                str(payload["card_instance_id"]),
                str(payload["target_player_id"]),
            )
        if name == "submit_decision":
            selections = payload.get("selections", ())
            if not isinstance(selections, list):
                raise RoomError("INVALID_COMMAND", "selections must be a list")
            return SubmitDecision(
                actor_id,
                revision,
                str(payload["decision_id"]),
                tuple(str(item) for item in selections),
            )
        raise RoomError("INVALID_COMMAND", "unknown command")


room_service = RoomService()
