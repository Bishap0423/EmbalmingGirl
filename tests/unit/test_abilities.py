from embalming_game import resolve_ability, resolve_infected_trigger, start_game
from embalming_game.events import CardMoved, GameEvent
from embalming_game.models import GameState, Zone
from embalming_game.reducer import reduce_event


def _apply(state: GameState, events: tuple[GameEvent, ...]) -> GameState:
    for event in events:
        state = reduce_event(state, event)
    return state


def _prepare(ability: str) -> tuple[GameState, str, str]:
    state, _ = start_game("game", ("a", "b", "c", "d", "e"), seed=12)
    card = next(card for card in state.cards if card.definition_id == ability)
    owner = next(player.id for player in state.players if card.id in player.hand)
    state = reduce_event(
        state,
        CardMoved(card.id, Zone.HAND, owner, Zone.USED, owner),
    )
    return state, owner, card.id


def _first_hand_card(state: GameState, player_id: str) -> str:
    return state.player(player_id).hand[0]


def test_infected_schedules_and_resolves_free_choice() -> None:
    state, actor, ability_card = _prepare("infected")
    donor = next(player.id for player in state.players if player.id != actor)
    chosen = _first_hand_card(state, donor)
    state = reduce_event(
        state,
        CardMoved(chosen, Zone.HAND, donor, Zone.EMBALMING, None),
    )
    state = _apply(state, resolve_ability(state, actor, ability_card))
    trigger = state.delayed_triggers[0]

    state = _apply(state, resolve_infected_trigger(state, trigger.id, chosen))

    assert chosen in state.player(actor).hand
    assert not state.delayed_triggers


def test_accomplice_transfers_suspicion() -> None:
    state, actor, ability_card = _prepare("accomplice")
    card = _first_hand_card(state, actor)
    state = reduce_event(
        state,
        CardMoved(card, Zone.HAND, actor, Zone.SUSPICION, "b"),
    )

    state = _apply(state, resolve_ability(state, actor, ability_card, (card, "c")))

    assert card in state.player("c").suspicion


def test_class_representative_exchanges_selected_cards() -> None:
    state, actor, ability_card = _prepare("class_representative")
    target = next(player.id for player in state.players if player.id != actor)
    actor_card = _first_hand_card(state, actor)
    target_card = _first_hand_card(state, target)

    state = _apply(
        state,
        resolve_ability(
            state,
            actor,
            ability_card,
            (target, actor_card, target_card),
        ),
    )

    assert actor_card in state.player(target).hand
    assert target_card in state.player(actor).hand


def test_private_information_abilities_record_only_viewer_reveal() -> None:
    state, actor, ability_card = _prepare("disciplinary_committee")
    target = next(player.id for player in state.players if player.id != actor)

    state = _apply(state, resolve_ability(state, actor, ability_card, (target,)))

    reveal = state.private_reveals[-1]
    assert reveal.viewer_id == actor
    assert reveal.values == state.player(target).hand


def test_health_committee_recovers_other_non_health_used_card() -> None:
    state, actor, ability_card = _prepare("health_committee")
    source = next(player.id for player in state.players if player.id != actor)
    recovered = _first_hand_card(state, source)
    state = reduce_event(
        state,
        CardMoved(recovered, Zone.HAND, source, Zone.USED, source),
    )

    state = _apply(state, resolve_ability(state, actor, ability_card, (recovered,)))

    assert recovered in state.player(actor).hand


def test_lady_draws_and_returns_selected_card() -> None:
    state, actor, ability_card = _prepare("lady")
    target = next(player.id for player in state.players if player.id != actor)
    returned = _first_hand_card(state, actor)
    target_count = len(state.player(target).hand)

    state = _apply(
        state,
        resolve_ability(state, actor, ability_card, (target, returned)),
    )

    assert returned in state.player(target).hand
    assert len(state.player(target).hand) == target_count


def test_newspaper_passes_original_selections_left_simultaneously() -> None:
    state, actor, ability_card = _prepare("newspaper_club")
    selected = tuple(_first_hand_card(state, player.id) for player in state.players)

    state = _apply(state, resolve_ability(state, actor, ability_card, selected))

    ids = tuple(player.id for player in state.players)
    for index, card in enumerate(selected):
        assert card in state.player(ids[(index + 1) % len(ids)]).hand


def test_go_home_exchanges_hand_and_embalming() -> None:
    state, actor, ability_card = _prepare("go_home_club")
    donor = next(player.id for player in state.players if player.id != actor)
    embalming_card = _first_hand_card(state, donor)
    hand_card = _first_hand_card(state, actor)
    state = reduce_event(
        state,
        CardMoved(embalming_card, Zone.HAND, donor, Zone.EMBALMING, None),
    )

    state = _apply(
        state,
        resolve_ability(state, actor, ability_card, (hand_card, embalming_card)),
    )

    assert hand_card in state.embalming
    assert embalming_card in state.player(actor).hand
