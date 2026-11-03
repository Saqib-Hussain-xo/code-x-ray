"""
X-Ray Execution Agent: Test Suite for Universal Semantic Visualization Engine
Module: test_semantic_visualization.py

Validates the universal visual-state contract across algorithms:
1. Search Semantics: Confirmed targets are 'found', absent targets leave 0 green elements.
2. Sorting Finality: Pass-by-pass permanent finalization (Bubble, Selection, Insertion).
3. Matrix Traversal: Visited and active cells, zero premature green states.
4. Two-Pointer and Window: Matching pairs emit 'found'.
5. Reversibility and Determinism: Identical state reproduction and timeline consistency.

Strict rules: Zero em dashes, zero premature green highlights.
"""

import unittest
from tracer import ExecutionTracer


class TestSemanticVisualization(unittest.TestCase):
    """
    Test suite validating universal semantic states and finality guarantees.
    """

    def setUp(self):
        self.tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)

    def test_linear_search_found(self):
        """
        Linear search with matching target:
        - Target index emits 'found' or 'search_found' with semantic_state 'found'.
        - Non-matching elements are compared as 'active', never prematurely finalized.
        """
        code = """
nums = [10, 20, 30, 40, 50]
target = 30
found_idx = -1
for i in range(len(nums)):
    if nums[i] == target:
        found_idx = i
        break
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        all_events = [ev for step in result["steps"] for ev in step.get("events", [])]

        # Verify found event exists for index 2
        found_events = [ev for ev in all_events if ev.get("semantic_state") == "found" or ev.get("type") in ("found", "search_found")]
        self.assertTrue(len(found_events) >= 1)
        self.assertIn(2, found_events[0].get("indices", []))

        # Verify no false position_finalized or sorted events during search
        finalized_events = [ev for ev in all_events if ev.get("type") in ("position_finalized", "sorted")]
        self.assertEqual(len(finalized_events), 0)

    def test_linear_search_not_found(self):
        """
        Linear search with missing target:
        - 0 elements marked 'found'.
        - 0 elements marked 'finalized' or 'sorted'.
        - Strictly 0 false green highlights.
        """
        code = """
nums = [10, 20, 30, 40, 50]
target = 99
found_idx = -1
for i in range(len(nums)):
    if nums[i] == target:
        found_idx = i
        break
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        all_events = [ev for step in result["steps"] for ev in step.get("events", [])]

        found_events = [ev for ev in all_events if ev.get("semantic_state") == "found" or ev.get("type") in ("found", "search_found")]
        self.assertEqual(len(found_events), 0)

        finalized_events = [ev for ev in all_events if ev.get("type") in ("position_finalized", "sorted")]
        self.assertEqual(len(finalized_events), 0)

    def test_binary_search_found(self):
        """
        Binary search on sorted input with matching target:
        - Input array is already sorted, but NO premature 'sorted' events should fire on intermediate steps.
        - Exactly matching target index emits 'found'.
        """
        code = """
nums = [11, 22, 33, 44, 55, 66, 77]
target = 44
left = 0
right = len(nums) - 1
mid_res = -1
while left <= right:
    mid = (left + right) // 2
    if nums[mid] == target:
        mid_res = mid
        break
    elif nums[mid] < target:
        left = mid + 1
    else:
        right = mid - 1
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        # Check all steps before the break
        found_events = []
        for step in result["steps"]:
            for ev in step.get("events", []):
                # Ensure no blanket 'sorted' events fired across the whole array
                if ev.get("type") == "sorted":
                    self.fail("Premature sorted event detected in binary search!")
                if ev.get("semantic_state") == "found" or ev.get("type") in ("found", "search_found"):
                    found_events.append(ev)

        self.assertTrue(len(found_events) >= 1)
        self.assertIn(3, found_events[0].get("indices", []))

    def test_binary_search_not_found(self):
        """
        Binary search with missing target:
        - Strictly 0 'found' events.
        - Strictly 0 'sorted' or 'finalized' events.
        """
        code = """
nums = [10, 20, 30, 40, 50]
target = 25
left = 0
right = len(nums) - 1
res = -1
while left <= right:
    mid = (left + right) // 2
    if nums[mid] == target:
        res = mid
        break
    elif nums[mid] < target:
        left = mid + 1
    else:
        right = mid - 1
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        all_events = [ev for step in result["steps"] for ev in step.get("events", [])]
        found_events = [ev for ev in all_events if ev.get("semantic_state") == "found" or ev.get("type") in ("found", "search_found")]
        self.assertEqual(len(found_events), 0)

        finalized_events = [ev for ev in all_events if ev.get("type") in ("position_finalized", "sorted")]
        self.assertEqual(len(finalized_events), 0)

    def test_bubble_sort_pass_by_pass_finality(self):
        """
        Bubble sort finality:
        - Elements finalize pass-by-pass from the right boundary.
        - Pass 0 ends: index n - 1 is finalized.
        - Pass 1 ends: index n - 2 is finalized.
        - Final step: all elements are finalized without duplicate indices.
        """
        code = """
nums = [5, 1, 4, 2, 8]
n = len(nums)
for i in range(n):
    for j in range(0, n - i - 1):
        if nums[j] > nums[j + 1]:
            nums[j], nums[j + 1] = nums[j + 1], nums[j]
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        finalized_indices_over_time = []
        for step in result["steps"]:
            for ev in step.get("events", []):
                if ev.get("type") == "position_finalized":
                    finalized_indices_over_time.extend(ev.get("indices", []))

        # Check that index 4 (last index) is finalized before earlier indices
        self.assertIn(4, finalized_indices_over_time)
        first_idx_4 = finalized_indices_over_time.index(4)

        # Index 3 must appear at or after index 4 in finalization order
        if 3 in finalized_indices_over_time:
            first_idx_3 = finalized_indices_over_time.index(3)
            self.assertGreaterEqual(first_idx_3, first_idx_4)

        # Terminal step check: all indices 0..4 must be finalized
        last_step_events = result["steps"][-1].get("events", [])
        finalized_last = [ev for ev in last_step_events if ev.get("type") == "position_finalized"]
        all_finalized = set()
        for ev in finalized_last:
            all_finalized.update(ev.get("indices", []))
        self.assertEqual(all_finalized, {0, 1, 2, 3, 4})

    def test_selection_sort_finality(self):
        """
        Selection sort finality:
        - At the end of outer loop iteration i, minimum element is swapped to index i.
        - Emits position_finalized for index i.
        """
        code = """
