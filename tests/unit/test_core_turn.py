import pytest
from embalming_game import (
    InvalidCommand,
    PlaySpecial,
    PlaySuspicion,
    PlayToEmbalming,
    execute,
    start_game,
)
from embalming_game.models import GameState, Phase


def _first_playable_card(state: GameState, player_id: str) -> str:
    player = state.player(player_id)
    return next(
        card_id for card_id in player.hand if state.card(card_id).definition_id != "criminal"
    )


def test_setup_is_deterministic_and_president_starts() -> None:
    first, first_event = start_game("game", ("a", "b", "c"), seed=42)
    second, second_event = start_game("game", ("a", "b", "c"), seed=42)

    assert first == second
    assert first_event == second_event
    active = first.player(first.active_player_id)
    assert any(
        first.card(card_id).definition_id == "student_council_president" for card_id in active.hand
    )


def test_three_basic_actions_move_cards_to_authoritative_zones() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=7)
    actor = state.active_player_id
    assert actor is not None

    special_card = _first_playable_card(state, actor)
    state, _ = execute(state, PlaySpecial(actor, state.revision, special_card))
    assert special_card in state.player(actor).used

    actor = state.active_player_id
    assert actor is not None
    embalming_card = _first_playable_card(state, actor)
    state, _ = execute(state, PlayToEmbalming(actor, state.revision, embalming_card))
    assert state.embalming[-1] == embalming_card

    actor = state.active_player_id
    assert actor is not None
    target = next(player_id for player_id in state.player_order if player_id != actor)
    suspicion_card = _first_playable_card(state, actor)
    state, _ = execute(
        state,
        PlaySuspicion(actor, state.revision, suspicion_card, target),
    )
    assert state.player(target).suspicion[-1] == suspicion_card


def test_invalid_command_does_not_mutate_state() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=1)
    original = state
    non_active = next(player.id for player in state.players if player.id != state.active_player_id)

    with pytest.raises(InvalidCommand, match="not your turn"):
        execute(
            state,
            PlayToEmbalming(
                non_active,
                state.revision,
                state.player(non_active).hand[0],
            ),
        )

    assert state == original


def test_players_finish_at_one_card_and_game_enters_scoring() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=19)

    while state.phase is Phase.TURN:
        actor = state.active_player_id
        assert actor is not None
        card_id = _first_playable_card(state, actor)
        state, _ = execute(state, PlayToEmbalming(actor, state.revision, card_id))

    assert state.phase is Phase.SCORING
    assert state.active_player_id is None
    assert all(player.finished and len(player.hand) == 1 for player in state.players)
