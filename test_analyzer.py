"""
Unit tests for Code X-Ray Complexity Analyzer (analyzer.py)
"""

import unittest
from analyzer import analyze_complexity, get_loop_nesting_depth, has_logarithmic_step


class TestComplexityAnalyzer(unittest.TestCase):
    def test_constant_time(self):
        code = "a = 5\nb = 10\nc = a + b"
        res = analyze_complexity(code)
        self.assertEqual(res["estimated_time"], "O(1)")
        self.assertEqual(res["estimated_space"], "O(1)")
        self.assertEqual(res["confidence"], "high")

    def test_linear_time_single_loop(self):
        code = "for x in [1, 2, 3]:\n    print(x)"
        res = analyze_complexity(code)
        self.assertEqual(res["estimated_time"], "O(n)")
        self.assertEqual(res["max_loop_depth"], 1)

    def test_quadratic_time_nested_loops(self):
        code = """
items = [3, 2, 1]
for i in range(len(items)):
    for j in range(len(items)):
        if items[i] < items[j]:
            pass
"""
        res = analyze_complexity(code)
        self.assertEqual(res["estimated_time"], "O(n^2)")
        self.assertEqual(res["max_loop_depth"], 2)

    def test_binary_search_logarithmic_time(self):
        code = """
low = 0
high = 10
while low <= high:
    mid = (low + high) // 2
    low = mid + 1
"""
        res = analyze_complexity(code)
        self.assertEqual(res["estimated_time"], "O(log n)")

    def test_recognized_sorting_family(self):
        code = """
arr = [5, 2, 8]
for i in range(len(arr)):
    for j in range(len(arr) - 1):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
        res = analyze_complexity(code)
        self.assertEqual(res["estimated_time"], "O(n^2)")
        self.assertEqual(res["confidence"], "high")
        self.assertIn("sorting", res["explanation"].lower())

    def test_observed_metrics_inclusion(self):
        code = "for i in range(5): pass"
        metrics = {"comparisons": 0, "swaps": 0, "assignments": 5, "loop_iterations": 5, "total": 10}
        res = analyze_complexity(code, trace_metrics=metrics)
        self.assertIsNotNone(res["observed_metrics"])
        self.assertIn("Single run measured", res["observed_metrics"]["summary_text"])
        self.assertIn("do not prove asymptotic complexity", res["disclaimer"])


if __name__ == "__main__":
    unittest.main()
