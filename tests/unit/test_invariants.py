import pytest
from embalming_game import (
    PlayToEmbalming,
    assert_state_invariants,
    execute,
    start_game,
)
from embalming_game.models import Phase


@pytest.mark.parametrize("player_count", [3, 4, 5, 6])
@pytest.mark.parametrize("seed", range(10))
def test_scripted_games_preserve_card_location_invariants(
    player_count: int,
    seed: int,
) -> None:
    player_ids = tuple(f"player_{index}" for index in range(player_count))
    state, _ = start_game(f"game_{player_count}_{seed}", player_ids, seed)
    assert_state_invariants(state)

    while state.phase is Phase.TURN:
        actor = state.active_player_id
        assert actor is not None
        card_id = next(
            card
            for card in state.player(actor).hand
            if state.card(card).definition_id != "criminal"
        )
        state, _ = execute(
            state,
            PlayToEmbalming(actor, state.revision, card_id),
        )
        assert_state_invariants(state)
