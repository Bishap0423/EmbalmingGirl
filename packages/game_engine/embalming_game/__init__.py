"""Authoritative game engine package."""

from embalming_game.catalog import CardDefinition, load_card_catalog
from embalming_game.deck import build_deck

__all__ = ["CardDefinition", "build_deck", "load_card_catalog"]
