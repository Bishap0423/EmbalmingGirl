from collections import defaultdict
from dataclasses import replace

import pytest
from embalming_game import score_game, start_game
from embalming_game.models import GameState, Phase, PlayerState
from embalming_game.reducer import reduce_event


def _scoring_state(
    roles: tuple[str, ...],
    embalming: tuple[str, ...] = (),
    suspicion: dict[int, tuple[str, ...]] | None = None,
) -> GameState:
    state, _ = start_game("score", ("a", "b", "c", "d", "e"), seed=31)
    instances: dict[str, list[str]] = defaultdict(list)
    for card in state.cards:
        instances[card.definition_id].append(card.id)

    def take(definition_id: str) -> str:
        return instances[definition_id].pop()

    hands = tuple(take(role) for role in roles)
    embalming_cards = tuple(take(role) for role in embalming)
    suspicion = suspicion or {}
    players = tuple(
        PlayerState(
            id=player.id,
            seat=player.seat,
            hand=(hands[index],),
            suspicion=tuple(take(role) for role in suspicion.get(index, ())),
            finished=True,
        )
        for index, player in enumerate(state.players)
    )
    return replace(
        state,
        phase=Phase.SCORING,
        active_player_id=None,
        players=players,
        embalming=embalming_cards,
    )


@pytest.mark.parametrize(
    ("state", "winners", "priority"),
    [
        (
            _scoring_state(
                ("alien", "infected", "criminal", "lady", "go_home_club"),
                suspicion={0: ("student_council_president",)},
            ),
            ("a",),
            1,
        ),
        (
            _scoring_state(("accomplice", "infected", "criminal", "lady", "go_home_club")),
            ("b",),
            2,
        ),
        (
            _scoring_state(
                (
                    "criminal",
                    "accomplice",
                    "accomplice",
                    "infected",
                    "go_home_club",
                ),
                ("student_council_president", "class_representative", "prodigy"),
            ),
            ("a", "b", "c"),
            3,
        ),
        (
            _scoring_state(
                (
                    "library_committee",
                    "newspaper_club",
                    "health_committee",
                    "infected",
                    "go_home_club",
                ),
                ("student_council_president", "class_representative", "prodigy"),
            ),
            ("a", "b", "c"),
            4,
        ),
        (
            _scoring_state(
                ("alien", "infected", "accomplice", "go_home_club", "go_home_club"),
                ("student_council_president", "class_representative", "prodigy"),
            ),
            ("d", "e"),
            5,
        ),
    ],
)
def test_victory_priority_matrix(
    state: GameState,
    winners: tuple[str, ...],
    priority: int,
) -> None:
    event = score_game(state)[0]

    assert event.result.winner_ids == winners
    assert event.result.winning_priority == priority
    assert not event.result.annihilation


def test_annihilation_when_no_role_condition_is_met() -> None:
    state = _scoring_state(
        ("alien", "infected", "accomplice", "accomplice", "accomplice"),
        ("student_council_president", "class_representative", "prodigy"),
    )

    event = score_game(state)[0]

    assert event.result.winner_ids == ()
    assert event.result.winning_priority is None
    assert event.result.annihilation


def test_suspicion_is_floored_at_zero_and_equal_totals_imprison_nobody() -> None:
    state = _scoring_state(
        (
            "criminal",
            "infected",
            "accomplice",
            "go_home_club",
            "go_home_club",
        ),
        suspicion={0: ("alien",)},
    )

    event = score_game(state)[0]

    assert event.result.suspicion_totals == (
        ("a", 0),
        ("b", 0),
        ("c", 0),
        ("d", 0),
        ("e", 0),
    )
    assert event.result.imprisoned_player_ids == ()


def test_scoring_event_finishes_game() -> None:
    state = _scoring_state(("alien", "infected", "accomplice", "go_home_club", "go_home_club"))

    finished = reduce_event(state, score_game(state)[0])

    assert finished.phase is Phase.FINISHED
    assert finished.result is not None
