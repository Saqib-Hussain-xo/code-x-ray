"""
X-Ray Execution Agent: Test Suite for Runtime Tracer Engine
Module: test_tracer.py

Verifies the deterministic interception engine, dual loop guard, pointer heuristics,
and error handling across canonical algorithmic patterns and edge cases.
"""

import unittest
from tracer import ExecutionTracer


class TestExecutionTracer(unittest.TestCase):
    """
    Test suite validating core ExecutionTracer capabilities.
    """

    def setUp(self):
        # Fresh tracer instance for each test
        self.tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)

    def test_snippet_1_two_pointer_palindrome(self):
        """
        Snippet 1: Two-Pointer Palindrome.
        Verifies:
        - Normal execution completion with status 'completed'.
        - Accurate step-by-step state capture.
        - Pointer heuristics detecting 'left' and 'right' bound to 's'.
        - Mutation tracking on 'left' and 'right'.
        - Capture of return value (True).
        """
        code = """
def is_palindrome(s):
    left = 0
    right = len(s) - 1
    while left < right:
        if s[left] != s[right]: return False
        left += 1; right -= 1
    return True
is_palindrome("racecar")
"""
        result = self.tracer.run_trace(code)

        # 1. Verification of status and step counts
        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["error"])
        self.assertGreater(result["total_steps"], 10)

        # 2. Verification of pointer heuristics
        found_left_ptr = False
        found_right_ptr = False
        for step in result["steps"]:
            pointers = step.get("pointers", [])
            for ptr in pointers:
                if ptr["name"] == "left" and ptr["target"] == "s":
                    found_left_ptr = True
                if ptr["name"] == "right" and ptr["target"] == "s":
                    found_right_ptr = True

        self.assertTrue(found_left_ptr, "Failed to detect 'left' pointer bound to sequence 's'")
        self.assertTrue(found_right_ptr, "Failed to detect 'right' pointer bound to sequence 's'")

        # 3. Verification of mutations
        mutated_vars = {mut for step in result["steps"] for mut in step["mutations"]}
        self.assertIn("left", mutated_vars)
        self.assertIn("right", mutated_vars)

        # 4. Verification of return value
        returns = [step for step in result["steps"] if step["event_type"] == "return"]
        self.assertTrue(any(step.get("return_value") is True for step in returns))

    def test_snippet_2_infinite_loop_kill_switch(self):
        """
        Snippet 2: Infinite Loop.
        Verifies:
        - Must trigger the 1,000-step/2.0s kill switch without hanging.
        - Status must be 'step_limit_exceeded'.
        - Error details must be populated.
        - Total steps must be capped at 1,000 steps.
        """
        code = """
counter = 0
while counter >= 0:
    counter += 1
"""
        result = self.tracer.run_trace(code)

        self.assertEqual(result["status"], "step_limit_exceeded")
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["error"]["type"], "TraceLimitExceeded")
        self.assertEqual(result["total_steps"], 1000)

        # In 1000 steps with 2 lines per while-loop iteration, counter increments ~500 times
        last_step = result["steps"][-1]
        self.assertIn("counter", last_step["locals_snapshot"])
        self.assertGreaterEqual(last_step["locals_snapshot"]["counter"], 450)

    def test_snippet_3_nested_array_scope(self):
        """
        Snippet 3: Nested Array Scope.
        Verifies:
        - Multi-dimensional matrix handling.
        - Loop pointers 'i' and 'j' detected and tracked.
        - Correct computation of total sum (10).
        - Status 'completed'.
        """
        code = """
matrix = [[1, 2], [3, 4]]
total = 0
for i in range(len(matrix)):
    for j in range(len(matrix[i])):
        total += matrix[i][j]
"""
        result = self.tracer.run_trace(code)

        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["error"])

        # Verify pointer heuristics detected 'i' and 'j'
        detected_pointers = {ptr["name"] for step in result["steps"] for ptr in step.get("pointers", [])}
        self.assertIn("i", detected_pointers)
        self.assertIn("j", detected_pointers)

        # Verify final computed sum in locals
        final_locals = result["steps"][-1]["locals_snapshot"]
        self.assertEqual(final_locals.get("total"), 10)

    def test_snippet_4_index_out_of_bounds(self):
        """
        Snippet 4: Index Out of Bounds.
        Verifies:
        - Graceful capture of IndexError without server/test crash.
        - Status 'exception'.
        - Error type 'IndexError'.
        - Preceding steps are intact and inspectable.
        """
        code = """
arr = [10, 20, 30]
i = 0
while i <= 3: 
    val = arr[i]
    i += 1
"""
        result = self.tracer.run_trace(code)

        self.assertEqual(result["status"], "exception")
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["error"]["type"], "IndexError")
        self.assertIn("list index out of range", result["error"]["message"])

        # Steps leading up to the error must be fully preserved
        self.assertGreater(result["total_steps"], 5)
        exception_events = [step for step in result["steps"] if step["event_type"] == "exception"]
        self.assertGreaterEqual(len(exception_events), 1)

    def test_syntax_error_handling(self):
        """
        Verifies graceful handling of invalid Python syntax.
        """
        bad_code = "def broken(:"
        result = self.tracer.run_trace(bad_code)
        self.assertEqual(result["status"], "syntax_error")
        self.assertEqual(result["total_steps"], 0)
        self.assertEqual(result["error"]["type"], "SyntaxError")

    def test_stdout_redirection_capture(self):
        """
        Verifies incremental capture of print statements in standard output.
        """
        code = """
print("Alpha")
x = 10
print("Beta")
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")
        self.assertIn("Alpha\nBeta\n", result["stdout"])


    def test_timeout_kill_switch(self):
        """
        Verifies that max_seconds cutoff triggers if execution exceeds time threshold.
        """
        quick_tracer = ExecutionTracer(max_steps=100000, max_seconds=0.05)
        code = """
