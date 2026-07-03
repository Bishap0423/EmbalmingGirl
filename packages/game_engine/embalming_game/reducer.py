from __future__ import annotations

from dataclasses import replace

from embalming_game.events import (
    CardMoved,
    GameEvent,
    GameStarted,
    PhaseChanged,
    PlayerFinished,
    TurnAdvanced,
)
from embalming_game.models import GameState, Phase, PlayerState, Zone


def _replace_player(state: GameState, updated: PlayerState) -> GameState:
    players = tuple(updated if player.id == updated.id else player for player in state.players)
    return replace(state, players=players)


def _remove_from_source(state: GameState, event: CardMoved) -> GameState:
    if event.source_zone is not Zone.HAND or event.source_player_id is None:
        raise ValueError("M1 only supports moving cards from a player's hand")
    player = state.player(event.source_player_id)
    if event.card_instance_id not in player.hand:
        raise ValueError("source hand does not contain card")
    hand = tuple(card for card in player.hand if card != event.card_instance_id)
    return _replace_player(state, replace(player, hand=hand))


def _add_to_target(state: GameState, event: CardMoved) -> GameState:
    if event.target_zone is Zone.EMBALMING:
        return replace(state, embalming=(*state.embalming, event.card_instance_id))
    if event.target_player_id is None:
        raise ValueError("player zone requires target_player_id")
    player = state.player(event.target_player_id)
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
        active = None if event.phase is not state.phase else state.active_player_id
        updated = replace(state, phase=event.phase, active_player_id=active)
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
