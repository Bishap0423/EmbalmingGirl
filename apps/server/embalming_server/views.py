from __future__ import annotations

from dataclasses import asdict
from typing import Any

from embalming_game.catalog import load_card_catalog
from embalming_game.models import GameState


def project_game(state: GameState, viewer_id: str) -> dict[str, Any]:
    definitions = {card.id: card for card in load_card_catalog()}

    def visible_card(card_id: str) -> dict[str, Any]:
        instance = state.card(card_id)
        definition = definitions[instance.definition_id]
        return {
            "instance_id": instance.id,
            "definition_id": definition.id,
            "name": definition.name_zh,
            "mp": definition.mp,
            "art_key": definition.art_key,
        }

    players = []
    for player in state.players:
        own = player.id == viewer_id
        players.append(
            {
                "id": player.id,
                "seat": player.seat,
                "finished": player.finished,
                "hand_count": len(player.hand),
                "hand": [visible_card(card) for card in player.hand] if own else None,
                "used": [visible_card(card) for card in player.used],
                "suspicion_count": len(player.suspicion),
            }
        )

    pending = state.pending_decision
    pending_view = None
    if pending is not None and viewer_id in pending.responders:
        pending_view = {
            "id": pending.id,
            "kind": pending.kind,
            "ability_card_id": pending.ability_card_id,
            "context": dict(pending.context),
            "submitted": any(player_id == viewer_id for player_id, _ in pending.submissions),
        }

    private_reveals = [
        {"reason": reveal.reason, "values": reveal.values}
        for reveal in state.private_reveals
        if reveal.viewer_id == viewer_id
    ]
    return {
        "id": state.id,
        "ruleset_version": state.ruleset_version,
        "revision": state.revision,
        "phase": state.phase.value,
        "target": state.target,
        "active_player_id": state.active_player_id,
        "players": players,
        "embalming_count": len(state.embalming),
        "pending_decision": pending_view,
        "private_reveals": private_reveals,
        "result": asdict(state.result) if state.result is not None else None,
    }
