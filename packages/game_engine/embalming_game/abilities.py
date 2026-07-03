from __future__ import annotations

import random

from embalming_game.events import (
    CardMoved,
    GameEvent,
    PrivateInformationRevealed,
    TriggerRemoved,
    TriggerScheduled,
)
from embalming_game.models import DelayedTrigger, GameState, PrivateReveal, Zone


class InvalidAbility(ValueError):
    pass


def _move(
    card_id: str,
    source_zone: Zone,
    source_player: str | None,
    target_zone: Zone,
    target_player: str | None,
) -> CardMoved:
    return CardMoved(card_id, source_zone, source_player, target_zone, target_player)


def _definition(state: GameState, card_id: str) -> str:
    try:
        return state.card(card_id).definition_id
    except KeyError as error:
        raise InvalidAbility("unknown card") from error


def resolve_ability(
    state: GameState,
    actor_id: str,
    ability_card_id: str,
    selections: tuple[str, ...] = (),
) -> tuple[GameEvent, ...]:
    actor = state.player(actor_id)
    if ability_card_id not in actor.used:
        raise InvalidAbility("ability card is not in actor used area")
    ability = _definition(state, ability_card_id)

    if ability in {"alien", "student_council_president"}:
        return ()
    if ability == "criminal":
        raise InvalidAbility("criminal cannot be used")
    if ability == "infected":
        trigger = DelayedTrigger(
            id=f"trigger:{ability_card_id}:{state.revision}",
            kind="infected_recover",
            owner_id=actor_id,
            source_card_id=ability_card_id,
        )
        return (TriggerScheduled(trigger),)
    if ability == "accomplice":
        if len(selections) != 2:
            raise InvalidAbility("accomplice requires suspicion card and target")
        card_id, target_id = selections
        source_id = next(
            (player.id for player in state.players if card_id in player.suspicion),
            None,
        )
        if source_id is None or target_id == source_id:
            raise InvalidAbility("invalid suspicion transfer")
        state.player(target_id)
        return (_move(card_id, Zone.SUSPICION, source_id, Zone.SUSPICION, target_id),)
    if ability == "class_representative":
        if len(selections) != 3:
            raise InvalidAbility("class representative requires target and two cards")
        target_id, actor_card, target_card = selections
        if target_id == actor_id:
            raise InvalidAbility("must choose another player")
        if actor_card not in actor.hand or target_card not in state.player(target_id).hand:
            raise InvalidAbility("exchange cards must be in selected hands")
        return (
            _move(actor_card, Zone.HAND, actor_id, Zone.HAND, target_id),
            _move(target_card, Zone.HAND, target_id, Zone.HAND, actor_id),
        )
    if ability == "prodigy":
        criminals = tuple(
            player.id
            for player in state.players
            if any(_definition(state, card) == "criminal" for card in player.hand)
        )
        aliens = {
            player.id
            for player in state.players
            if any(_definition(state, card) == "alien" for card in player.hand)
        }
        false_signals = set(selections)
        if not false_signals <= aliens:
            raise InvalidAbility("only alien holders may send false signals")
        return (
            PrivateInformationRevealed(
                PrivateReveal(actor_id, "prodigy_signals", (*criminals, *sorted(false_signals)))
            ),
        )
    if ability == "disciplinary_committee":
        if len(selections) != 1 or selections[0] == actor_id:
            raise InvalidAbility("disciplinary committee requires another player")
        target = state.player(selections[0])
        return (
            PrivateInformationRevealed(PrivateReveal(actor_id, "disciplinary_hand", target.hand)),
        )
    if ability == "health_committee":
        if len(selections) != 1:
            raise InvalidAbility("health committee requires one used card")
        card_id = selections[0]
        source = next(
            (
                player.id
                for player in state.players
                if player.id != actor_id and card_id in player.used
            ),
            None,
        )
        if source is None or _definition(state, card_id) == "health_committee":
            raise InvalidAbility("invalid used card recovery")
        return (_move(card_id, Zone.USED, source, Zone.HAND, actor_id),)
    if ability == "lady":
        if len(selections) != 2:
            raise InvalidAbility("lady requires target and returned card")
        target_id, returned_card = selections
        target = state.player(target_id)
        if target_id == actor_id or not target.hand:
            raise InvalidAbility("invalid lady target")
        rng = random.Random(f"{state.seed}:{state.revision}:{ability_card_id}")
        drawn = rng.choice(target.hand)
        available_to_return = {*actor.hand, drawn}
        if returned_card not in available_to_return:
            raise InvalidAbility("returned card is not available")
        events: list[GameEvent] = [
            _move(drawn, Zone.HAND, target_id, Zone.HAND, actor_id),
        ]
        events.append(_move(returned_card, Zone.HAND, actor_id, Zone.HAND, target_id))
        return tuple(events)
    if ability == "library_committee":
        return (
            PrivateInformationRevealed(
                PrivateReveal(actor_id, "library_embalming", state.embalming)
            ),
        )
    if ability == "newspaper_club":
        eligible = tuple(player for player in state.players if not player.finished)
        if len(eligible) < 2 or len(selections) != len(eligible):
            raise InvalidAbility("newspaper requires one card per eligible player")
        chosen = dict(zip((player.id for player in eligible), selections, strict=True))
        if any(card not in state.player(player_id).hand for player_id, card in chosen.items()):
            raise InvalidAbility("newspaper selections must be in original hands")
        events = []
        ids = tuple(player.id for player in eligible)
        for index, source_id in enumerate(ids):
            target_id = ids[(index + 1) % len(ids)]
            events.append(_move(chosen[source_id], Zone.HAND, source_id, Zone.HAND, target_id))
        return tuple(events)
    if ability == "go_home_club":
        if len(selections) != 2:
            raise InvalidAbility("go-home club requires hand and embalming cards")
        hand_card, embalming_card = selections
        if hand_card not in actor.hand or embalming_card not in state.embalming:
            raise InvalidAbility("invalid go-home exchange")
        return (
            _move(hand_card, Zone.HAND, actor_id, Zone.EMBALMING, None),
            _move(embalming_card, Zone.EMBALMING, None, Zone.HAND, actor_id),
        )
    raise InvalidAbility(f"unsupported ability {ability!r}")


def resolve_infected_trigger(
    state: GameState,
    trigger_id: str,
    chosen_card_id: str,
) -> tuple[GameEvent, ...]:
    trigger = next(
        (item for item in state.delayed_triggers if item.id == trigger_id),
        None,
    )
    if trigger is None or trigger.kind != "infected_recover":
        raise InvalidAbility("infected trigger not found")
    owner = state.player(trigger.owner_id)
    if trigger.source_card_id not in owner.used:
        return (TriggerRemoved(trigger.id),)
    if chosen_card_id not in state.embalming:
        raise InvalidAbility("chosen card is not in embalming")
    return (
        _move(chosen_card_id, Zone.EMBALMING, None, Zone.HAND, owner.id),
        TriggerRemoved(trigger.id),
    )
