"""
Unit tests for Code X-Ray Algorithm & Code Comparison Engine (comparison.py)
"""

import unittest
from comparison import compare_algorithms, get_ast_stats


class TestAlgorithmComparison(unittest.TestCase):
    def test_compare_bubble_vs_selection_sort(self):
        code_bubble = """
arr = [4, 2, 1]
n = len(arr)
for i in range(n):
    for j in range(n - 1):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
print(arr)
"""
        code_selection = """
arr = [4, 2, 1]
n = len(arr)
for i in range(n):
    min_idx = i
    for j in range(i + 1, n):
        if arr[j] < arr[min_idx]:
            min_idx = j
    arr[i], arr[min_idx] = arr[min_idx], arr[i]
print(arr)
"""
        res = compare_algorithms(code_bubble, code_selection, name_a="Bubble Sort", name_b="Selection Sort")

        self.assertEqual(res["implementation_a"]["status"], "completed")
        self.assertEqual(res["implementation_b"]["status"], "completed")
        self.assertTrue(res["comparison"]["outputs_match"])
        self.assertEqual(res["implementation_a"]["stdout"], "[1, 2, 4]")
        self.assertEqual(res["implementation_b"]["stdout"], "[1, 2, 4]")

        # Check operations delta
        delta = res["comparison"]["operations_delta"]
        self.assertIn("comparisons", delta)
        self.assertIn("swaps", delta)
        self.assertIn("total", delta)

        # Check structure
        self.assertGreater(res["implementation_a"]["structure"]["node_count"], 0)
        self.assertGreater(res["implementation_b"]["structure"]["node_count"], 0)

        # Check verdict contains qualification
        self.assertIn("do not prove asymptotic superiority", res["comparison"]["verdict"])

    def test_compare_differing_outputs(self):
        code_a = "print('Hello')"
        code_b = "print('World')"
        res = compare_algorithms(code_a, code_b, name_a="Code A", name_b="Code B")
        self.assertFalse(res["comparison"]["outputs_match"])
        self.assertIn("differing outputs", res["comparison"]["verdict"])


if __name__ == "__main__":
    unittest.main()
