"""
Code X-Ray Algorithm and Code Comparison Engine (comparison.py)
Provides comparative execution, structural diffing, operational metrics deltas, and output verification.
"""

import ast
from typing import Any, Dict, Optional
from tracer import ExecutionTracer
from analyzer import analyze_complexity


def get_ast_stats(code_str: str) -> Dict[str, int]:
    """
    Computes structural AST metrics: node count, line count, and statement count.
    """
    lines = [line for line in code_str.strip().splitlines() if line.strip() and not line.strip().startswith("#")]
    try:
        tree = ast.parse(code_str)
        nodes = list(ast.walk(tree))
        node_count = len(nodes)
        statement_count = len([n for n in nodes if isinstance(n, ast.stmt)])
    except SyntaxError:
        node_count = 0
        statement_count = 0

    return {
        "line_count": len(lines),
        "node_count": node_count,
        "statement_count": statement_count
    }


def compare_algorithms(
    code_a: str,
    code_b: str,
    stdin_data: str = "",
    name_a: str = "Implementation A",
    name_b: str = "Implementation B"
) -> Dict[str, Any]:
    """
    Executes two code implementations on identical input and compares outputs,
    structural metrics, runtime operations, and asymptotic complexity estimates.
    """
    tracer_a = ExecutionTracer(max_steps=1000, max_seconds=2.0)
    tracer_b = ExecutionTracer(max_steps=1000, max_seconds=2.0)

    trace_a = tracer_a.run_trace(code_a, stdin_data=stdin_data)
    trace_b = tracer_b.run_trace(code_b, stdin_data=stdin_data)

    metrics_a = trace_a.get("operation_metrics", {})
    metrics_b = trace_b.get("operation_metrics", {})

    complexity_a = analyze_complexity(code_a, trace_metrics=metrics_a, recognized_algo=trace_a.get("recognition"))
    complexity_b = analyze_complexity(code_b, trace_metrics=metrics_b, recognized_algo=trace_b.get("recognition"))

    struct_a = get_ast_stats(code_a)
    struct_b = get_ast_stats(code_b)

    # Output Equivalence Check
    stdout_a = trace_a.get("stdout", "").strip()
    stdout_b = trace_b.get("stdout", "").strip()

    status_a = trace_a.get("status", "unknown")
    status_b = trace_b.get("status", "unknown")

    outputs_match = False
    output_note = ""

    if status_a != "completed" or status_b != "completed":
        outputs_match = False
        output_note = f"Execution incomplete: {name_a} status is '{status_a}', {name_b} status is '{status_b}'."
    elif stdout_a or stdout_b:
        outputs_match = (stdout_a == stdout_b)
        output_note = "Standard output matched exactly." if outputs_match else "Standard outputs differed."
    else:
        # Check final sequence locals state
        final_locals_a = trace_a["steps"][-1].get("locals_snapshot", {}) if trace_a.get("steps") else {}
        final_locals_b = trace_b["steps"][-1].get("locals_snapshot", {}) if trace_b.get("steps") else {}

        common_keys = [k for k in final_locals_a if k in final_locals_b and not k.startswith("_")]
        if common_keys:
            all_match = all(final_locals_a[k] == final_locals_b[k] for k in common_keys)
            outputs_match = all_match
            output_note = f"Shared final state variable(s) {common_keys} matched." if all_match else "Shared final state variable values differed."
        else:
            outputs_match = True
            output_note = "Both implementations completed cleanly with no conflicting output."

    # Operations Delta Table
    operations_delta = {}
    metric_keys = ["comparisons", "swaps", "assignments", "array_accesses", "loop_iterations", "function_calls", "total"]
    for k in metric_keys:
        val_a = metrics_a.get(k, 0)
        val_b = metrics_b.get(k, 0)
        operations_delta[k] = {
            "a": val_a,
            "b": val_b,
            "diff_b_minus_a": val_b - val_a
        }

    # Balanced qualitative verdict without unproven claims
    if status_a == "completed" and status_b == "completed":
        if outputs_match:
            steps_a = trace_a.get("total_steps", 0)
            steps_b = trace_b.get("total_steps", 0)
            verdict = (
                f"Both implementations produced matching outputs on this input. "
                f"{name_a} executed {steps_a} steps ({metrics_a.get('comparisons', 0)} comparisons, {metrics_a.get('swaps', 0)} swaps) "
                f"while {name_b} executed {steps_b} steps ({metrics_b.get('comparisons', 0)} comparisons, {metrics_b.get('swaps', 0)} swaps). "
                f"Note: Single-input operation counts illustrate execution mechanics but do not prove asymptotic superiority."
            )
        else:
            verdict = (
                f"Implementations produced differing outputs on this input. "
                f"Verify algorithm logic or problem constraints."
            )
    else:
        verdict = f"Comparison inconclusive because one or both implementations failed to complete cleanly."

    return {
        "implementation_a": {
            "name": name_a,
            "status": status_a,
            "total_steps": trace_a.get("total_steps", 0),
            "stdout": stdout_a,
            "recognition": trace_a.get("recognition", {}),
            "complexity": complexity_a,
            "structure": struct_a,
            "metrics": metrics_a
        },
        "implementation_b": {
            "name": name_b,
            "status": status_b,
            "total_steps": trace_b.get("total_steps", 0),
            "stdout": stdout_b,
            "recognition": trace_b.get("recognition", {}),
            "complexity": complexity_b,
            "structure": struct_b,
            "metrics": metrics_b
        },
        "comparison": {
            "outputs_match": outputs_match,
            "output_note": output_note,
            "operations_delta": operations_delta,
            "verdict": verdict,
            "disclaimer": "Measured operation counts reflect this specific execution and do not constitute formal asymptotic proof."
        }
    }
