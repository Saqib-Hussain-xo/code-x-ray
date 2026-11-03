"""
Unit tests for the Error Detective Diagnostics Engine (diagnostics.py).
"""

import unittest
from diagnostics import diagnose_error


class TestErrorDetective(unittest.TestCase):
    def test_index_error_diagnosis(self):
        err = {"type": "IndexError", "message": "list index out of range", "line_no": 5}
        code = "arr = [1, 2, 3]\nfor i in range(10):\n    x = arr[i]"
        last_step = {"sequences": {"arr": {"length": 3}}}
        diag = diagnose_error(err, code, last_step)

        self.assertIn("Index Out of Bounds", diag["title"])
        self.assertIn("0-based indexing", diag["suggestion"])
        self.assertIn("length 3", diag["explanation"])

    def test_type_error_unsupported_comparison(self):
        err = {"type": "TypeError", "message": "'<' not supported between instances of 'str' and 'int'", "line_no": 3}
        code = "a = 'hello'\nb = 5\nif a < b: pass"
        diag = diagnose_error(err, code)

        self.assertIn("Incompatible Types", diag["title"])
        self.assertIn("share the same data type", diag["suggestion"])

    def test_zero_division_diagnosis(self):
        err = {"type": "ZeroDivisionError", "message": "division by zero", "line_no": 4}
        code = "x = 10\ny = 0\nz = x / y"
        diag = diagnose_error(err, code)

        self.assertIn("Division by Zero", diag["title"])
        self.assertIn("divisor of 0", diag["explanation"])

    def test_recursion_error_diagnosis(self):
        err = {"type": "RecursionError", "message": "maximum recursion depth exceeded", "line_no": 2}
        code = "def f(): f()\nf()"
        diag = diagnose_error(err, code)

        self.assertIn("Infinite Recursion", diag["title"])
        self.assertIn("base case", diag["suggestion"])

    def test_trace_limit_exceeded_diagnosis(self):
        err = {"type": "TraceLimitExceeded", "message": "Execution exceeded maximum step limit", "line_no": 3}
        code = "while True:\n    pass"
        diag = diagnose_error(err, code)

        self.assertIn("Loop Step Limit", diag["title"])
        self.assertIn("infinite while loop", diag["explanation"])

    def test_name_error_diagnosis(self):
        err = {"type": "NameError", "message": "name 'countr' is not defined", "line_no": 1}
        code = "countr += 1"
        diag = diagnose_error(err, code)

        self.assertIn("NameError: countr", diag["title"])
        self.assertIn("spelling typo", diag["suggestion"])


if __name__ == "__main__":
    unittest.main()
