import random
import unittest

from initiative_tracker import next_turn, ordered_combatants, roll_initiative


# Diese Proben schauen, ob Würfel und Zugreihenfolge stimmen.
class InitiativeTrackerTests(unittest.TestCase):
    def setUp(self):
        self.combatants = [
            {"id": "slow", "initiative": 8, "order": 0},
            {"id": "first", "initiative": 17, "order": 1},
            {"id": "tied", "initiative": 17, "order": 2},
        ]

    # Der W20-Wurf bekommt den Bonus dazu.
    def test_rolls_d20_and_adds_modifier(self):
        self.assertEqual(roll_initiative(4, random.Random(2)), 6)

    # Höhere Zahlen sind zuerst dran. Bei Gleichstand bleibt die Reihenfolge gleich.
    def test_combatants_are_sorted_descending_and_ties_preserve_order(self):
        self.assertEqual(
            [combatant["id"] for combatant in ordered_combatants(self.combatants)],
            ["first", "tied", "slow"],
        )

    # Nach dem letzten Zug startet die nächste Runde.
    def test_turn_advances_and_round_increments_after_last_combatant(self):
        self.assertEqual(next_turn(self.combatants, "first", 1), ("tied", 1))
        self.assertEqual(next_turn(self.combatants, "slow", 1), ("first", 2))

    # Prüft den Start der Runde und den Fall, dass niemand eingetragen ist.
    def test_turn_starts_at_first_combatant_and_handles_empty_list(self):
        self.assertEqual(next_turn(self.combatants, None, 1), ("first", 1))
        self.assertEqual(next_turn([], None, 0), (None, 1))


if __name__ == "__main__":
    unittest.main()
