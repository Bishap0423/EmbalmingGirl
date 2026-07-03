from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Phase(StrEnum):
    TURN = "turn"
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
