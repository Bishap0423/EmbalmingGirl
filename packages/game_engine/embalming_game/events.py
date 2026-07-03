from __future__ import annotations

from dataclasses import dataclass

from embalming_game.models import CardInstance, Phase, PlayerState, Zone


@dataclass(frozen=True, slots=True)
class GameStarted:
    game_id: str
    ruleset_version: str
    seed: int
    target: int
    player_order: tuple[str, ...]
    players: tuple[PlayerState, ...]
    cards: tuple[CardInstance, ...]
    active_player_id: str


@dataclass(frozen=True, slots=True)
class CardMoved:
    card_instance_id: str
    source_zone: Zone
    source_player_id: str | None
    target_zone: Zone
    target_player_id: str | None


@dataclass(frozen=True, slots=True)
class PlayerFinished:
    player_id: str


@dataclass(frozen=True, slots=True)
class TurnAdvanced:
    player_id: str


@dataclass(frozen=True, slots=True)
class PhaseChanged:
    phase: Phase


GameEvent = GameStarted | CardMoved | PlayerFinished | TurnAdvanced | PhaseChanged
