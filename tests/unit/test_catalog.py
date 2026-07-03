from collections import Counter

import pytest
from embalming_game import build_deck, load_card_catalog
from embalming_game.deck import HAND_SIZE_BY_PLAYER_COUNT


def test_standard_catalog_contains_13_types_and_25_cards() -> None:
    catalog = load_card_catalog()

    assert len(catalog) == 13
    assert sum(card.copies for card in catalog) == 25
    assert len({card.id for card in catalog}) == len(catalog)


@pytest.mark.parametrize("player_count", [3, 4, 5, 6])
def test_deck_is_evenly_dealt_for_supported_player_counts(player_count: int) -> None:
    deck = build_deck(player_count)

    assert len(deck) == player_count * HAND_SIZE_BY_PLAYER_COUNT[player_count]
    assert deck.count("student_council_president") == 1
    assert deck.count("criminal") == 1


def test_three_player_deck_uses_official_removals() -> None:
    full_deck = Counter(build_deck(5))
    three_player_deck = Counter(build_deck(3))
    removed = full_deck - three_player_deck

    assert removed == Counter(
        {
            "library_committee": 1,
            "accomplice": 1,
            "prodigy": 1,
            "disciplinary_committee": 1,
            "lady": 1,
            "newspaper_club": 1,
            "go_home_club": 1,
        }
    )


def test_infected_ability_records_free_choice_project_ruling() -> None:
    infected = next(card for card in load_card_catalog() if card.id == "infected")

    assert infected.ability == "recover_chosen_embalming_card_next_turn"


def test_unsupported_player_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="between 3 and 6"):
        build_deck(2)