import time
for _ in range(100):
    time.sleep(0.01)
"""
        result = quick_tracer.run_trace(code)
        self.assertEqual(result["status"], "timeout")
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["error"]["type"], "TraceTimeout")

    def test_stdout_truncation_limit(self):
        """
        Verifies that stdout buffer truncation prevents unbounded memory consumption.
        """
        capped_tracer = ExecutionTracer(max_steps=500, max_seconds=2.0, max_stdout_chars=500)
        code = """
for _ in range(50):
    print("A" * 50)
"""
        result = capped_tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")
        self.assertIn("... [stdout truncated]", result["stdout"])
        self.assertLessEqual(len(result["stdout"]), 600)

    def test_recursion_limit_guard(self):
        """
        Verifies that deep recursion triggers standard RecursionError gracefully without crashing Python.
        """
        code = """
def runaway():
    runaway()
runaway()
"""
        tracer = ExecutionTracer(max_steps=1000, max_seconds=5.0)
        result = tracer.run_trace(code)
        self.assertEqual(result["status"], "exception")
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["error"]["type"], "RecursionError")

    def test_operation_aware_tracing(self):
        """
        Verifies that tracer detects operations: swaps, comparisons, shifts, and mutations.
        """
        code = """
arr = [5, 1, 4]
if arr[0] > arr[1]:
    arr[0], arr[1] = arr[1], arr[0]
arr[2] = 99
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        all_ops = []
        for step in result["steps"]:
            ops = step.get("operations", [])
            all_ops.extend(ops)

        # Check comparison detection
        comparisons = [op for op in all_ops if op.get("type") == "comparison"]
        self.assertTrue(len(comparisons) > 0, "Tracer should detect comparisons on active line")
        self.assertEqual(comparisons[0]["sequence"], "arr")
        self.assertEqual(comparisons[0]["indices"], [0, 1])

        # Check swap detection
        swaps = [op for op in all_ops if op.get("type") == "swap"]
        self.assertTrue(len(swaps) > 0, "Tracer should detect tuple swap between arr[0] and arr[1]")
        self.assertEqual(swaps[0]["sequence"], "arr")
        self.assertEqual(swaps[0]["indices"], [0, 1])
        self.assertEqual(swaps[0]["from_values"], [5, 1])
        self.assertEqual(swaps[0]["to_values"], [1, 5])

        # Check mutation detection
        mutations = [op for op in all_ops if op.get("type") == "mutation"]
        self.assertTrue(len(mutations) > 0, "Tracer should detect mutation on arr[2]")
        self.assertEqual(mutations[0]["sequence"], "arr")
        self.assertEqual(mutations[0]["index"], 2)
        self.assertEqual(mutations[0]["from_value"], 4)
        self.assertEqual(mutations[0]["to_value"], 99)

    def test_2d_matrix_detection_and_events(self):
        """
        Verifies 2D matrix detection and matrix_access event emissions.
        """
        code = """
grid = [
    [10, 20],
    [30, 40]
]
x = grid[0][1]
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")
        self.assertIn("recognition", result)

        final_step = result["steps"][-1]
        seqs = final_step.get("sequences", {})
        self.assertIn("grid", seqs)
        self.assertTrue(seqs["grid"]["is_2d_matrix"])
        self.assertEqual(seqs["grid"]["rows"], 2)
        self.assertEqual(seqs["grid"]["cols"], 2)
        self.assertEqual(seqs["grid"]["matrix_elements"], [[10, 20], [30, 40]])

        all_events = []
        for step in result["steps"]:
            all_events.extend(step.get("events", []))

        matrix_events = [e for e in all_events if e.get("type") == "matrix_access"]
        self.assertTrue(len(matrix_events) > 0, "Should emit matrix_access event")
        self.assertEqual(matrix_events[0]["target"], "grid")
        self.assertEqual(matrix_events[0]["row"], 0)
        self.assertEqual(matrix_events[0]["col"], 1)

    def test_standardized_events_and_searching(self):
        """
        Verifies normalized events for search intervals and target findings.
        """
        code = """
