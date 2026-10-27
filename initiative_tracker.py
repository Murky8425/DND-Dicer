"""Small helpers for turn order in the initiative tracker."""

import random
from collections.abc import Sequence
from typing import Any


def roll_initiative(modifier: int, rng: random.Random | None = None) -> int:
    """Roll a d20 and add the combatant's initiative modifier."""
    roller = rng or random
    return roller.randint(1, 20) + modifier


def ordered_combatants(
    combatants: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sort combatants by initiative, preserving insertion order for ties."""
    return sorted(
        combatants,
        key=lambda combatant: (-combatant["initiative"], combatant["order"]),
    )


def next_turn(
    combatants: Sequence[dict[str, Any]],
    active_id: str | None,
    round_number: int,
) -> tuple[str | None, int]:
    """Return the next combatant and round number in initiative order."""
    ordered = ordered_combatants(combatants)
    if not ordered:
        return None, max(1, round_number)

    active_index = next(
        (
            index
            for index, combatant in enumerate(ordered)
            if combatant["id"] == active_id
        ),
        -1,
    )
    next_index = active_index + 1
    if next_index >= len(ordered):
        return ordered[0]["id"], max(1, round_number) + 1
    return ordered[next_index]["id"], max(1, round_number)
