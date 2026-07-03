"""Authoritative game engine package."""

from embalming_game.catalog import CardDefinition, load_card_catalog
from embalming_game.commands import PlaySpecial, PlaySuspicion, PlayToEmbalming
from embalming_game.deck import build_deck
from embalming_game.rules import InvalidCommand, execute
from embalming_game.setup import start_game

__all__ = [
    "CardDefinition",
    "InvalidCommand",
    "PlaySpecial",
    "PlaySuspicion",
    "PlayToEmbalming",
    "build_deck",
    "execute",
    "load_card_catalog",
    "start_game",
]
