"""
Unit tests for AST-based algorithm recognition.
File: test_recognizer.py
"""

import unittest
from recognizer import recognize_algorithm
from presets_data import ALGORITHM_PRESETS


class TestAlgorithmRecognizer(unittest.TestCase):
    """
    Tests static AST recognition against common algorithm families and presets.
    """

    def test_bubble_sort_recognition(self):
        code = """
arr = [64, 34, 25, 12, 22]
n = len(arr)
for i in range(n):
    for j in range(0, n - i - 1):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
        res = recognize_algorithm(code)
        self.assertEqual(res["category"], "sorting")
        self.assertEqual(res["algorithm"], "bubble_sort")
        self.assertGreaterEqual(res["confidence"], 0.8)

    def test_binary_search_recognition(self):
        code = """
arr = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
target = 23
low = 0
high = len(arr) - 1
while low <= high:
    mid = (low + high) // 2
    if arr[mid] == target:
        break
    elif arr[mid] < target:
        low = mid + 1
    else:
        high = mid - 1
"""
        res = recognize_algorithm(code)
        self.assertEqual(res["category"], "searching")
        self.assertEqual(res["algorithm"], "binary_search")
        self.assertGreaterEqual(res["confidence"], 0.8)

    def test_matrix_traversal_recognition(self):
        code = """
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
for r in range(len(matrix)):
    for c in range(len(matrix[0])):
        val = matrix[r][c]
"""
        res = recognize_algorithm(code)
        self.assertEqual(res["category"], "matrix")
        self.assertGreaterEqual(res["confidence"], 0.8)

    def test_recursion_recognition(self):
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
result = factorial(5)
"""
        res = recognize_algorithm(code)
        self.assertEqual(res["category"], "recursion")
        self.assertGreaterEqual(res["confidence"], 0.8)

    def test_generic_fallback(self):
        code = """
x = 10
y = 20
z = x + y
print(z)
"""
        res = recognize_algorithm(code)
        self.assertEqual(res["category"], "generic")
        self.assertEqual(res["confidence"], 0.0)

    def test_syntax_error_returns_generic(self):
        code = "def foo(:"
        res = recognize_algorithm(code)
        self.assertEqual(res["category"], "generic")
        self.assertEqual(res["confidence"], 0.0)

    def test_presets_recognition(self):
        # All 25 presets should produce valid dictionaries
        for pid, pdata in ALGORITHM_PRESETS.items():
            res = recognize_algorithm(pdata["code"])
            self.assertIn("algorithm", res)
            self.assertIn("category", res)
            self.assertIn("confidence", res)
            self.assertIn("visualization", res)


if __name__ == "__main__":
    unittest.main()
