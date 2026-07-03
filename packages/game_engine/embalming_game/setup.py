from __future__ import annotations

import random

from embalming_game.catalog import load_card_catalog
from embalming_game.deck import build_deck
from embalming_game.events import GameStarted
from embalming_game.models import CardInstance, GameState, PlayerState
from embalming_game.reducer import reduce_event

RULESET_VERSION = "2020-06-30-project-ruling-1"


def start_game(
    game_id: str,
    player_ids: tuple[str, ...],
    seed: int,
) -> tuple[GameState, GameStarted]:
    if len(player_ids) != len(set(player_ids)):
        raise ValueError("player IDs must be unique")

    definitions = load_card_catalog()
    definition_ids = list(build_deck(len(player_ids), definitions))
    cards = tuple(
        CardInstance(id=f"card_{index:02d}", definition_id=definition_id)
        for index, definition_id in enumerate(definition_ids, start=1)
    )
    shuffled_ids = [card.id for card in cards]
    random.Random(seed).shuffle(shuffled_ids)

    hands = tuple(tuple(shuffled_ids[seat :: len(player_ids)]) for seat in range(len(player_ids)))
    players = tuple(
        PlayerState(id=player_id, seat=seat, hand=hands[seat])
        for seat, player_id in enumerate(player_ids)
    )
    president_instance = next(
        card.id for card in cards if card.definition_id == "student_council_president"
    )
    active_player_id = next(player.id for player in players if president_instance in player.hand)
    event = GameStarted(
        game_id=game_id,
        ruleset_version=RULESET_VERSION,
        seed=seed,
        target=12 - len(player_ids),
        player_order=player_ids,
        players=players,
        cards=cards,
        active_player_id=active_player_id,
    )
    return reduce_event(None, event), event
