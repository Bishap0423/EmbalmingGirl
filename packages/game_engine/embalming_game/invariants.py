from embalming_game.models import GameState, Phase


def assert_state_invariants(state: GameState) -> None:
    known = {card.id for card in state.cards}
    located: list[str] = [*state.embalming]
    for player in state.players:
        located.extend(player.hand)
        located.extend(player.used)
        located.extend(player.suspicion)

    if len(located) != len(set(located)):
        raise AssertionError("a card instance exists in more than one zone")
    if set(located) != known:
        missing = known - set(located)
        unknown = set(located) - known
        raise AssertionError(f"card location mismatch: missing={missing}, unknown={unknown}")
    if state.phase in {Phase.TURN, Phase.RESOLVING} and state.active_player_id is None:
        raise AssertionError("active phase requires an active player")
    if state.phase in {Phase.SCORING, Phase.FINISHED} and state.active_player_id is not None:
        raise AssertionError("terminal phase cannot have an active player")
    if state.pending_decision is not None and state.phase is not Phase.RESOLVING:
        raise AssertionError("pending decision requires resolving phase")
