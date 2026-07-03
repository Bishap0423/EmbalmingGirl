import pytest
from embalming_game.events import DecisionCleared, DecisionRequested, DecisionSubmitted
from embalming_game.models import PendingDecision, Phase
from embalming_game.reducer import reduce_event
from embalming_game.setup import start_game


def test_pending_decision_is_serializable_state_and_collects_responses() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=8)
    decision = PendingDecision(
        id="decision_1",
        kind="select_card",
        ability_card_id="card_01",
        owner_id="a",
        responders=("a", "b"),
        context=(("target", "b"),),
    )

    state = reduce_event(state, DecisionRequested(decision))
    assert state.phase is Phase.RESOLVING
    assert state.pending_decision == decision

    state = reduce_event(state, DecisionSubmitted("decision_1", "a", ("card_02",)))
    assert state.pending_decision is not None
    assert state.pending_decision.submissions == (("a", ("card_02",)),)

    state = reduce_event(state, DecisionCleared("decision_1"))
    assert state.phase is Phase.TURN
    assert state.pending_decision is None


def test_player_cannot_submit_same_decision_twice() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=9)
    decision = PendingDecision("d", "select", "card_01", "a", ("a",))
    state = reduce_event(state, DecisionRequested(decision))
    state = reduce_event(state, DecisionSubmitted("d", "a", ("card_02",)))

    with pytest.raises(ValueError, match="already submitted"):
        reduce_event(state, DecisionSubmitted("d", "a", ("card_03",)))
