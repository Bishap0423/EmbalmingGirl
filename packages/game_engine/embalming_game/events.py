from __future__ import annotations

from dataclasses import dataclass

from embalming_game.models import (
    CardInstance,
    DelayedTrigger,
    PendingDecision,
    Phase,
    PlayerState,
    PrivateReveal,
    Zone,
)


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


@dataclass(frozen=True, slots=True)
class DecisionRequested:
    decision: PendingDecision


@dataclass(frozen=True, slots=True)
class DecisionSubmitted:
    decision_id: str
    player_id: str
    selections: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecisionCleared:
    decision_id: str


@dataclass(frozen=True, slots=True)
class PrivateInformationRevealed:
    reveal: PrivateReveal


@dataclass(frozen=True, slots=True)
class TriggerScheduled:
    trigger: DelayedTrigger


@dataclass(frozen=True, slots=True)
class TriggerRemoved:
    trigger_id: str


GameEvent = (
    GameStarted
    | CardMoved
    | PlayerFinished
    | TurnAdvanced
    | PhaseChanged
    | DecisionRequested
    | DecisionSubmitted
    | DecisionCleared
    | PrivateInformationRevealed
    | TriggerScheduled
    | TriggerRemoved
)
