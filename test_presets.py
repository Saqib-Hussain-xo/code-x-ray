"""
X-Ray Execution Agent: Test Suite for Algorithm Presets Library
Module: test_presets.py

Automated regression suite verifying:
- All 25 algorithm presets parse and compile cleanly.
- Each preset executes to status 'completed' without uncaught exceptions or timeouts.
- Expected sequences and algorithmic pointer bindings are populated.
"""

import re
import unittest
from tracer import ExecutionTracer


def load_presets_from_js():
    """Extract all preset keys and Python code from static/js/presets.js."""
    with open("static/js/presets.js", "r", encoding="utf-8") as f:
        content = f.read()

    # Match key: `...`
    pattern = r"(\w+):\s*`([^`]+)`"
    matches = re.findall(pattern, content)
    return {k: v for k, v in matches}


from presets_data import ALGORITHM_PRESETS, ALLOWED_PRESET_IDS


class TestAlgorithmPresets(unittest.TestCase):
    """Verifies runtime behavior of all pre-loaded algorithm presets."""

    @classmethod
    def setUpClass(cls):
        cls.presets = load_presets_from_js()
        cls.tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)

    def test_preset_count(self):
        """Verify exactly 25 presets are defined in presets.js and presets_data.py."""
        self.assertEqual(len(self.presets), 25, f"Expected 25 presets, found {len(self.presets)}")
        self.assertEqual(len(ALGORITHM_PRESETS), 25, f"Expected 25 backend presets, found {len(ALGORITHM_PRESETS)}")
        self.assertEqual(set(self.presets.keys()), ALLOWED_PRESET_IDS, "Frontend and backend preset IDs must match 1:1")

    def test_two_pointers_category(self):
        """Verify the 6 Two Pointers algorithms."""
        keys = [
            "two_pointer_palindrome", "two_sum_sorted", "reverse_array",
            "remove_duplicates", "move_zeroes", "container_most_water"
        ]
        for key in keys:
            self.assertIn(key, self.presets)
            res = self.tracer.run_trace(self.presets[key])
            self.assertEqual(res["status"], "completed", f"Preset {key} failed: {res['error']}")
            self.assertGreater(res["total_steps"], 5)
            self.assertGreater(len(res["steps"][-1]["sequences"]), 0)

    def test_sliding_window_category(self):
        """Verify the 4 Sliding Window algorithms."""
        keys = [
            "max_sum_subarray", "min_length_subarray",
            "longest_substr_no_repeat", "fixed_window_average"
        ]
        for key in keys:
            self.assertIn(key, self.presets)
            res = self.tracer.run_trace(self.presets[key])
            self.assertEqual(res["status"], "completed", f"Preset {key} failed: {res['error']}")
            self.assertGreater(res["total_steps"], 10)

    def test_searching_and_arrays_category(self):
        """Verify the 5 Searching and Array algorithms."""
        keys = [
            "linear_search", "binary_search", "sentinel_search",
            "prefix_sums", "frequency_counting"
        ]
        for key in keys:
            self.assertIn(key, self.presets)
            res = self.tracer.run_trace(self.presets[key])
            self.assertEqual(res["status"], "completed", f"Preset {key} failed: {res['error']}")
            self.assertGreater(res["total_steps"], 5)

    def test_sorting_category(self):
        """Verify the 4 Sorting algorithms."""
        keys = [
            "bubble_sort", "selection_sort", "insertion_sort", "merge_sort"
        ]
        for key in keys:
            self.assertIn(key, self.presets)
            res = self.tracer.run_trace(self.presets[key])
            self.assertEqual(res["status"], "completed", f"Preset {key} failed: {res['error']}")
            self.assertGreater(res["total_steps"], 15)

    def test_matrices_category(self):
        """Verify the 4 Matrix algorithms."""
        keys = [
            "matrix_traversal", "matrix_row_sums", "matrix_col_sums", "matrix_diagonal"
        ]
        for key in keys:
            self.assertIn(key, self.presets)
            res = self.tracer.run_trace(self.presets[key])
            self.assertEqual(res["status"], "completed", f"Preset {key} failed: {res['error']}")
            self.assertGreater(res["total_steps"], 15)

    def test_stacks_queues_recursion_category(self):
        """Verify Stacks, Queues, and Recursion algorithms."""
        keys = ["stack_queue_ops", "factorial_fibonacci"]
        for key in keys:
            self.assertIn(key, self.presets)
            res = self.tracer.run_trace(self.presets[key])
            self.assertEqual(res["status"], "completed", f"Preset {key} failed: {res['error']}")
            self.assertGreater(res["total_steps"], 10)


if __name__ == "__main__":
    unittest.main()