arr = [10, 20, 30, 40]
target = 30
low = 0
high = 3
mid = 2
if arr[mid] == target:
    found = True
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        all_events = []
        for step in result["steps"]:
            all_events.extend(step.get("events", []))

        search_ranges = [e for e in all_events if e.get("type") == "search_range"]
        self.assertTrue(len(search_ranges) > 0, "Should emit search_range event")
        self.assertEqual(search_ranges[0]["target"], "arr")
        self.assertEqual(search_ranges[0]["low"], 0)
        self.assertEqual(search_ranges[0]["high"], 3)

    def test_stdin_input_and_explanations(self):
        """
        Verifies input() handling with stdin_data and step explanations.
        """
        code = """
name = input()
greeting = f"Hello, {name}"
"""
        result = self.tracer.run_trace(code, stdin_data="Alice\n")
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["has_input"])
        self.assertEqual(result["steps"][-1]["locals_snapshot"]["name"], "Alice")
        self.assertEqual(result["steps"][-1]["locals_snapshot"]["greeting"], "Hello, Alice")

        # Verify step explanation presence
        for step in result["steps"]:
            self.assertIn("explanation", step)
            self.assertIsInstance(step["explanation"], str)
            self.assertTrue(len(step["explanation"]) > 0)

    def test_call_stack_and_recursion_tracking(self):
        """
        Verifies call stack tracking and recursion info on recursive calls.
        """
        code = """
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)

res = fact(3)
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        # Find steps inside fact()
        steps_in_fact = [s for s in result["steps"] if any(f["func_name"] == "fact" for f in s.get("call_stack", []))]
        self.assertTrue(len(steps_in_fact) > 0, "Should record frames for fact()")

        # Verify max recursion depth reached >= 3
        max_depth = max(s["recursion_info"]["depth"] for s in result["steps"])
        self.assertGreaterEqual(max_depth, 3)

        # Verify is_recursive flag was set during recursive descent
        recursive_steps = [s for s in result["steps"] if s["recursion_info"]["is_recursive"]]
        self.assertTrue(len(recursive_steps) > 0)

    def test_error_diagnosis_attachment(self):
        """
        Verifies diagnosis payload is attached to runtime errors.
        """
        code = """
items = [1, 2]
bad = items[99]
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "exception")
        self.assertIn("diagnosis", result["error"])
        diag = result["error"]["diagnosis"]
        self.assertIn("Index Out of Bounds", diag["title"])
        self.assertIn("0-based indexing", diag["suggestion"])

    def test_runtime_operation_counters(self):
        """
        Verifies runtime operation counters (comparisons, swaps, loop iterations, assignments).
        """
        code = """
nums = [4, 2, 1]
n = len(nums)
for i in range(n):
    for j in range(n - 1):
        if nums[j] > nums[j + 1]:
            nums[j], nums[j + 1] = nums[j + 1], nums[j]
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")
        self.assertIn("operation_metrics", result)
        metrics = result["operation_metrics"]

        # Loop iterations, comparisons, swaps, assignments should be detected and > 0
        self.assertGreater(metrics["loop_iterations"], 0)
        self.assertGreater(metrics["comparisons"], 0)
        self.assertGreater(metrics["swaps"], 0)
        self.assertGreater(metrics["assignments"], 0)
        self.assertGreater(metrics["total"], 0)

        # Step-level cumulative counters should be monotonically increasing
        final_step = result["steps"][-1]
        self.assertIn("cumulative_operations", final_step)
        step_cum = final_step["cumulative_operations"]
        self.assertEqual(step_cum["swaps"], metrics["swaps"])
        self.assertEqual(step_cum["comparisons"], metrics["comparisons"])


if __name__ == "__main__":
    unittest.main()
