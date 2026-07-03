from __future__ import annotations

from dataclasses import replace

from embalming_game.events import (
    CardMoved,
    DecisionCleared,
    DecisionRequested,
    DecisionSubmitted,
    GameEvent,
    GameScored,
    GameStarted,
    PhaseChanged,
    PlayerFinished,
    PrivateInformationRevealed,
    TriggerRemoved,
    TriggerScheduled,
    TurnAdvanced,
)
from embalming_game.models import GameState, Phase, PlayerState, Zone


def _replace_player(state: GameState, updated: PlayerState) -> GameState:
    players = tuple(updated if player.id == updated.id else player for player in state.players)
    return replace(state, players=players)


def _without(cards: tuple[str, ...], card_id: str, zone: Zone) -> tuple[str, ...]:
    if card_id not in cards:
        raise ValueError(f"{zone} does not contain card")
    return tuple(candidate for candidate in cards if candidate != card_id)


def _remove_from_source(state: GameState, event: CardMoved) -> GameState:
    if event.source_zone is Zone.EMBALMING:
        if event.source_player_id is not None:
            raise ValueError("embalming source cannot have a player")
        return replace(
            state,
            embalming=_without(state.embalming, event.card_instance_id, Zone.EMBALMING),
        )
    if event.source_player_id is None:
        raise ValueError("player source zone requires source_player_id")

    player = state.player(event.source_player_id)
    if event.source_zone is Zone.HAND:
        updated = replace(
            player,
            hand=_without(player.hand, event.card_instance_id, Zone.HAND),
        )
    elif event.source_zone is Zone.USED:
        updated = replace(
            player,
            used=_without(player.used, event.card_instance_id, Zone.USED),
        )
    elif event.source_zone is Zone.SUSPICION:
        updated = replace(
            player,
            suspicion=_without(player.suspicion, event.card_instance_id, Zone.SUSPICION),
        )
    else:
        raise ValueError(f"unsupported source zone {event.source_zone}")
    return _replace_player(state, updated)


def _add_to_target(state: GameState, event: CardMoved) -> GameState:
    if event.target_zone is Zone.EMBALMING:
        if event.target_player_id is not None:
            raise ValueError("embalming target cannot have a player")
        return replace(state, embalming=(*state.embalming, event.card_instance_id))
    if event.target_player_id is None:
        raise ValueError("player zone requires target_player_id")
    player = state.player(event.target_player_id)
    if event.target_zone is Zone.HAND:
        return _replace_player(
            state,
            replace(player, hand=(*player.hand, event.card_instance_id)),
        )
    if event.target_zone is Zone.USED:
        return _replace_player(
            state,
            replace(player, used=(*player.used, event.card_instance_id)),
        )
    if event.target_zone is Zone.SUSPICION:
        return _replace_player(
            state,
            replace(player, suspicion=(*player.suspicion, event.card_instance_id)),
        )
    raise ValueError(f"unsupported target zone {event.target_zone}")


def reduce_event(state: GameState | None, event: GameEvent) -> GameState:
    if isinstance(event, GameStarted):
        if state is not None:
            raise ValueError("GameStarted requires an empty state")
        return GameState(
            id=event.game_id,
            ruleset_version=event.ruleset_version,
            seed=event.seed,
            revision=1,
            phase=Phase.TURN,
            target=event.target,
            player_order=event.player_order,
            players=event.players,
            cards=event.cards,
            active_player_id=event.active_player_id,
        )
    if state is None:
        raise ValueError("the first event must be GameStarted")

    updated = state
    if isinstance(event, CardMoved):
        updated = _add_to_target(_remove_from_source(state, event), event)
    elif isinstance(event, PlayerFinished):
        player = state.player(event.player_id)
        updated = _replace_player(state, replace(player, finished=True))
    elif isinstance(event, TurnAdvanced):
        updated = replace(state, active_player_id=event.player_id)
    elif isinstance(event, PhaseChanged):
        active = state.active_player_id if event.phase is Phase.TURN else None
        updated = replace(state, phase=event.phase, active_player_id=active)
    elif isinstance(event, DecisionRequested):
        if state.pending_decision is not None:
            raise ValueError("another decision is already pending")
        updated = replace(
            state,
            phase=Phase.RESOLVING,
            pending_decision=event.decision,
        )
    elif isinstance(event, DecisionSubmitted):
        decision = state.pending_decision
        if decision is None or decision.id != event.decision_id:
            raise ValueError("decision is not pending")
        if event.player_id not in decision.responders:
            raise ValueError("player is not a decision responder")
        if any(player_id == event.player_id for player_id, _ in decision.submissions):
            raise ValueError("player already submitted this decision")
        updated = replace(
            state,
            pending_decision=replace(
                decision,
                submissions=(
                    *decision.submissions,
                    (event.player_id, event.selections),
                ),
            ),
        )
    elif isinstance(event, DecisionCleared):
        decision = state.pending_decision
        if decision is None or decision.id != event.decision_id:
            raise ValueError("decision is not pending")
        updated = replace(state, phase=Phase.TURN, pending_decision=None)
    elif isinstance(event, PrivateInformationRevealed):
        updated = replace(
            state,
            private_reveals=(*state.private_reveals, event.reveal),
        )
    elif isinstance(event, TriggerScheduled):
        if any(trigger.id == event.trigger.id for trigger in state.delayed_triggers):
            raise ValueError("trigger ID must be unique")
        updated = replace(
            state,
            delayed_triggers=(*state.delayed_triggers, event.trigger),
        )
    elif isinstance(event, TriggerRemoved):
        if not any(trigger.id == event.trigger_id for trigger in state.delayed_triggers):
            raise ValueError("trigger does not exist")
        updated = replace(
            state,
            delayed_triggers=tuple(
                trigger for trigger in state.delayed_triggers if trigger.id != event.trigger_id
            ),
        )
    elif isinstance(event, GameScored):
        if state.phase is not Phase.SCORING:
            raise ValueError("game can only be scored in scoring phase")
        updated = replace(
            state,
            phase=Phase.FINISHED,
            active_player_id=None,
            result=event.result,
        )
    else:
        raise TypeError(f"unknown event {type(event)!r}")
    return replace(updated, revision=state.revision + 1)


def replay(events: tuple[GameEvent, ...]) -> GameState:
    state: GameState | None = None
    for event in events:
        state = reduce_event(state, event)
    if state is None:
        raise ValueError("cannot replay an empty event stream")
    return state
