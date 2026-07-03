from __future__ import annotations

from embalming_game.commands import (
    GameCommand,
    PlaySpecial,
    PlaySuspicion,
    PlayToEmbalming,
    SubmitDecision,
)
from embalming_game.events import (
    CardMoved,
    DecisionSubmitted,
    GameEvent,
    PhaseChanged,
    PlayerFinished,
    TurnAdvanced,
)
from embalming_game.models import GameState, Phase, Zone
from embalming_game.reducer import reduce_event


class InvalidCommand(ValueError):
    pass


def _next_active_player(state: GameState, actor_id: str, finishing: bool) -> str | None:
    actor_index = state.player_order.index(actor_id)
    for offset in range(1, len(state.player_order) + 1):
        candidate_id = state.player_order[(actor_index + offset) % len(state.player_order)]
        candidate = state.player(candidate_id)
        if not candidate.finished and not (finishing and candidate_id == actor_id):
            return candidate_id
    return None


def decide(state: GameState, command: GameCommand) -> tuple[GameEvent, ...]:
    if isinstance(command, SubmitDecision):
        if state.phase is not Phase.RESOLVING or state.pending_decision is None:
            raise InvalidCommand("no decision is pending")
        if command.expected_revision != state.revision:
            raise InvalidCommand("stale revision")
        decision = state.pending_decision
        if command.decision_id != decision.id:
            raise InvalidCommand("decision is not pending")
        if command.actor_id not in decision.responders:
            raise InvalidCommand("not a decision responder")
        if any(player_id == command.actor_id for player_id, _ in decision.submissions):
            raise InvalidCommand("decision already submitted")
        return (
            DecisionSubmitted(
                decision_id=decision.id,
                player_id=command.actor_id,
                selections=command.selections,
            ),
        )

    if state.phase is not Phase.TURN:
        raise InvalidCommand("game is not accepting turn actions")
    if command.expected_revision != state.revision:
        raise InvalidCommand("stale revision")
    if command.actor_id != state.active_player_id:
        raise InvalidCommand("not your turn")

    actor = state.player(command.actor_id)
    if command.card_instance_id not in actor.hand:
        raise InvalidCommand("card is not in actor hand")
    card = state.card(command.card_instance_id)
    if card.definition_id == "criminal":
        raise InvalidCommand("this card cannot be played")

    if isinstance(command, PlaySpecial):
        target_zone = Zone.USED
        target_player_id = actor.id
    elif isinstance(command, PlayToEmbalming):
        target_zone = Zone.EMBALMING
        target_player_id = None
    elif isinstance(command, PlaySuspicion):
        if command.target_player_id == actor.id:
            raise InvalidCommand("cannot place suspicion on yourself")
        try:
            state.player(command.target_player_id)
        except KeyError as error:
            raise InvalidCommand("unknown suspicion target") from error
        target_zone = Zone.SUSPICION
        target_player_id = command.target_player_id
    else:
        raise TypeError(f"unknown command {type(command)!r}")

    events: list[GameEvent] = [
        CardMoved(
            card_instance_id=command.card_instance_id,
            source_zone=Zone.HAND,
            source_player_id=actor.id,
            target_zone=target_zone,
            target_player_id=target_player_id,
        )
    ]
    finishing = len(actor.hand) == 2
    if finishing:
        events.append(PlayerFinished(actor.id))

    next_player_id = _next_active_player(state, actor.id, finishing)
    if next_player_id is None:
        events.append(PhaseChanged(Phase.SCORING))
    else:
        events.append(TurnAdvanced(next_player_id))
    return tuple(events)


def execute(state: GameState, command: GameCommand) -> tuple[GameState, tuple[GameEvent, ...]]:
    events = decide(state, command)
    updated = state
    for event in events:
        updated = reduce_event(updated, event)
    return updated, events
