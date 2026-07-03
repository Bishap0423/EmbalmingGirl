from typing import Any

from embalming_game import load_card_catalog
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from embalming_server.realtime import realtime_hub
from embalming_server.rooms import Credentials, RoomError, room_service

app = FastAPI(title="Embalming Girl API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    ruleset: str
    card_types: int
    card_instances: int


class PlayerNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class ReadyRequest(BaseModel):
    ready: bool = True


class StartRequest(BaseModel):
    seed: int


class CommandRequest(BaseModel):
    command: str
    expected_revision: int
    card_instance_id: str | None = None
    target_player_id: str | None = None
    decision_id: str | None = None
    selections: list[str] | None = None


def _credentials(value: Credentials) -> dict[str, str]:
    return {
        "room_id": value.room_id,
        "player_id": value.player_id,
        "player_token": value.player_token,
    }


def _room_error(error: RoomError) -> HTTPException:
    status = 401 if error.code == "UNAUTHORIZED" else 400
    if error.code == "ROOM_NOT_FOUND":
        status = 404
    return HTTPException(
        status_code=status,
        detail={"code": error.code, "message": str(error)},
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    cards = load_card_catalog()
    return HealthResponse(
        status="ok",
        ruleset="2020-06-30-project-ruling-1",
        card_types=len(cards),
        card_instances=sum(card.copies for card in cards),
    )


@app.post("/api/rooms")
async def create_room(body: PlayerNameRequest) -> dict[str, str]:
    return _credentials(room_service.create_room(body.name))


@app.post("/api/rooms/{room_id}/players")
async def join_room(room_id: str, body: PlayerNameRequest) -> dict[str, str]:
    try:
        return _credentials(room_service.join_room(room_id, body.name))
    except RoomError as error:
        raise _room_error(error) from error


@app.put("/api/rooms/{room_id}/ready")
async def set_ready(
    room_id: str,
    body: ReadyRequest,
    x_player_token: str = Header(),
) -> dict[str, bool]:
    try:
        room_service.set_ready(room_id, x_player_token, body.ready)
        await realtime_hub.broadcast(room_id)
        return {"ready": body.ready}
    except RoomError as error:
        raise _room_error(error) from error


@app.post("/api/rooms/{room_id}/start")
async def start_room(
    room_id: str,
    body: StartRequest,
    x_player_token: str = Header(),
) -> dict[str, Any]:
    try:
        await room_service.start(room_id, x_player_token, body.seed)
        await realtime_hub.broadcast(room_id)
        return room_service.snapshot(room_id, x_player_token)
    except RoomError as error:
        raise _room_error(error) from error


@app.get("/api/rooms/{room_id}")
async def get_room(
    room_id: str,
    x_player_token: str = Header(),
) -> dict[str, Any]:
    try:
        return room_service.snapshot(room_id, x_player_token)
    except RoomError as error:
        raise _room_error(error) from error


@app.post("/api/rooms/{room_id}/commands")
async def submit_command(
    room_id: str,
    body: CommandRequest,
    x_player_token: str = Header(),
) -> dict[str, Any]:
    try:
        await room_service.command(
            room_id,
            x_player_token,
            body.model_dump(exclude_none=True),
        )
        await realtime_hub.broadcast(room_id)
        return room_service.snapshot(room_id, x_player_token)
    except RoomError as error:
        raise _room_error(error) from error


@app.websocket("/ws/rooms/{room_id}")
async def room_socket(socket: WebSocket, room_id: str, token: str) -> None:
    player_id: str | None = None
    try:
        player_id = await realtime_hub.connect(room_id, token, socket)
        while True:
            message = await socket.receive_json()
            try:
                await realtime_hub.handle(room_id, token, message)
            except RoomError as error:
                await socket.send_json(
                    {
                        "type": "command_rejected",
                        "payload": {"code": error.code, "message": str(error)},
                    }
                )
    except RoomError:
        await socket.close(code=4401)
    except WebSocketDisconnect:
        pass
    finally:
        if player_id is not None:
            realtime_hub.disconnect(room_id, player_id, socket)
