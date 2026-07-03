from embalming_game.events import CardMoved
from embalming_game.models import Zone
from embalming_game.reducer import reduce_event
from embalming_game.setup import start_game


def test_card_can_move_from_used_area_back_to_hand() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=3)
    player = state.players[0]
    card_id = player.hand[0]
    state = reduce_event(
        state,
        CardMoved(card_id, Zone.HAND, player.id, Zone.USED, player.id),
    )

    state = reduce_event(
        state,
        CardMoved(card_id, Zone.USED, player.id, Zone.HAND, player.id),
    )

    assert card_id in state.player(player.id).hand
    assert card_id not in state.player(player.id).used


def test_card_can_move_between_suspicion_players() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=4)
    card_id = state.player("a").hand[0]
    state = reduce_event(
        state,
        CardMoved(card_id, Zone.HAND, "a", Zone.SUSPICION, "b"),
    )

    state = reduce_event(
        state,
        CardMoved(card_id, Zone.SUSPICION, "b", Zone.SUSPICION, "c"),
    )

    assert card_id not in state.player("b").suspicion
    assert card_id in state.player("c").suspicion


def test_card_can_exchange_between_embalming_and_hand() -> None:
    state, _ = start_game("game", ("a", "b", "c"), seed=5)
    hand_card = state.player("a").hand[0]
    state = reduce_event(
        state,
        CardMoved(hand_card, Zone.HAND, "a", Zone.EMBALMING, None),
    )

    state = reduce_event(
        state,
        CardMoved(hand_card, Zone.EMBALMING, None, Zone.HAND, "a"),
    )

    assert hand_card not in state.embalming
    assert hand_card in state.player("a").hand