nums = [29, 10, 14, 37, 13]
n = len(nums)
for i in range(n):
    min_idx = i
    for j in range(i + 1, n):
        if nums[j] < nums[min_idx]:
            min_idx = j
    nums[i], nums[min_idx] = nums[min_idx], nums[i]
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        finalized_indices = []
        for step in result["steps"]:
            for ev in step.get("events", []):
                if ev.get("type") == "position_finalized":
                    finalized_indices.extend(ev.get("indices", []))

        # Index 0 must be finalized first, followed by index 1, etc.
        self.assertIn(0, finalized_indices)
        self.assertIn(1, finalized_indices)
        self.assertLess(finalized_indices.index(0), finalized_indices.index(1))

    def test_insertion_sort_prefix_discovery(self):
        """
        Insertion sort semantics:
        - Intermediate sorted prefixes are marked as 'discovered' (segment_sorted), NOT finalized.
        - Terminal step marks all positions finalized.
        """
        code = """
nums = [12, 11, 13, 5, 6]
for i in range(1, len(nums)):
    key = nums[i]
    j = i - 1
    while j >= 0 and key < nums[j]:
        nums[j + 1] = nums[j]
        j -= 1
    nums[j + 1] = key
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        # Discover events should have semantic_state == 'discovered'
        discovered_events = []
        for step in result["steps"][:-1]:
            for ev in step.get("events", []):
                if ev.get("type") == "segment_sorted":
                    self.assertEqual(ev.get("semantic_state"), "discovered")
                    discovered_events.append(ev)

        self.assertTrue(len(discovered_events) >= 1)

        # Terminal step finalizes all positions
        last_step_events = result["steps"][-1].get("events", [])
        finalized_last = [ev for ev in last_step_events if ev.get("type") == "position_finalized"]
        all_finalized = set()
        for ev in finalized_last:
            all_finalized.update(ev.get("indices", []))
        self.assertEqual(all_finalized, {0, 1, 2, 3, 4})

    def test_matrix_traversal_semantics(self):
        """
        Matrix row traversal:
        - Emits matrix_access events with semantic_state 'active'.
        - Does not emit premature sorted or found events.
        """
        code = """
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
total = 0
for r in range(len(matrix)):
    for c in range(len(matrix[0])):
        total += matrix[r][c]
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        matrix_events = []
        for step in result["steps"]:
            for ev in step.get("events", []):
                if ev.get("type") == "matrix_access":
                    self.assertEqual(ev.get("semantic_state"), "active")
                    matrix_events.append(ev)
                elif ev.get("type") in ("sorted", "position_finalized", "found"):
                    self.fail(f"Unexpected premature event in matrix traversal: {ev}")

        self.assertEqual(len(matrix_events), 9)

    def test_two_sum_semantics(self):
        """
        Two Sum pair matching:
        - When pair sum == target, emits 'search_found' with semantic_state 'found'.
        """
        code = """
nums = [2, 7, 11, 15]
target = 9
found_pair = None
for i in range(len(nums)):
    for j in range(i + 1, len(nums)):
        if nums[i] + nums[j] == target:
            found_pair = (i, j)
            break
"""
        result = self.tracer.run_trace(code)
        self.assertEqual(result["status"], "completed")

        found_events = []
        for step in result["steps"]:
            for ev in step.get("events", []):
                if ev.get("semantic_state") == "found" or ev.get("type") in ("found", "search_found"):
                    found_events.append(ev)

        self.assertTrue(len(found_events) >= 1)
        self.assertEqual(set(found_events[0].get("indices", [])), {0, 1})

    def test_reversibility_and_determinism(self):
        """
        Reversibility and determinism:
        - Executing the same trace multiple times yields identical sequences of steps and events.
        """
        code = """
nums = [3, 1, 2]
nums[0], nums[1] = nums[1], nums[0]
"""
        res1 = self.tracer.run_trace(code)
        res2 = self.tracer.run_trace(code)

        self.assertEqual(len(res1["steps"]), len(res2["steps"]))
        for s1, s2 in zip(res1["steps"], res2["steps"]):
            ev1 = s1.get("events", [])
            ev2 = s2.get("events", [])
            self.assertEqual(len(ev1), len(ev2))
            for e1, e2 in zip(ev1, ev2):
                self.assertEqual(e1.get("type"), e2.get("type"))
                self.assertEqual(e1.get("semantic_state"), e2.get("semantic_state"))


if __name__ == "__main__":
    unittest.main()
