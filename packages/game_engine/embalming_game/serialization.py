from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from embalming_game.events import GameEvent
from embalming_game.models import GameState


def _canonical(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def event_to_json(event: GameEvent) -> str:
    return _canonical(
        {
            "type": type(event).__name__,
            "payload": asdict(event),
        }
    )


def state_fingerprint(state: GameState) -> str:
    return hashlib.sha256(_canonical(asdict(state)).encode()).hexdigest()
