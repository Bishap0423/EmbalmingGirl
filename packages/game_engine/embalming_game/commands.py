from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Command:
    actor_id: str
    expected_revision: int


@dataclass(frozen=True, slots=True)
class PlaySpecial(Command):
    card_instance_id: str


@dataclass(frozen=True, slots=True)
class PlayToEmbalming(Command):
    card_instance_id: str


@dataclass(frozen=True, slots=True)
class PlaySuspicion(Command):
    card_instance_id: str
    target_player_id: str


GameCommand = PlaySpecial | PlayToEmbalming | PlaySuspicion
