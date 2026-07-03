from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Phase(StrEnum):
    TURN = "turn"
    RESOLVING = "resolving"
    SCORING = "scoring"
    FINISHED = "finished"


class Zone(StrEnum):
    HAND = "hand"
    USED = "used"
    EMBALMING = "embalming"
    SUSPICION = "suspicion"


@dataclass(frozen=True, slots=True)
class CardInstance:
    id: str
    definition_id: str


@dataclass(frozen=True, slots=True)
class PlayerState:
    id: str
    seat: int
    hand: tuple[str, ...]
    used: tuple[str, ...] = ()
    suspicion: tuple[str, ...] = ()
    finished: bool = False


@dataclass(frozen=True, slots=True)
class PendingDecision:
    id: str
    kind: str
    ability_card_id: str
    owner_id: str
    responders: tuple[str, ...]
    context: tuple[tuple[str, str], ...] = ()
    submissions: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True, slots=True)
class PrivateReveal:
    viewer_id: str
    reason: str
    values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DelayedTrigger:
    id: str
    kind: str
    owner_id: str
    source_card_id: str


@dataclass(frozen=True, slots=True)
class GameState:
    id: str
    ruleset_version: str
    seed: int
    revision: int
    phase: Phase
    target: int
    player_order: tuple[str, ...]
    players: tuple[PlayerState, ...]
    cards: tuple[CardInstance, ...]
    active_player_id: str | None
    embalming: tuple[str, ...] = ()
    pending_decision: PendingDecision | None = None
    private_reveals: tuple[PrivateReveal, ...] = ()
    delayed_triggers: tuple[DelayedTrigger, ...] = ()

    def player(self, player_id: str) -> PlayerState:
        try:
            return next(player for player in self.players if player.id == player_id)
        except StopIteration as error:
            raise KeyError(f"unknown player {player_id!r}") from error

    def card(self, instance_id: str) -> CardInstance:
        try:
            return next(card for card in self.cards if card.id == instance_id)
        except StopIteration as error:
            raise KeyError(f"unknown card instance {instance_id!r}") from error
