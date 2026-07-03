from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any


@dataclass(frozen=True, slots=True)
class CardDefinition:
    id: str
    name_ja: str
    name_zh: str
    mp: int
    copies: int
    victory_priority: int
    ability: str
    victory: str
    art_key: str


def _require_int(record: dict[str, Any], key: str) -> int:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key!r} must be an integer")
    return value


def _parse_card(record: dict[str, Any]) -> CardDefinition:
    string_keys = ("id", "name_ja", "name_zh", "ability", "victory", "art_key")
    strings: dict[str, str] = {}
    for key in string_keys:
        value = record.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{key!r} must be a non-empty string")
        strings[key] = value

    return CardDefinition(
        id=strings["id"],
        name_ja=strings["name_ja"],
        name_zh=strings["name_zh"],
        mp=_require_int(record, "mp"),
        copies=_require_int(record, "copies"),
        victory_priority=_require_int(record, "victory_priority"),
        ability=strings["ability"],
        victory=strings["victory"],
        art_key=strings["art_key"],
    )


@lru_cache(maxsize=1)
def load_card_catalog() -> tuple[CardDefinition, ...]:
    resource = files("embalming_game").joinpath("data/cards.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported card catalog schema")

    records = payload.get("cards")
    if not isinstance(records, list):
        raise ValueError("'cards' must be a list")

    cards = tuple(_parse_card(record) for record in records if isinstance(record, dict))
    if len(cards) != len(records):
        raise ValueError("every card record must be an object")

    ids = [card.id for card in cards]
    if len(ids) != len(set(ids)):
        raise ValueError("card IDs must be unique")
    if sum(card.copies for card in cards) != 25:
        raise ValueError("the standard catalog must contain exactly 25 cards")
    return cards
