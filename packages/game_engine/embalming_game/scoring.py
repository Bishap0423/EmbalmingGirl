from __future__ import annotations

from embalming_game.catalog import load_card_catalog
from embalming_game.events import GameScored
from embalming_game.models import GameResult, GameState, Phase

SUCCESS_STUDENT_ROLES = {
    "student_council_president",
    "class_representative",
    "prodigy",
    "disciplinary_committee",
    "health_committee",
    "library_committee",
    "newspaper_club",
}


def _final_roles(state: GameState) -> dict[str, str]:
    roles: dict[str, str] = {}
    for player in state.players:
        if len(player.hand) != 1:
            raise ValueError("every player must have exactly one final hand card")
        roles[player.id] = state.card(player.hand[0]).definition_id
    return roles


def score_game(state: GameState) -> tuple[GameScored, ...]:
    if state.phase is not Phase.SCORING:
        raise ValueError("game is not in scoring phase")

    mp = {card.id: card.mp for card in load_card_catalog()}
    embalming_total = sum(mp[state.card(card_id).definition_id] for card_id in state.embalming)
    embalming_succeeded = embalming_total >= state.target

    suspicion_totals = tuple(
        (
            player.id,
            max(
                0,
                sum(mp[state.card(card_id).definition_id] for card_id in player.suspicion),
            ),
        )
        for player in state.players
    )
    values = tuple(total for _, total in suspicion_totals)
    if len(set(values)) == 1:
        imprisoned: tuple[str, ...] = ()
    else:
        highest = max(values)
        imprisoned = tuple(player_id for player_id, total in suspicion_totals if total == highest)

    roles = _final_roles(state)
    imprisoned_set = set(imprisoned)
    winners: tuple[str, ...] = ()
    priority: int | None = None

    priority_one = tuple(
        player_id
        for player_id, role in roles.items()
        if role == "alien" and player_id in imprisoned_set
    )
    if priority_one:
        winners, priority = priority_one, 1
    elif not embalming_succeeded:
        priority_two = tuple(player_id for player_id, role in roles.items() if role == "infected")
        if priority_two:
            winners, priority = priority_two, 2

    if not winners:
        criminal_winners = tuple(
            player_id
            for player_id, role in roles.items()
            if role == "criminal" and player_id not in imprisoned_set
        )
        if criminal_winners:
            accomplices = tuple(
                player_id for player_id, role in roles.items() if role == "accomplice"
            )
            winners, priority = (*criminal_winners, *accomplices), 3

    if not winners:
        priority_four = tuple(
            player_id
            for player_id, role in roles.items()
            if (role in SUCCESS_STUDENT_ROLES and embalming_succeeded)
            or (role == "lady" and player_id not in imprisoned_set)
        )
        if priority_four:
            winners, priority = priority_four, 4

    if not winners:
        priority_five = tuple(
            player_id for player_id, role in roles.items() if role == "go_home_club"
        )
        if priority_five:
            winners, priority = priority_five, 5

    result = GameResult(
        embalming_total=embalming_total,
        embalming_succeeded=embalming_succeeded,
        suspicion_totals=suspicion_totals,
        imprisoned_player_ids=imprisoned,
        winner_ids=winners,
        winning_priority=priority,
        annihilation=not winners,
    )
    return (GameScored(result),)
