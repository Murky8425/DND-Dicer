import random
import unittest

from initiative_tracker import next_turn, ordered_combatants, roll_initiative


class InitiativeTrackerTests(unittest.TestCase):
    def setUp(self):
        self.combatants = [
            {"id": "slow", "initiative": 8, "order": 0},
            {"id": "first", "initiative": 17, "order": 1},
            {"id": "tied", "initiative": 17, "order": 2},
        ]

    def test_rolls_d20_and_adds_modifier(self):
        self.assertEqual(roll_initiative(4, random.Random(2)), 6)

    def test_combatants_are_sorted_descending_and_ties_preserve_order(self):
        self.assertEqual(
            [combatant["id"] for combatant in ordered_combatants(self.combatants)],
            ["first", "tied", "slow"],
        )

    def test_turn_advances_and_round_increments_after_last_combatant(self):
        self.assertEqual(next_turn(self.combatants, "first", 1), ("tied", 1))
        self.assertEqual(next_turn(self.combatants, "slow", 1), ("first", 2))

    def test_turn_starts_at_first_combatant_and_handles_empty_list(self):
        self.assertEqual(next_turn(self.combatants, None, 1), ("first", 1))
        self.assertEqual(next_turn([], None, 0), (None, 1))


if __name__ == "__main__":
    unittest.main()
