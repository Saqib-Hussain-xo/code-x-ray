"""
Unit tests for the Step-by-Step Explanation Engine (explainer.py).
"""

import unittest
from explainer import generate_step_explanation


class TestStepExplainer(unittest.TestCase):
    def test_search_found_explanation(self):
        step = {
            "line_no": 12,
            "events": [{"type": "found", "target": "arr", "index": 3, "value": 42}],
            "locals_snapshot": {"target": 42, "mid": 3}
        }
        exp = generate_step_explanation(step)
        self.assertIn("Found target value 42 at index 3.", exp)

    def test_search_range_explanation(self):
        step = {
            "line_no": 7,
            "events": [{"type": "search_range", "target": "arr", "low": 0, "mid": 4, "high": 9}],
            "locals_snapshot": {"low": 0, "mid": 4, "high": 9}
        }
        exp = generate_step_explanation(step)
        self.assertIn("Narrowing search range to [0..9]", exp)
        self.assertIn("middle index 4", exp)

    def test_matrix_access_explanation(self):
        step = {
            "line_no": 5,
            "events": [{"type": "matrix_access", "target": "grid", "row": 1, "col": 2, "value": 99}],
            "locals_snapshot": {"r": 1, "c": 2}
        }
        exp = generate_step_explanation(step)
        self.assertIn("Accessing cell grid[1][2] (value: 99).", exp)

    def test_swap_explanation(self):
        step = {
            "line_no": 10,
            "events": [{"type": "swap", "target": "nums", "indices": [0, 1], "from_values": [5, 2], "to_values": [2, 5]}],
            "locals_snapshot": {"nums": [2, 5]}
        }
        exp = generate_step_explanation(step)
        self.assertIn("Swapped nums[0] (5) with nums[1] (2).", exp)

    def test_variable_mutation_explanation(self):
        prev = {"locals_snapshot": {"counter": 0}}
        curr = {"line_no": 4, "locals_snapshot": {"counter": 1}}
        exp = generate_step_explanation(curr, prev)
        self.assertIn("Updated 'counter' from 0 to 1.", exp)

    def test_variable_initialization_explanation(self):
        prev = {"locals_snapshot": {}}
        curr = {"line_no": 2, "locals_snapshot": {"total": 100}}
        exp = generate_step_explanation(curr, prev)
        self.assertIn("Initialized variable 'total' to 100.", exp)

    def test_pointer_movement_explanation(self):
        prev = {"locals_snapshot": {}, "pointers": [{"name": "left", "value": 0}]}
        curr = {"line_no": 8, "locals_snapshot": {}, "pointers": [{"name": "left", "value": 1}]}
        exp = generate_step_explanation(curr, prev)
        self.assertIn("Moved pointer 'left' from index 0 to 1.", exp)

    def test_fallback_explanation(self):
        step = {"line_no": 15, "locals_snapshot": {}}
        exp = generate_step_explanation(step)
        self.assertEqual("Executed line 15.", exp)


if __name__ == "__main__":
    unittest.main()
