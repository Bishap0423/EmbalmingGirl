"""Authoritative game engine package."""

from embalming_game.abilities import InvalidAbility, resolve_ability, resolve_infected_trigger
from embalming_game.catalog import CardDefinition, load_card_catalog
from embalming_game.commands import PlaySpecial, PlaySuspicion, PlayToEmbalming
from embalming_game.deck import build_deck
from embalming_game.invariants import assert_state_invariants
from embalming_game.rules import InvalidCommand, execute
from embalming_game.scoring import score_game
from embalming_game.serialization import event_to_json, state_fingerprint
from embalming_game.setup import start_game

__all__ = [
    "CardDefinition",
    "InvalidCommand",
    "InvalidAbility",
    "PlaySpecial",
    "PlaySuspicion",
    "PlayToEmbalming",
    "build_deck",
    "assert_state_invariants",
    "execute",
    "event_to_json",
    "load_card_catalog",
    "resolve_ability",
    "resolve_infected_trigger",
    "score_game",
    "start_game",
    "state_fingerprint",
]
