from embalming_game import (
    PlayToEmbalming,
    event_to_json,
    execute,
    start_game,
    state_fingerprint,
)
from embalming_game.models import GameState
from embalming_game.reducer import replay


def _playable(state: GameState, player_id: str) -> str:
    return next(
        card_id
        for card_id in state.player(player_id).hand
        if state.card(card_id).definition_id != "criminal"
    )


def test_event_replay_has_identical_state_fingerprint() -> None:
    state, started = start_game("replay", ("a", "b", "c"), seed=88)
    events = [started]

    for _ in range(5):
        actor = state.active_player_id
        assert actor is not None
        state, emitted = execute(
            state,
            PlayToEmbalming(actor, state.revision, _playable(state, actor)),
        )
        events.extend(emitted)

    replayed = replay(tuple(events))

    assert replayed == state
    assert state_fingerprint(replayed) == state_fingerprint(state)
    assert all(event_to_json(event).startswith('{"payload":') for event in events)
