from __future__ import annotations

from collections import Counter

from embalming_game.catalog import CardDefinition, load_card_catalog

REMOVALS_BY_PLAYER_COUNT: dict[int, Counter[str]] = {
    3: Counter(
        {
            "library_committee": 1,
            "accomplice": 1,
            "prodigy": 1,
            "disciplinary_committee": 1,
            "lady": 1,
            "newspaper_club": 1,
            "go_home_club": 1,
        }
    ),
    4: Counter({"library_committee": 1}),
    5: Counter(),
    6: Counter({"library_committee": 1}),
}

HAND_SIZE_BY_PLAYER_COUNT = {3: 6, 4: 6, 5: 5, 6: 4}


def build_deck(
    player_count: int,
    catalog: tuple[CardDefinition, ...] | None = None,
) -> tuple[str, ...]:
    if player_count not in REMOVALS_BY_PLAYER_COUNT:
        raise ValueError("player_count must be between 3 and 6")

    definitions = catalog or load_card_catalog()
    counts = Counter({card.id: card.copies for card in definitions})
    counts.subtract(REMOVALS_BY_PLAYER_COUNT[player_count])

    if any(count < 0 for count in counts.values()):
        raise ValueError("deck removal exceeds available cards")

    deck = tuple(card.id for card in definitions for _ in range(counts[card.id]))
    expected_size = player_count * HAND_SIZE_BY_PLAYER_COUNT[player_count]
    if len(deck) != expected_size:
        raise ValueError(f"expected {expected_size} cards, got {len(deck)}")
    return deck
