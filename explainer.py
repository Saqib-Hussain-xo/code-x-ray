"""
X-Ray Execution Agent: Step-by-Step Explanation Engine
File: explainer.py

Deterministic explanation generator that translates execution events,
AST line semantics, variable mutations, and pointer adjustments into
clear, pedagogically sound plain-English explanations.

Strict rules:
- Zero LLM dependency: deterministic templating ensures 100% reliability, reproducibility, and zero latency.
- Zero em dashes in strings or docstrings.
"""

from typing import Dict, Any, Optional, List


def generate_step_explanation(
    step: Dict[str, Any],
    prev_step: Optional[Dict[str, Any]] = None,
    recognition: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a concise, human-readable explanation for a single execution step.
    Prioritizes high-level semantic events, then memory mutations, then line operations.
    """
    events: List[Dict[str, Any]] = step.get("events", [])
    locals_curr = step.get("locals_snapshot", {})
    locals_prev = prev_step.get("locals_snapshot", {}) if prev_step else {}
    line_no = step.get("line_no", 1)

    # 1. Search Events
    for e in events:
        e_type = e.get("type")
        if e_type == "found":
            target_val = e.get("value")
            idx = e.get("index")
            return f"Found target value {target_val} at index {idx}."
        if e_type == "search_range":
            low = e.get("low")
            high = e.get("high")
            mid = e.get("mid")
            if mid is not None:
                return f"Narrowing search range to [{low}..{high}]; inspecting middle index {mid}."
            return f"Search range set to [{low}..{high}]."
        if e_type == "visit":
            idx = e.get("index")
            val = e.get("value")
            return f"Visiting index {idx} with value {val}."
        if e_type == "reject":
            idx = e.get("index")
            return f"Element at index {idx} does not match the search target."

    # 2. Matrix Events
    for e in events:
        e_type = e.get("type")
        if e_type == "matrix_access":
            target = e.get("target", "matrix")
            r = e.get("row")
            c = e.get("col")
            val = e.get("value")
            return f"Accessing cell {target}[{r}][{c}] (value: {val})."
        if e_type == "row_complete":
            r = e.get("row")
            return f"Completed scan of row {r}."
        if e_type == "column_complete":
            c = e.get("col")
            return f"Completed scan of column {c}."

    # 3. Sorting & Sequence Events
    for e in events:
        e_type = e.get("type")
        if e_type == "swap":
            target = e.get("target", "sequence")
            indices = e.get("indices", [])
            from_vals = e.get("from_values", [])
            to_vals = e.get("to_values", [])
            if len(indices) == 2 and len(from_vals) == 2:
                return f"Swapped {target}[{indices[0]}] ({from_vals[0]}) with {target}[{indices[1]}] ({from_vals[1]})."
            return f"Swapped elements in {target} at indices {indices}."
        if e_type == "sorted":
            target = e.get("target", "sequence")
            return f"All elements in {target} are now in sorted order."
        if e_type == "compare":
            target = e.get("target", "sequence")
            indices = e.get("indices", [])
            if len(indices) == 2:
                return f"Comparing elements {target}[{indices[0]}] and {target}[{indices[1]}]."
            if len(indices) == 1:
                return f"Comparing element {target}[{indices[0]}] against comparison value."

    # 4. Mutations & Variable Transitions
    mutated_vars = []
    for var_name, val in locals_curr.items():
        if var_name.startswith("__"):
            continue
        if var_name not in locals_prev:
            mutated_vars.append((var_name, None, val, True))
        elif locals_prev[var_name] != val:
            mutated_vars.append((var_name, locals_prev[var_name], val, False))

    if mutated_vars:
        # Single variable assignment
        if len(mutated_vars) == 1:
            var_name, old_val, new_val, is_new = mutated_vars[0]
            if is_new:
                return f"Initialized variable '{var_name}' to {new_val}."
            return f"Updated '{var_name}' from {old_val} to {new_val}."
        # Multiple variable updates
        summary_parts = []
        for var_name, _, new_val, is_new in mutated_vars[:3]:
            summary_parts.append(f"{var_name}={new_val}")
        return f"Updated variables: {', '.join(summary_parts)}."

    # 5. Pointers check
    pointers = step.get("pointers", [])
    prev_pointers = prev_step.get("pointers", []) if prev_step else []
    if pointers and prev_pointers:
        for p in pointers:
            p_name = p.get("name")
            p_val = p.get("value")
            prev_match = next((pp for pp in prev_pointers if pp.get("name") == p_name), None)
            if prev_match and prev_match.get("value") != p_val:
                return f"Moved pointer '{p_name}' from index {prev_match.get('value')} to {p_val}."

    # 6. Default fallback
    return f"Executed line {line_no}."
