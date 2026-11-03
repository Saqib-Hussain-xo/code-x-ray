"""
X-Ray Execution Agent: AST-Based Algorithm Recognizer
Module: recognizer.py

Analyzes Python source code structure using the built-in ast module to recognize
algorithmic patterns (Sorting, Searching, Matrix Traversal, Two Pointers, Recursion)
with confidence scoring and safe generic fallback.
"""

import ast
from typing import Any, Dict, List, Optional, Set, Tuple


class AlgorithmRecognizer:
    """
    Static code analyzer evaluating AST patterns to determine the most likely
    algorithm family and specific algorithm implementation.
    """

    def __init__(self, code_str: str):
        self.code_str = code_str
        self.tree: Optional[ast.AST] = None
        self.features: Set[str] = set()
        self.parse_error: Optional[str] = None

        try:
            self.tree = ast.parse(code_str)
        except SyntaxError as e:
            self.parse_error = str(e)

    def extract_features(self) -> Set[str]:
        """
        Inspect AST nodes and extract structural features.
        """
        if not self.tree:
            return self.features

        has_nested_loops = False
        loop_depth = 0
        max_loop_depth = 0
        has_tuple_swap = False
        has_subscript_compare = False
        has_mid_calculation = False
        has_binary_search_bounds = False
        has_recursion = False
        has_2d_subscript = False
        has_linear_search_pattern = False

        function_names = set()
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.add(node.name)

        class FeatureVisitor(ast.NodeVisitor):
            def __init__(self, outer):
                self.outer = outer
                self.current_loop_depth = 0
                self.current_func = None

            def visit_FunctionDef(self, node):
                prev_func = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = prev_func

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and self.current_func:
                    if node.func.id == self.current_func:
                        self.outer.features.add("recursion")
                self.generic_visit(node)

            def visit_For(self, node):
                self.current_loop_depth += 1
                if self.current_loop_depth > self.outer.max_depth:
                    self.outer.max_depth = self.current_loop_depth
                if self.current_loop_depth >= 2:
                    self.outer.features.add("nested_loops")
                self.generic_visit(node)
                self.current_loop_depth -= 1

            def visit_While(self, node):
                self.current_loop_depth += 1
                if self.current_loop_depth > self.outer.max_depth:
                    self.outer.max_depth = self.current_loop_depth
                if self.current_loop_depth >= 2:
                    self.outer.features.add("nested_loops")
                self.generic_visit(node)
                self.current_loop_depth -= 1

            def visit_Assign(self, node):
                # Tuple swap detection: a[i], a[j] = a[j], a[i]
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
                    if isinstance(node.value, ast.Tuple) and len(node.targets[0].elts) == 2 and len(node.value.elts) == 2:
                        self.outer.features.add("tuple_swap")

                # Mid calculation: (low + high) // 2 or (left + right) // 2
                if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, (ast.FloorDiv, ast.Div)):
                    self.outer.features.add("mid_calculation")

                self.generic_visit(node)

            def visit_Compare(self, node):
                if isinstance(node.left, ast.Subscript):
                    self.outer.features.add("subscript_comparison")
                for comp in node.comparators:
                    if isinstance(comp, ast.Subscript):
                        self.outer.features.add("subscript_comparison")
                self.generic_visit(node)

            def visit_Subscript(self, node):
                # 2D indexing: a[r][c] -> Subscript(value=Subscript(...))
                if isinstance(node.value, ast.Subscript):
                    self.outer.features.add("2d_indexing")
                self.generic_visit(node)

        self.max_depth = 0
        visitor = FeatureVisitor(self)
        visitor.visit(self.tree)

        if self.max_depth == 1:
            self.features.add("single_loop")
        elif self.max_depth >= 2:
            self.features.add("nested_loops")

        # Binary search interval adjustments: low = mid + 1, high = mid - 1
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id.lower()
                        if name in ("low", "left", "start", "high", "right", "end"):
                            if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, (ast.Add, ast.Sub)):
                                self.features.add("interval_adjustment")

        # Linear search: loop with if element == target: return or break
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        if isinstance(child.test, ast.Compare):
                            # check for return or break in body
                            for sub in child.body:
                                if isinstance(sub, (ast.Return, ast.Break)):
                                    self.features.add("conditional_break_or_return")

        return self.features

    def recognize(self) -> Dict[str, Any]:
        """
        Classify the algorithm family and compute confidence score.
        """
        if self.parse_error or not self.tree:
            return {
                "algorithm": "generic",
                "category": "generic",
                "confidence": 0.0,
                "visualization": "generic",
                "features": []
            }

        features = self.extract_features()
        code_lower = self.code_str.lower()

        # 1. 2D Matrix Algorithms
        if "2d_indexing" in features:
            if "matrix_diagonal" in code_lower or "diagonal" in code_lower:
                return {
                    "algorithm": "matrix_diagonal",
                    "category": "matrix",
                    "confidence": 0.95,
                    "visualization": "matrix",
                    "features": sorted(list(features))
                }
            if "row_sums" in code_lower or ("row" in code_lower and "sum" in code_lower):
                return {
                    "algorithm": "matrix_row_sums",
                    "category": "matrix",
                    "confidence": 0.95,
                    "visualization": "matrix",
                    "features": sorted(list(features))
                }
            if "col_sums" in code_lower or ("col" in code_lower and "sum" in code_lower):
                return {
                    "algorithm": "matrix_col_sums",
                    "category": "matrix",
                    "confidence": 0.95,
                    "visualization": "matrix",
                    "features": sorted(list(features))
                }
            return {
                "algorithm": "matrix_traversal",
                "category": "matrix",
                "confidence": 0.90,
                "visualization": "matrix",
                "features": sorted(list(features))
            }

        # 2. Searching Algorithms
        if "mid_calculation" in features and "interval_adjustment" in features:
            return {
                "algorithm": "binary_search",
                "category": "searching",
                "confidence": 0.95,
                "visualization": "searching",
                "features": sorted(list(features))
            }

        if "single_loop" in features and "conditional_break_or_return" in features and "tuple_swap" not in features:
            if "sentinel" in code_lower:
                return {
                    "algorithm": "sentinel_search",
                    "category": "searching",
                    "confidence": 0.90,
                    "visualization": "searching",
                    "features": sorted(list(features))
                }
            if "search" in code_lower or "find" in code_lower or "target" in code_lower:
                return {
                    "algorithm": "linear_search",
                    "category": "searching",
                    "confidence": 0.88,
                    "visualization": "searching",
                    "features": sorted(list(features))
                }

        # 3. Sorting Algorithms
        if "nested_loops" in features and ("tuple_swap" in features or "subscript_comparison" in features):
            # Bubble Sort vs Selection Sort vs Insertion Sort
            if "bubble" in code_lower or ("tuple_swap" in features and "subscript_comparison" in features and "min" not in code_lower):
                return {
                    "algorithm": "bubble_sort",
                    "category": "sorting",
                    "confidence": 0.92,
                    "visualization": "sorting",
                    "features": sorted(list(features))
                }
            if "selection" in code_lower or "min_idx" in code_lower or "min" in code_lower:
                return {
                    "algorithm": "selection_sort",
                    "category": "sorting",
                    "confidence": 0.92,
                    "visualization": "sorting",
                    "features": sorted(list(features))
                }
            if "insertion" in code_lower or ("while" in code_lower and "key" in code_lower):
                return {
                    "algorithm": "insertion_sort",
                    "category": "sorting",
                    "confidence": 0.90,
                    "visualization": "sorting",
                    "features": sorted(list(features))
                }
            return {
                "algorithm": "generic_sort",
                "category": "sorting",
                "confidence": 0.80,
                "visualization": "sorting",
                "features": sorted(list(features))
            }

        # 4. Recursion
        if "recursion" in features:
            algo_name = "recursion"
            if "factorial" in code_lower:
                algo_name = "factorial_recursion"
            elif "fibonacci" in code_lower or "fib" in code_lower:
                algo_name = "fibonacci_recursion"
            return {
                "algorithm": algo_name,
                "category": "recursion",
                "confidence": 0.90,
                "visualization": "recursion",
                "features": sorted(list(features))
            }

        # 5. Two Pointers / Sliding Window
        if "single_loop" in features and ("left" in code_lower and "right" in code_lower):
            if "window" in code_lower or "substr" in code_lower:
                return {
                    "algorithm": "sliding_window",
                    "category": "sliding_window",
                    "confidence": 0.85,
                    "visualization": "generic",
                    "features": sorted(list(features))
                }
            return {
                "algorithm": "two_pointers",
                "category": "two_pointers",
                "confidence": 0.85,
                "visualization": "generic",
                "features": sorted(list(features))
            }

        # Fallback to Generic
        return {
            "algorithm": "generic",
            "category": "generic",
            "confidence": 0.0,
            "visualization": "generic",
            "features": sorted(list(features))
        }


def recognize_algorithm(code_str: str) -> Dict[str, Any]:
    """
    Public entry point for AST-based algorithm classification.
    """
    recognizer = AlgorithmRecognizer(code_str)
    return recognizer.recognize()
