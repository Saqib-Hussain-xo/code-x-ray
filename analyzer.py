"""
Code X-Ray Complexity Analyzer
Provides static AST Big-O complexity estimates combined with empirical operation metrics.
"""

import ast
from typing import Any, Dict, List, Optional
from recognizer import recognize_algorithm


def get_loop_nesting_depth(tree: ast.AST) -> int:
    """
    Computes the maximum loop nesting depth (For and While loops) in an AST.
    """
    max_depth = 0

    def visit(node: ast.AST, current_depth: int) -> None:
        nonlocal max_depth
        is_loop = isinstance(node, (ast.For, ast.While))
        new_depth = current_depth + 1 if is_loop else current_depth
        if new_depth > max_depth:
            max_depth = new_depth
        for child in ast.iter_child_nodes(node):
            visit(child, new_depth)

    visit(tree, 0)
    return max_depth


def has_logarithmic_step(tree: ast.AST) -> bool:
    """
    Detects whether loops contain halving operations (e.g. // 2, >> 1) typical of binary search.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            for child in ast.walk(node):
                if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.FloorDiv, ast.RShift)):
                    return True
    return False


def detect_auxiliary_allocations(tree: ast.AST) -> bool:
    """
    Detects whether dynamic data structures are allocated or grown proportional to input.
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in ("append", "extend", "insert"):
                return True
    return False


def analyze_complexity(
    code_str: str,
    trace_metrics: Optional[Dict[str, Any]] = None,
    recognized_algo: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyzes code to produce an estimated time/space complexity alongside measured metrics.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        return {
            "estimated_time": "Unable to determine reliably",
            "estimated_space": "Unable to determine reliably",
            "confidence": "low",
            "max_loop_depth": 0,
            "dominant_operations": [],
            "explanation": "Code contains syntax errors; static analysis unavailable.",
            "observed_metrics": trace_metrics,
            "disclaimer": "Static estimate based on AST heuristics. Measured runtime operations reflect this single execution and do not prove asymptotic complexity."
        }

    rec = recognized_algo if recognized_algo is not None else recognize_algorithm(code_str)
    algo_id = rec.get("algorithm") or rec.get("algorithm_id", "generic")
    algo_category = rec.get("category", "")
    loop_depth = get_loop_nesting_depth(tree)
    has_halving = has_logarithmic_step(tree)
    has_alloc = detect_auxiliary_allocations(tree)

    dominant_ops = []
    if loop_depth > 0:
        dominant_ops.append("loop_iterations")
    if any(isinstance(n, ast.Compare) for n in ast.walk(tree)):
        dominant_ops.append("comparisons")
    if any(isinstance(n, ast.Subscript) for n in ast.walk(tree)):
        dominant_ops.append("array_accesses")

    # 1. Recognized Algorithm Families
    if algo_category == "sorting" or algo_id in ("bubble_sort", "selection_sort", "insertion_sort", "generic_sort"):
        est_time = "O(n^2)"
        est_space = "O(1)"
        confidence = "high"
        explanation = f"Quadratic sorting algorithm ({rec.get('algorithm', 'sorting')}) with nested passes comparing and reordering elements."
    elif algo_id == "binary_search":
        est_time = "O(log n)"
        est_space = "O(1)"
        confidence = "high"
        explanation = "Logarithmic search repeatedly halving the search interval until target is located."
    elif algo_category == "searching" or algo_id in ("linear_search", "sentinel_search"):
        est_time = "O(n)"
        est_space = "O(1)"
        confidence = "high"
        explanation = "Linear search scanning up to n elements sequentially."
    elif algo_category == "matrix" or algo_id.startswith("matrix_"):
        est_time = "O(n^2)"
        est_space = "O(1)"
        confidence = "high"
        explanation = "2D matrix traversal scanning rectangular rows and columns."
    elif algo_id == "two_pointer":
        est_time = "O(n)"
        est_space = "O(1)"
        confidence = "high"
        explanation = "Linear two-pointer scan converging from opposite ends in a single pass."
    elif algo_id == "recursion":
        est_time = "O(n)"
        est_space = "O(n)"
        confidence = "medium"
        explanation = "Recursive function with linear call stack depth allocation."
    else:
        # Fallback to pure AST loop-depth heuristics
        if loop_depth == 0:
            est_time = "O(1)"
            est_space = "O(1)"
            confidence = "high"
            explanation = "No iteration loops or recursion detected; executes in constant time."
        elif loop_depth == 1:
            if has_halving:
                est_time = "O(log n)"
                est_space = "O(1)"
                confidence = "medium"
                explanation = "Single loop with halving operation; estimated logarithmic time."
            else:
                est_time = "O(n)"
                est_space = "O(n)" if has_alloc else "O(1)"
                confidence = "high"
                explanation = "Single linear loop iterating over input elements."
        elif loop_depth == 2:
            est_time = "O(n^2)"
            est_space = "O(n)" if has_alloc else "O(1)"
            confidence = "high"
            explanation = "Two nested iteration loops yielding quadratic time complexity."
        elif loop_depth == 3:
            est_time = "O(n^3)"
            est_space = "O(n)" if has_alloc else "O(1)"
            confidence = "medium"
            explanation = "Three nested iteration loops yielding cubic time complexity."
        else:
            est_time = f"O(n^{loop_depth})"
            est_space = "O(1)"
            confidence = "low"
            explanation = f"Deeply nested iteration loops ({loop_depth} levels)."

    # Format observed metrics description if available
    observed_summary = None
    if trace_metrics:
        observed_summary = {
            "metrics": trace_metrics,
            "summary_text": (
                f"Single run measured: {trace_metrics.get('comparisons', 0)} comparisons, "
                f"{trace_metrics.get('swaps', 0)} swaps, {trace_metrics.get('assignments', 0)} assignments, "
                f"{trace_metrics.get('loop_iterations', 0)} loop iterations ({trace_metrics.get('total', 0)} total operations)."
            )
        }

    return {
        "estimated_time": est_time,
        "estimated_space": est_space,
        "confidence": confidence,
        "max_loop_depth": loop_depth,
        "dominant_operations": dominant_ops,
        "explanation": explanation,
        "observed_metrics": observed_summary,
        "disclaimer": "Static estimate based on AST heuristics. Measured runtime operations reflect this single execution and do not prove asymptotic complexity."
    }
