"""
X-Ray Execution Agent: Error Detective Diagnostics Engine
File: diagnostics.py

Provides beginner-friendly, root-cause diagnostics and pedagogical fix suggestions
for Python runtime exceptions (IndexError, TypeError, ZeroDivisionError, RecursionError,
TraceLimitExceeded, TraceTimeout) and SyntaxErrors.

Strict rules:
- Zero LLM dependency: deterministic pattern analysis guarantees 100% reliable advice.
- Zero em dashes in strings or docstrings.
"""

import re
from typing import Any, Dict, Optional


def diagnose_error(
    error_info: Optional[Dict[str, Any]],
    code_str: str = "",
    last_step: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Analyze error details, AST line content, and final execution state to produce
    a human-readable diagnostic title, explanation, and pedagogical suggestion.
    """
    if not error_info:
        return {
            "title": "Unknown Error",
            "explanation": "An unexpected error occurred during execution.",
            "suggestion": "Check the standard output console for traceback information."
        }

    err_type = error_info.get("type", "RuntimeError")
    err_msg = error_info.get("message", "")
    line_no = error_info.get("line_no", 1)

    code_lines = code_str.split("\n") if code_str else []
    failing_line = code_lines[line_no - 1].strip() if 1 <= line_no <= len(code_lines) else ""
    locals_snap = last_step.get("locals_snapshot", {}) if last_step else {}

    # 1. IndexError
    if err_type == "IndexError":
        # Check sequences in last step
        seqs = last_step.get("sequences", {}) if last_step else {}
        details = []
        for seq_name, seq_info in seqs.items():
            length = seq_info.get("length", 0)
            details.append(f"'{seq_name}' has length {length} (valid indices: 0 to {max(0, length - 1)})")

        seq_summary = "; ".join(details) if details else "the sequence is empty or bounds were exceeded"

        return {
            "title": "Index Out of Bounds (IndexError)",
            "explanation": f"At line {line_no} (`{failing_line}`), code attempted to access an index outside the sequence bounds. Specifically: {seq_summary}.",
            "suggestion": "Python uses 0-based indexing (0 to length - 1). Verify loop boundaries; for example, use `while left < len(arr):` instead of `<= len(arr)`."
        }

    # 2. TypeError
    if err_type == "TypeError":
        if "not supported between instances" in err_msg:
            return {
                "title": "Incompatible Types in Comparison (TypeError)",
                "explanation": f"At line {line_no} (`{failing_line}`), an order comparison (<, <=, >, >=) was attempted between incompatible data types ({err_msg}).",
                "suggestion": "Ensure all elements in the collection or variables being compared share the same data type (e.g. all integers or all strings)."
            }
        if "object is not subscriptable" in err_msg:
            return {
                "title": "Subscript on Non-Indexable Object (TypeError)",
                "explanation": f"At line {line_no} (`{failing_line}`), code used bracket notation `[...]` on a variable that is not a list, tuple, dict, or string ({err_msg}).",
                "suggestion": "Check if a variable was assigned None or an integer. If calling a function, make sure it returns a list rather than None."
            }
        return {
            "title": f"Type Mismatch ({err_type})",
            "explanation": f"At line {line_no} (`{failing_line}`): {err_msg}.",
            "suggestion": "Inspect variable types in the Memory Map panel to verify arguments and operands match expected types."
        }

    # 3. ZeroDivisionError
    if err_type == "ZeroDivisionError":
        return {
            "title": "Division by Zero (ZeroDivisionError)",
            "explanation": f"At line {line_no} (`{failing_line}`), a division or modulo operation used a divisor of 0.",
            "suggestion": "Add a guard check before dividing (e.g. `if divisor != 0:`) or check why the divisor variable decreased to zero."
        }

    # 4. RecursionError
    if err_type == "RecursionError":
        return {
            "title": "Infinite Recursion (RecursionError)",
            "explanation": f"At line {line_no} (`{failing_line}`), the function called itself repeatedly without stopping, exceeding Python's call limit.",
            "suggestion": "Verify your recursive base case (e.g. `if n <= 1: return n`) and ensure recursive arguments make progress toward the base case."
        }

    # 5. TraceLimitExceeded
    if err_type == "TraceLimitExceeded":
        return {
            "title": "Loop Step Limit Exceeded (1,000 steps)",
            "explanation": f"Execution exceeded 1,000 steps around line {line_no} (`{failing_line}`). This usually indicates an infinite while loop.",
            "suggestion": "Check the loop variable inside the loop body. Ensure loop pointers (e.g. `i`, `left`, `right`) are modified during every iteration so the loop condition eventually becomes False."
        }

    # 6. TraceTimeout
    if err_type == "TraceTimeout":
        return {
            "title": "Execution Time Budget Exceeded (2.0s limit)",
            "explanation": f"Execution took longer than 2.0 seconds near line {line_no} (`{failing_line}`).",
            "suggestion": "Check for deeply nested loops or non-advancing while loops. Ensure step increments are properly configured."
        }

    # 7. NameError
    if err_type == "NameError":
        var_match = re.search(r"name '([^']+)' is not defined", err_msg)
        var_name = var_match.group(1) if var_match else "variable"
        return {
            "title": f"Undefined Variable (NameError: {var_name})",
            "explanation": f"At line {line_no} (`{failing_line}`), Python encountered '{var_name}', which has not been defined or initialized in current scope.",
            "suggestion": f"Initialize '{var_name}' before this line (e.g. `{var_name} = 0` or `{var_name} = []`), or check for a spelling typo."
        }

    # 8. SyntaxError
    if err_type == "SyntaxError":
        return {
            "title": "Syntax Error",
            "explanation": f"Line {line_no} contains invalid Python syntax: {err_msg}.",
            "suggestion": "Check for missing colons `:` at the end of `if`, `for`, `while`, or `def` lines, or unclosed parentheses `()`, brackets `[]`, or quotes."
        }

    # Default fallback
    return {
        "title": f"Runtime Exception ({err_type})",
        "explanation": f"Error at line {line_no} (`{failing_line}`): {err_msg}.",
        "suggestion": "Inspect the active line in the editor and variable states in the Memory Map panel."
    }
