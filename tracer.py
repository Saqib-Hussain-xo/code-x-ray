"""
X-Ray Execution Agent: Deterministic Python Runtime Tracer Engine
Module: tracer.py

Features:
- Deterministic line-by-line runtime state interception using sys.settrace.
- Dual loop guard: 1,000 steps limit and 2.0 seconds timeout.
- Deep-copied locals snapshot serialization with cyclic reference protection.
- State mutation diffing between consecutive execution steps.
- Sequence and pointer heuristic detection for DSA visualizer.
- Incremental stdout capture and unhandled exception recording.
"""

import ast
import copy
import inspect
import io
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from recognizer import recognize_algorithm
except ImportError:
    def recognize_algorithm(code: str) -> Dict[str, Any]:
        return {
            "algorithm": "generic",
            "category": "generic",
            "confidence": 0.0,
            "visualization": "generic",
            "features": []
        }

try:
    from explainer import generate_step_explanation
except ImportError:
    def generate_step_explanation(step: Dict[str, Any], prev_step=None, recognition=None) -> str:
        return f"Executed line {step.get('line_no', 1)}."

try:
    from diagnostics import diagnose_error
except ImportError:
    def diagnose_error(error_info, code_str="", last_step=None) -> Dict[str, str]:
        return {
            "title": error_info.get("type", "Error"),
            "explanation": error_info.get("message", "Execution error"),
            "suggestion": "Check your code."
        }


class SafeStdin(io.StringIO):
    """
    Guarded standard input stream that returns empty strings instead of EOFError when exhausted.
    """
    def readline(self, size: int = -1) -> str:
        line = super().readline(size)
        if not line:
            return ""
        return line


class TraceLimitExceeded(RuntimeError):
    """Raised when execution step count reaches the configured threshold."""
    pass


class TraceTimeout(RuntimeError):
    """Raised when execution duration reaches the configured wall-clock timeout."""
    pass


# Candidate pointer names common in Data Structures and Algorithms implementations.
COMMON_POINTER_NAMES: Set[str] = {
    "i", "j", "k", "l", "r", "p", "q",
    "left", "right", "low", "high", "mid", "middle",
    "slow", "fast", "start", "end", "idx", "index",
    "ptr", "pointer", "curr", "cur", "prev", "next",
    "head", "tail", "pivot", "anchor", "read", "write",
    "top", "bottom", "first", "last"
}

# Common suffixes identifying pointer or index variables.
POINTER_SUFFIXES: Tuple[str, ...] = (
    "_idx", "_index", "_ptr", "_pointer", "_i", "_j", "_k",
    "_pos", "_head", "_tail"
)


def is_candidate_pointer_name(name: str) -> bool:
    """
    Determine if a variable name follows algorithmic pointer or index conventions.
    """
    lowered = name.lower()
    if lowered in COMMON_POINTER_NAMES:
        return True
    return any(lowered.endswith(suffix) for suffix in POINTER_SUFFIXES)


def serialize_value(val: Any, depth: int = 0, max_depth: int = 8, seen: Optional[Set[int]] = None) -> Any:
    """
    Recursively serialize Python objects into JSON-compatible primitives.
    Guards against circular references and deep nesting.
    """
    if seen is None:
        seen = set()

    # Direct primitive passthrough
    if val is None or isinstance(val, (int, float, str, bool)):
        return val

    val_id = id(val)
    if val_id in seen:
        return "<circular reference>"

    if depth > max_depth:
        return repr(val)

    seen.add(val_id)

    try:
        if isinstance(val, (list, tuple)):
            # Cap array serialization length to avoid oversized payloads
            max_items = 100
            serialized_items = [
                serialize_value(item, depth + 1, max_depth, seen.copy())
                for item in val[:max_items]
            ]
            if len(val) > max_items:
                serialized_items.append(f"... ({len(val) - max_items} more items)")
            return serialized_items

        if isinstance(val, set):
            max_items = 100
            items_list = list(val)[:max_items]
            serialized_items = [
                serialize_value(item, depth + 1, max_depth, seen.copy())
                for item in items_list
            ]
            return serialized_items

        if isinstance(val, dict):
            max_items = 50
            serialized_dict = {}
            for i, (k, v) in enumerate(val.items()):
                if i >= max_items:
                    serialized_dict["..."] = f"({len(val) - max_items} more keys)"
                    break
                serialized_dict[str(k)] = serialize_value(v, depth + 1, max_depth, seen.copy())
            return serialized_dict

        if inspect.isfunction(val) or inspect.ismethod(val):
            func_name = getattr(val, "__name__", repr(val))
            return f"<function {func_name}>"

        if inspect.isclass(val):
            return f"<class {val.__name__}>"

        return repr(val)

    except Exception:
        return repr(val)


def extract_sequences(locals_dict: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Inspect local variables to identify active 1D/2D lists, tuples, and strings.
    Extracts element breakdowns to support frontend memory cell rendering.
    """
    sequences: Dict[str, Dict[str, Any]] = {}

    for var_name, val in locals_dict.items():
        if var_name.startswith("__"):
            continue

        if isinstance(val, (list, tuple)):
            # Distinguish 1D vs 2D rectangular matrices vs irregular nested
            is_2d = False
            matrix_data = None
            rows = 0
            cols = 0
            if len(val) > 0 and all(isinstance(sub, (list, tuple)) for sub in val):
                first_len = len(val[0])
                if all(len(sub) == first_len for sub in val):
                    is_2d = True
                    rows = len(val)
                    cols = first_len
                    # Bounded 10x10 representation for performant UI rendering
                    matrix_data = []
                    for r_idx, row in enumerate(val[:10]):
                        row_items = [serialize_value(c) for c in row[:10]]
                        matrix_data.append(row_items)

            # Format elements for visual memory stage
            element_list = []
            for item in val[:50]:  # Cap stage display items
                element_list.append(serialize_value(item))

            sequences[var_name] = {
                "name": var_name,
                "type": type(val).__name__,
                "length": len(val),
                "elements": element_list,
                "is_nested": any(isinstance(sub, (list, tuple)) for sub in val) if val else False,
                "is_2d_matrix": is_2d,
                "rows": rows,
                "cols": cols,
                "matrix_elements": matrix_data
            }

        elif isinstance(val, str) and len(val) <= 100:
            # Strings are visualized as character cells
            sequences[var_name] = {
                "name": var_name,
                "type": "str",
                "length": len(val),
                "elements": list(val),
                "is_nested": False,
                "is_2d_matrix": False,
                "rows": 0,
                "cols": 0,
                "matrix_elements": None
            }

    return sequences


def detect_pointers(
    locals_dict: Dict[str, Any],
    sequences: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Identify integer variables functioning as pointers or indices.
    Binds each pointer to a corresponding sequence whose bounds satisfy 0 <= val <= len(seq).
    """
    pointers: List[Dict[str, Any]] = []
    if not sequences:
        return pointers

    for var_name, val in locals_dict.items():
        if var_name.startswith("__"):
            continue

        # Pointers must be integers, excluding booleans (bool is a subclass of int in Python)
        if isinstance(val, int) and not isinstance(val, bool):
            is_pointer_named = is_candidate_pointer_name(var_name)

            for seq_name, seq_info in sequences.items():
                seq_len = seq_info["length"]

                # Pointers are valid within [0, seq_len] (including boundary pointers like right = len)
                in_bounds = 0 <= val <= seq_len

                if in_bounds and is_pointer_named:
                    pointers.append({
                        "name": var_name,
                        "value": val,
                        "target": seq_name
                    })
                    break  # Bind to primary matching sequence

    return pointers


def eval_ast_index(node: ast.AST, locals_dict: Dict[str, Any]) -> Optional[int]:
    """
    Safely evaluate subscript index expressions from AST using local variables.
    Supports constant numbers, integer variable names, unary negation, and simple addition/subtraction.
    """
    try:
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, int) and not isinstance(node.value, bool) else None
        if isinstance(node, ast.Name):
            val = locals_dict.get(node.id)
            return val if isinstance(val, int) and not isinstance(val, bool) else None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            val = eval_ast_index(node.operand, locals_dict)
            return -val if val is not None else None
        if isinstance(node, ast.BinOp):
            left = eval_ast_index(node.left, locals_dict)
            right = eval_ast_index(node.right, locals_dict)
            if left is not None and right is not None:
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
    except Exception:
        return None
    return None


def detect_operations(
    prev_sequences: Dict[str, Dict[str, Any]],
    curr_sequences: Dict[str, Dict[str, Any]],
    ast_compares: List[ast.Compare],
    raw_locals: Dict[str, Any],
    ast_subscript_assigns: Optional[Dict[str, Tuple[str, ast.AST]]] = None
) -> List[Dict[str, Any]]:
    """
    Detect explicit sequence operations (swaps, comparisons, shifts, mutations)
    to power physics-inspired animations and semantic visualization in the frontend.
    """
    operations: List[Dict[str, Any]] = []
    seen_ops = set()
    sub_assigns = ast_subscript_assigns or {}

    # 1. Comparison detection on active line
    for comp in ast_compares:
        try:
            left_seq = None
            idx1 = None
            if isinstance(comp.left, ast.Subscript) and isinstance(comp.left.value, ast.Name):
                left_seq = comp.left.value.id
                idx1 = eval_ast_index(comp.left.slice, raw_locals)
            elif isinstance(comp.left, ast.Name) and comp.left.id in sub_assigns:
                left_seq, slice_node = sub_assigns[comp.left.id]
                idx1 = eval_ast_index(slice_node, raw_locals)

            for comparator in comp.comparators:
                right_seq = None
                idx2 = None
                if isinstance(comparator, ast.Subscript) and isinstance(comparator.value, ast.Name):
                    right_seq = comparator.value.id
                    idx2 = eval_ast_index(comparator.slice, raw_locals)
                elif isinstance(comparator, ast.Name) and comparator.id in sub_assigns:
                    right_seq, slice_node = sub_assigns[comparator.id]
                    idx2 = eval_ast_index(slice_node, raw_locals)

                # Case 1: Both elements from the same sequence (e.g. arr[i] < arr[j])
                if left_seq and right_seq and left_seq == right_seq and idx1 is not None and idx2 is not None:
                    op_key = f"comp:{left_seq}:{min(idx1, idx2)}:{max(idx1, idx2)}"
                    if op_key not in seen_ops:
                        seen_ops.add(op_key)
                        operations.append({
                            "type": "comparison",
                            "sequence": left_seq,
                            "indices": [idx1, idx2],
                            "semantic_state": "active"
                        })
                # Case 2: One element compared with a scalar or variable (e.g. arr[mid] == target)
                elif left_seq and idx1 is not None and not right_seq:
                    op_key = f"comp:{left_seq}:{idx1}"
                    if op_key not in seen_ops:
                        seen_ops.add(op_key)
                        operations.append({
                            "type": "comparison",
                            "sequence": left_seq,
                            "indices": [idx1],
                            "semantic_state": "active"
                        })
                elif right_seq and idx2 is not None and not left_seq:
                    op_key = f"comp:{right_seq}:{idx2}"
                    if op_key not in seen_ops:
                        seen_ops.add(op_key)
                        operations.append({
                            "type": "comparison",
                            "sequence": right_seq,
                            "indices": [idx2],
                            "semantic_state": "active"
                        })
        except Exception:
            pass

    # 2. Sequence state diffing (swap, shift, mutation)
    for seq_name, curr_info in curr_sequences.items():
        if seq_name in prev_sequences:
            prev_info = prev_sequences[seq_name]
            prev_elem = prev_info.get("elements", [])
            curr_elem = curr_info.get("elements", [])

            if prev_elem != curr_elem and len(prev_elem) == len(curr_elem):
                diffs = [i for i in range(len(prev_elem)) if prev_elem[i] != curr_elem[i]]
                if len(diffs) == 2:
                    i, j = diffs[0], diffs[1]
                    if prev_elem[i] == curr_elem[j] and prev_elem[j] == curr_elem[i]:
                        operations.append({
                            "type": "swap",
                            "sequence": seq_name,
                            "indices": [i, j],
                            "from_values": [prev_elem[i], prev_elem[j]],
                            "to_values": [curr_elem[i], curr_elem[j]],
                            "semantic_state": "modified"
                        })
                    else:
                        operations.append({
                            "type": "mutation",
                            "sequence": seq_name,
                            "indices": [i, j],
                            "from_values": [prev_elem[i], prev_elem[j]],
                            "to_values": [curr_elem[i], curr_elem[j]],
                            "semantic_state": "modified"
                        })
                elif len(diffs) == 1:
                    i = diffs[0]
                    operations.append({
                        "type": "mutation",
                        "sequence": seq_name,
                        "index": i,
                        "from_value": prev_elem[i],
                        "to_value": curr_elem[i],
                        "semantic_state": "modified"
                    })
                elif len(diffs) > 2:
                    operations.append({
                        "type": "shift",
                        "sequence": seq_name,
                        "indices": diffs,
                        "from_values": [prev_elem[k] for k in diffs],
                        "to_values": [curr_elem[k] for k in diffs],
                        "semantic_state": "modified"
                    })

    return operations

    return operations


def detect_events(
    prev_sequences: Dict[str, Dict[str, Any]],
    curr_sequences: Dict[str, Dict[str, Any]],
    ast_compares: List[ast.Compare],
    ast_subscripts: List[ast.Subscript],
    raw_locals: Dict[str, Any],
    operations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate normalized, high-level execution events with universal semantic states:
    - compare, swap, shift, mutation (active, modified)
    - matrix_access, row_complete, column_complete (active, completed)
    - search_range, visit, reject, found (discovered, active, rejected, found)
    """
    events: List[Dict[str, Any]] = []

    # 1. Map lower-level operations directly into standardized events
    for op in operations:
        op_type = op.get("type")
        if op_type == "comparison":
            events.append({
                "type": "compare",
                "target": op.get("sequence"),
                "indices": op.get("indices", []),
                "semantic_state": "active",
                "meta": {}
            })
        elif op_type == "swap":
            events.append({
                "type": "swap",
                "target": op.get("sequence"),
                "indices": op.get("indices", []),
                "from_values": op.get("from_values", []),
                "to_values": op.get("to_values", []),
                "semantic_state": "modified",
                "meta": {}
            })
        elif op_type == "shift":
            events.append({
                "type": "shift",
                "target": op.get("sequence"),
                "indices": op.get("indices", []),
                "meta": {},
                "semantic_state": "modified"
            })
        elif op_type == "mutation":
            events.append({
                "type": "mutation",
                "target": op.get("sequence"),
                "index": op.get("index"),
                "indices": op.get("indices", []),
                "semantic_state": "modified",
                "meta": {}
            })

    # 2. 2D Matrix accesses: matrix[r][c]
    seen_matrix_access = set()
    for sub in ast_subscripts:
        try:
            if isinstance(sub.value, ast.Subscript) and isinstance(sub.value.value, ast.Name):
                matrix_name = sub.value.value.id
                r = eval_ast_index(sub.value.slice, raw_locals)
                c = eval_ast_index(sub.slice, raw_locals)
                if matrix_name in curr_sequences and curr_sequences[matrix_name].get("is_2d_matrix"):
                    rows = curr_sequences[matrix_name]["rows"]
                    cols = curr_sequences[matrix_name]["cols"]
                    if r is not None and c is not None and 0 <= r < rows and 0 <= c < cols:
                        key = f"{matrix_name}:{r}:{c}"
                        if key not in seen_matrix_access:
                            seen_matrix_access.add(key)
                            matrix_data = curr_sequences[matrix_name].get("matrix_elements")
                            cell_val = matrix_data[r][c] if matrix_data and r < len(matrix_data) and c < len(matrix_data[r]) else None
                            events.append({
                                "type": "matrix_access",
                                "target": matrix_name,
                                "row": r,
                                "col": c,
                                "indices": [r, c],
                                "value": cell_val,
                                "semantic_state": "active",
                                "meta": {"rows": rows, "cols": cols}
                            })
                            if c == cols - 1:
                                events.append({
                                    "type": "row_complete",
                                    "target": matrix_name,
                                    "row": r,
                                    "semantic_state": "completed",
                                    "meta": {}
                                })
                            if r == rows - 1:
                                events.append({
                                    "type": "column_complete",
                                    "target": matrix_name,
                                    "col": c,
                                    "semantic_state": "completed",
                                    "meta": {}
                                })
        except Exception:
            pass

    # 3. Searching patterns: binary search interval & search visit/reject/found
    for seq_name, seq_info in curr_sequences.items():
        if seq_info.get("is_2d_matrix"):
            continue
        elems = seq_info.get("elements", [])
        length = seq_info.get("length", 0)

        # Binary search interval tracking
        if "low" in raw_locals and "high" in raw_locals:
            low = raw_locals.get("low")
            high = raw_locals.get("high")
            mid = raw_locals.get("mid")
            if isinstance(low, int) and isinstance(high, int):
                events.append({
                    "type": "search_range",
                    "target": seq_name,
                    "low": low,
                    "mid": mid if isinstance(mid, int) else None,
                    "high": high,
                    "semantic_state": "discovered",
                    "meta": {}
                })

        # Searching visit / found tracking
        for comp in operations:
            if comp.get("type") == "comparison" and comp.get("sequence") == seq_name:
                indices = comp.get("indices", [])
                if len(indices) == 1:
                    idx = indices[0]
                    if 0 <= idx < length:
                        events.append({
                            "type": "visit",
                            "target": seq_name,
                            "index": idx,
                            "value": elems[idx] if idx < len(elems) else None,
                            "semantic_state": "active",
                            "meta": {}
                        })
                        # Candidate search target resolution
                        target_val = None
                        for target_key in ("target", "key", "val", "query", "target_val"):
                            if target_key in raw_locals:
                                target_val = raw_locals[target_key]
                                break

                        if target_val is not None and elems and idx < len(elems) and elems[idx] == target_val:
                            events.append({
                                "type": "found",
                                "target": seq_name,
                                "index": idx,
                                "indices": [idx],
                                "value": elems[idx],
                                "semantic_state": "found",
                                "meta": {"reason": "target_matched"}
                            })
                            events.append({
                                "type": "search_found",
                                "target": seq_name,
                                "index": idx,
                                "indices": [idx],
                                "value": elems[idx],
                                "semantic_state": "found",
                                "meta": {"reason": "target_matched"}
                            })
                        elif target_val is not None:
                            events.append({
                                "type": "reject",
                                "target": seq_name,
                                "index": idx,
                                "indices": [idx],
                                "semantic_state": "rejected",
                                "meta": {"reason": "target_mismatch"}
                            })
                            events.append({
                                "type": "search_rejected",
                                "target": seq_name,
                                "index": idx,
                                "indices": [idx],
                                "semantic_state": "rejected",
                                "meta": {"reason": "target_mismatch"}
                            })

    return events


def enrich_semantic_events(steps: List[Dict[str, Any]], recognition: Dict[str, Any], code_str: str) -> None:
    """
    Second-pass semantic state resolution engine.
    Applies algorithm-specific finality and success rules based on verifiable execution evidence:
    - Bubble Sort: finalizes pass boundaries (n - 1 - pass), early exit on 0 swaps, and terminal completion.
    - Selection Sort: finalizes min element placement at index i, and terminal completion.
    - Insertion Sort: marks prefixes as discovered segments, never finalizing until the full sort completes.
    - Merge Sort & Quick Sort: marks partitions/slices as discovered, finalizing pivots and terminal completion.
    - Searching (Linear, Binary, Sentinel): strictly emits found ONLY on exact target verification; leaves non-found neutral/rejected.
    - Two Sum: marks matching pointer pair as found.
    - Matrices: maintains active access and visited cell semantics without false green coloring.
    """
    if not steps:
        return

    algo_name = (recognition.get("algorithm") or "").lower()
    algo_type = (recognition.get("type") or "").lower()
    algo_cat = (recognition.get("category") or "").lower()
    code_lower = code_str.lower()

    # 1. Guarantee semantic_state exists on all events across all steps
    for st in steps:
        for ev in st.get("events", []):
            if "semantic_state" not in ev:
                t = ev.get("type")
                if t in ("compare", "visit", "matrix_access", "call_enter"):
                    ev["semantic_state"] = "active"
                elif t in ("swap", "mutation", "shift"):
                    ev["semantic_state"] = "modified"
                elif t in ("found", "search_found"):
                    ev["semantic_state"] = "found"
                elif t in ("reject", "search_rejected"):
                    ev["semantic_state"] = "rejected"
                elif t in ("position_finalized",):
                    ev["semantic_state"] = "finalized"
                elif t in ("search_range", "segment_sorted"):
                    ev["semantic_state"] = "discovered"
                elif t in ("row_complete", "column_complete", "call_return", "operation_completed"):
                    ev["semantic_state"] = "completed"
                else:
                    ev["semantic_state"] = "neutral"

    # Identify primary sequence name and length
    primary_seq = None
    seq_len = 0
    for st in steps:
        seqs = st.get("sequences", {})
        for sname, sinfo in seqs.items():
            if not sinfo.get("is_2d_matrix") and sinfo.get("length", 0) > 1:
                primary_seq = sname
                seq_len = sinfo.get("length", 0)
                break
        if primary_seq:
            break

    # 2. Bubble Sort Finality
    is_bubble = (algo_name == "bubble_sort" or "bubble" in algo_type or ("bubble" in code_lower and "sort" in code_lower))
    if is_bubble and primary_seq and seq_len > 1:
        pass_steps: Dict[int, List[int]] = {}
        for s_idx, st in enumerate(steps):
            loc = st.get("locals_snapshot", {})
            i_val = loc.get("i")
            if isinstance(i_val, int):
                pass_steps.setdefault(i_val, []).append(s_idx)

        # For each completed pass p, finalize index (seq_len - 1 - p) at the last step of that pass
        for p, s_list in pass_steps.items():
            final_idx = seq_len - 1 - p
            if 0 <= final_idx < seq_len and s_list:
                end_step = s_list[-1]
                steps[end_step]["events"].append({
                    "type": "position_finalized",
                    "target": primary_seq,
                    "index": final_idx,
                    "indices": [final_idx],
                    "semantic_state": "finalized",
                    "meta": {"reason": f"bubble_pass_{p}_complete", "finalized_index": final_idx}
                })
                # Check if pass p completed with no swaps (early termination on 'if not swapped: break')
                end_loc = steps[end_step].get("locals_snapshot", {})
                if end_loc.get("swapped") is False:
                    for rem_idx in range(seq_len):
                        steps[end_step]["events"].append({
                            "type": "position_finalized",
                            "target": primary_seq,
                            "index": rem_idx,
                            "indices": [rem_idx],
                            "semantic_state": "finalized",
                            "meta": {"reason": "bubble_early_exit_sorted", "finalized_index": rem_idx}
                        })

        # Terminal step finalization for all elements
        last_step = steps[-1]
        existing_finalized = {e.get("index") for e in last_step.get("events", []) if e.get("type") == "position_finalized"}
        for rem_idx in range(seq_len):
            if rem_idx not in existing_finalized:
                last_step["events"].append({
                    "type": "position_finalized",
                    "target": primary_seq,
                    "index": rem_idx,
                    "indices": [rem_idx],
                    "semantic_state": "finalized",
                    "meta": {"reason": "sort_complete", "finalized_index": rem_idx}
                })

    # 3. Selection Sort Finality
    is_selection = (algo_name == "selection_sort" or "selection" in algo_type or ("selection" in code_lower and "sort" in code_lower))
    if is_selection and primary_seq and seq_len > 1:
        placed_steps: Dict[int, int] = {}
        for s_idx, st in enumerate(steps):
            loc = st.get("locals_snapshot", {})
            i_val = loc.get("i")
            if isinstance(i_val, int):
                for ev in st.get("events", []):
                    if ev.get("type") in ("swap", "mutation") and ev.get("target") == primary_seq:
                        idxs = ev.get("indices", [ev.get("index")])
                        if i_val in idxs:
                            placed_steps[i_val] = s_idx

        for i_val, s_idx in placed_steps.items():
            if 0 <= i_val < seq_len:
                steps[s_idx]["events"].append({
                    "type": "position_finalized",
                    "target": primary_seq,
                    "index": i_val,
                    "indices": [i_val],
                    "semantic_state": "finalized",
                    "meta": {"reason": f"selection_min_placed_{i_val}", "finalized_index": i_val}
                })

        last_step = steps[-1]
        existing_finalized = {e.get("index") for e in last_step.get("events", []) if e.get("type") == "position_finalized"}
        for rem_idx in range(seq_len):
            if rem_idx not in existing_finalized:
                last_step["events"].append({
                    "type": "position_finalized",
                    "target": primary_seq,
                    "index": rem_idx,
                    "indices": [rem_idx],
                    "semantic_state": "finalized",
                    "meta": {"reason": "sort_complete", "finalized_index": rem_idx}
                })

    # 4. Insertion Sort Prefixes vs Finality
    is_insertion = (algo_name == "insertion_sort" or "insertion" in algo_type or ("insertion" in code_lower and "sort" in code_lower))
    if is_insertion and primary_seq and seq_len > 1:
        for st in steps:
            loc = st.get("locals_snapshot", {})
            i_val = loc.get("i")
            if isinstance(i_val, int) and i_val >= 1:
                st["events"].append({
                    "type": "segment_sorted",
                    "target": primary_seq,
                    "indices": list(range(min(i_val + 1, seq_len))),
                    "semantic_state": "discovered",
                    "meta": {"reason": f"prefix_sorted_{i_val}"}
                })
        last_step = steps[-1]
        existing_finalized = {e.get("index") for e in last_step.get("events", []) if e.get("type") == "position_finalized"}
        for rem_idx in range(seq_len):
            if rem_idx not in existing_finalized:
                last_step["events"].append({
                    "type": "position_finalized",
                    "target": primary_seq,
                    "index": rem_idx,
                    "indices": [rem_idx],
                    "semantic_state": "finalized",
                    "meta": {"reason": "sort_complete", "finalized_index": rem_idx}
                })

    # 5. General Sorting
    is_other_sort = (algo_cat == "sorting" or "sort" in algo_name or "sort" in algo_type) and not (is_bubble or is_selection or is_insertion)
    if is_other_sort and primary_seq and seq_len > 1:
        last_step = steps[-1]
        existing_finalized = {e.get("index") for e in last_step.get("events", []) if e.get("type") == "position_finalized"}
        for rem_idx in range(seq_len):
            if rem_idx not in existing_finalized:
                last_step["events"].append({
                    "type": "position_finalized",
                    "target": primary_seq,
                    "index": rem_idx,
                    "indices": [rem_idx],
                    "semantic_state": "finalized",
                    "meta": {"reason": "sort_complete", "finalized_index": rem_idx}
                })

    # 6. Searching (Linear, Binary, Sentinel)
    is_search = (algo_cat == "searching" or "search" in algo_name or "search" in algo_type or "search" in code_lower or "target" in code_lower)
    if is_search and primary_seq:
        target_val = None
        for tk in ("target", "key", "val", "query", "target_val", "x", "needle", "item"):
            for st in steps:
                loc = st.get("locals_snapshot", {})
                if tk in loc:
                    target_val = loc[tk]
                    break
            if target_val is not None:
                break

        initial_elems = []
        for st in steps:
            seqs = st.get("sequences", {})
            if primary_seq in seqs and seqs[primary_seq].get("elements"):
                initial_elems = seqs[primary_seq]["elements"]
                break
        target_is_present = (target_val is not None and isinstance(initial_elems, list) and target_val in initial_elems)

        if target_is_present:
            actual_target_idx = initial_elems.index(target_val)
            found_emitted = False
            for st in steps:
                for ev in st.get("events", []):
                    if ev.get("type") in ("found", "search_found") and ev.get("target") == primary_seq and (ev.get("index") == actual_target_idx or (isinstance(ev.get("indices"), list) and actual_target_idx in ev.get("indices"))):
                        found_emitted = True
                        ev["index"] = actual_target_idx
                        ev["indices"] = [actual_target_idx]
                        break
                if found_emitted:
                    break

            if not found_emitted:
                for st in steps:
                    for ev in st.get("events", []):
                        if ev.get("target") == primary_seq and (ev.get("index") == actual_target_idx or (isinstance(ev.get("indices"), list) and actual_target_idx in ev.get("indices"))):
                            st["events"].append({
                                "type": "search_found",
                                "target": primary_seq,
                                "index": actual_target_idx,
                                "indices": [actual_target_idx],
                                "value": target_val,
                                "semantic_state": "found",
                                "meta": {"reason": "target_verified"}
                            })
                            st["events"].append({
                                "type": "found",
                                "target": primary_seq,
                                "index": actual_target_idx,
                                "indices": [actual_target_idx],
                                "value": target_val,
                                "semantic_state": "found",
                                "meta": {"reason": "target_verified"}
                            })
                            found_emitted = True
                            break
                    if found_emitted:
                        break
        else:
            # Target was NOT in initial array: strictly strip any found events
            for st in steps:
                st["events"] = [
                    ev for ev in st.get("events", [])
                    if ev.get("type") not in ("found", "search_found") and ev.get("semantic_state") != "found"
                ]

    # 7. Two Sum on Sorted Array or Hash Map
    is_two_sum = ("two_sum" in algo_name or "two sum" in code_lower or ("target" in code_lower and ("pair" in code_lower or "found_pair" in code_lower)))
    if is_two_sum and primary_seq:
        found_pair = None
        target_step = None
        for st in steps:
            loc = st.get("locals_snapshot", {})
            for pk in ("pair", "found_pair", "res", "result"):
                p_val = loc.get(pk)
                if isinstance(p_val, (list, tuple)) and len(p_val) == 2 and all(isinstance(x, int) for x in p_val):
                    found_pair = list(p_val)
                    target_step = st
                    break
            if found_pair:
                break

        if found_pair and target_step is not None:
            target_step["events"].append({
                "type": "search_found",
                "target": primary_seq,
                "indices": found_pair,
                "semantic_state": "found",
                "meta": {"reason": "two_sum_pair_found"}
            })
            target_step["events"].append({
                "type": "found",
                "target": primary_seq,
                "indices": found_pair,
                "semantic_state": "found",
                "meta": {"reason": "two_sum_pair_found"}
            })


class ExecutionTracer:
    """
    Deterministic runtime interception engine.
    Controls execution via sys.settrace, isolates namespaces, and enforces loop boundaries.
    """

    def __init__(self, max_steps: int = 1000, max_seconds: float = 2.0, max_stdout_chars: int = 20000):
        self.max_steps = max_steps
        self.max_seconds = max_seconds
        self.max_stdout_chars = max_stdout_chars
        self.steps: List[Dict[str, Any]] = []
        self.step_count = 0
        self.start_time = 0.0
        self.stdout_buffer = io.StringIO()
        self.last_locals: Dict[str, Any] = {}
        self.last_sequences: Dict[str, Dict[str, Any]] = {}
        self.ast_compares_by_line: Dict[int, List[ast.Compare]] = {}
        self.ast_subscripts_by_line: Dict[int, List[ast.Subscript]] = {}
        self.ast_all_subscripts_by_line: Dict[int, List[ast.Subscript]] = {}
        self.ast_subscript_assigns: Dict[str, Tuple[str, ast.AST]] = {}
        self.ast_loop_lines: Set[int] = set()
        self.op_counts: Dict[str, int] = {
            "comparisons": 0,
            "swaps": 0,
            "assignments": 0,
            "array_accesses": 0,
            "loop_iterations": 0,
            "function_calls": 0,
            "recursive_calls": 0,
            "total": 0,
        }
        self.call_stack: List[Dict[str, Any]] = []
        self.max_recursion_depth: int = 1
        self.user_filename = "<user_code>"
        self.aborted = False
        self.abort_reason: Optional[str] = None

    def _trace_dispatch(self, frame, event: str, arg: Any):
        """
        Main callback hooked into Python's execution frame dispatcher via sys.settrace.
        """
        # Strictly ignore non-user frames (standard library, builtins, tracer internals)
        if frame.f_code.co_filename != self.user_filename:
            return None

        # Check loop guards before recording
        self.step_count += 1
        elapsed = time.monotonic() - self.start_time

        if self.step_count > self.max_steps:
            self.aborted = True
            self.abort_reason = f"Execution exceeded maximum step limit ({self.max_steps} steps)."
            sys.settrace(None)
            raise TraceLimitExceeded(self.abort_reason)

        if elapsed > self.max_seconds:
            self.aborted = True
            self.abort_reason = f"Execution timed out ({self.max_seconds} seconds limit)."
            sys.settrace(None)
            raise TraceTimeout(self.abort_reason)

        # Normalize line number (module call can initialize at line 0 in Python 3.14)
        line_no = frame.f_lineno if frame.f_lineno > 0 else 1

        # Extract local variables, filtering out dunder internals
        raw_locals = {
            k: v for k, v in frame.f_locals.items()
            if not k.startswith("__")
        }

        # Serializable snapshot of locals
        current_snapshot: Dict[str, Any] = {}
        types_snapshot: Dict[str, str] = {}
        for k, v in raw_locals.items():
            current_snapshot[k] = serialize_value(v)
            types_snapshot[k] = type(v).__name__

        # Calculate variable mutations vs step n - 1
        mutations: List[str] = []
        for k, curr_v in current_snapshot.items():
            if k not in self.last_locals or self.last_locals[k] != curr_v:
                mutations.append(k)

        # Update last seen locals for subsequent step comparison
        self.last_locals = copy.deepcopy(current_snapshot)

        # Heuristic detection for active data structures and index pointers
        active_sequences = extract_sequences(raw_locals)
        active_pointers = detect_pointers(raw_locals, active_sequences)

        # Detect operations and high-level normalized events
        compares_on_line = self.ast_compares_by_line.get(line_no, [])
        subscripts_on_line = self.ast_subscripts_by_line.get(line_no, [])
        operations = detect_operations(self.last_sequences, active_sequences, compares_on_line, raw_locals, self.ast_subscript_assigns)
        events = detect_events(self.last_sequences, active_sequences, compares_on_line, subscripts_on_line, raw_locals, operations)
        self.last_sequences = copy.deepcopy(active_sequences)

        # Call stack & recursion tracking
        if event == "call":
            args_dict = {}
            try:
                arg_info = inspect.getargvalues(frame)
                for a in arg_info.args:
                    args_dict[a] = serialize_value(arg_info.locals.get(a))
            except Exception:
                pass
            self.call_stack.append({
                "func_name": frame.f_code.co_name,
                "line_no": line_no,
                "args": args_dict,
                "depth": len(self.call_stack) + 1
            })
            if len(self.call_stack) > self.max_recursion_depth:
                self.max_recursion_depth = len(self.call_stack)
        elif event == "return":
            if len(self.call_stack) > 1:
                self.call_stack.pop()

        is_recursive = False
        if len(self.call_stack) > 1:
            names = [f["func_name"] for f in self.call_stack]
            is_recursive = len(names) > len(set(names))

        # Runtime Operation Counters (Feature 14)
        num_compares = len([op for op in operations if op.get("type") in ("comparison", "compare")])
        num_swaps = len([op for op in operations if op.get("type") == "swap"])
        num_assignments = len(mutations)
        num_accesses = len(self.ast_all_subscripts_by_line.get(line_no, []))
        num_loops = 1 if line_no in self.ast_loop_lines else 0
        num_calls = 1 if event == "call" else 0
        num_recursive = 1 if (event == "call" and is_recursive) else 0

        self.op_counts["comparisons"] += num_compares
        self.op_counts["swaps"] += num_swaps
        self.op_counts["assignments"] += num_assignments
        self.op_counts["array_accesses"] += num_accesses
        self.op_counts["loop_iterations"] += num_loops
        self.op_counts["function_calls"] += num_calls
        self.op_counts["recursive_calls"] += num_recursive
        self.op_counts["total"] = (
            self.op_counts["comparisons"] +
            self.op_counts["swaps"] +
            self.op_counts["assignments"] +
            self.op_counts["array_accesses"] +
            self.op_counts["loop_iterations"] +
            self.op_counts["function_calls"]
        )

        # Capture incremental stdout generated up to this point (bounded by max_stdout_chars)
        current_stdout = self.stdout_buffer.getvalue()
        if len(current_stdout) > self.max_stdout_chars:
            current_stdout = current_stdout[:self.max_stdout_chars] + "\n... [stdout truncated]"

        # Step record payload
        step_record: Dict[str, Any] = {
            "step_index": len(self.steps),
            "line_no": line_no,
            "event_type": event,
            "locals_snapshot": current_snapshot,
            "types": types_snapshot,
            "mutations": mutations,
            "sequences": active_sequences,
            "pointers": active_pointers,
            "operations": operations,
            "events": events,
            "stdout": current_stdout,
            "call_stack": copy.deepcopy(self.call_stack),
            "recursion_info": {
                "depth": len(self.call_stack),
                "max_depth": self.max_recursion_depth,
                "is_recursive": is_recursive
            },
            "cumulative_operations": copy.deepcopy(self.op_counts)
        }

        # Record return value or exception details if present
        if event == "return":
            step_record["return_value"] = serialize_value(arg)
        elif event == "exception":
            exc_type, exc_val, _ = arg
            step_record["exception"] = {
                "type": getattr(exc_type, "__name__", str(exc_type)),
                "message": str(exc_val)
            }

        self.steps.append(step_record)
        return self._trace_dispatch

    def run_trace(self, code_str: str, stdin_data: str = "") -> Dict[str, Any]:
        """
        Execute user code inside an isolated namespace with runtime tracing.
        Supports optional stdin_data for programs calling input().
        Returns complete execution trace payload and execution metadata.
        """
        self.steps = []
        self.step_count = 0
        self.last_locals = {}
        self.last_sequences = {}
        self.ast_compares_by_line = {}
        self.ast_subscripts_by_line = {}
        self.ast_all_subscripts_by_line = {}
        self.ast_subscript_assigns = {}
        self.ast_loop_lines = set()
        self.op_counts = {
            "comparisons": 0,
            "swaps": 0,
            "assignments": 0,
            "array_accesses": 0,
            "loop_iterations": 0,
            "function_calls": 0,
            "recursive_calls": 0,
            "total": 0,
        }
        self.call_stack = []
        self.max_recursion_depth = 1
        self.aborted = False
        self.abort_reason = None
        self.stdout_buffer = io.StringIO()
        has_input = False

        # Phase A: AST Syntax Validation and AST Node Pre-Indexing
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    self.ast_compares_by_line.setdefault(node.lineno, []).append(node)
                elif isinstance(node, ast.Subscript):
                    self.ast_all_subscripts_by_line.setdefault(node.lineno, []).append(node)
                    if isinstance(node.value, ast.Subscript):
                        self.ast_subscripts_by_line.setdefault(node.lineno, []).append(node)
                elif isinstance(node, ast.Assign):
                    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Subscript):
                        if isinstance(node.value.value, ast.Name):
                            self.ast_subscript_assigns[node.targets[0].id] = (node.value.value.id, node.value.slice)
                elif isinstance(node, (ast.For, ast.While)):
                    self.ast_loop_lines.add(node.lineno)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
                    has_input = True
        except Exception:
            self.ast_compares_by_line = {}
            self.ast_subscripts_by_line = {}
            self.ast_all_subscripts_by_line = {}
            self.ast_subscript_assigns = {}
            self.ast_loop_lines = set()

        try:
            compiled_code = compile(code_str, self.user_filename, "exec")
        except SyntaxError as syn_err:
            syn_err_dict = {
                "type": "SyntaxError",
                "message": syn_err.msg or "Invalid syntax",
                "line_no": syn_err.lineno or 1,
                "offset": syn_err.offset or 0
            }
            syn_err_dict["diagnosis"] = diagnose_error(syn_err_dict, code_str)
            return {
                "status": "syntax_error",
                "total_steps": 0,
                "steps": [],
                "error": syn_err_dict,
                "stdout": "",
                "has_input": False,
                "operation_metrics": copy.deepcopy(self.op_counts)
            }

        # Phase B: Execution with redirected stdout & stdin, guarded recursion limit, and sys.settrace
        original_stdout = sys.stdout
        original_stdin = sys.stdin
        sys.stdout = self.stdout_buffer
        sys.stdin = SafeStdin(stdin_data or "")
        self.start_time = time.monotonic()
        orig_recursion_limit = sys.getrecursionlimit()

        sandbox_globals: Dict[str, Any] = {
            "__name__": "__main__",
            "__builtins__": __builtins__
        }

        trace_status = "completed"
        error_info: Optional[Dict[str, Any]] = None

        try:
            # Enforce bounded recursion limit to prevent Python runtime stack overflow
            sys.setrecursionlimit(500)
            sys.settrace(self._trace_dispatch)
            exec(compiled_code, sandbox_globals)
        except TraceLimitExceeded as e:
            trace_status = "step_limit_exceeded"
            error_info = {
                "type": "TraceLimitExceeded",
                "message": str(e),
                "line_no": self.steps[-1]["line_no"] if self.steps else 1
            }
        except TraceTimeout as e:
            trace_status = "timeout"
            error_info = {
                "type": "TraceTimeout",
                "message": str(e),
                "line_no": self.steps[-1]["line_no"] if self.steps else 1
            }
        except Exception as runtime_err:
            trace_status = "exception"
            # Find the line number of failure from the last executed step or traceback
            exc_type = type(runtime_err).__name__
            exc_msg = str(runtime_err)
            line_no = self.steps[-1]["line_no"] if self.steps else 1

            error_info = {
                "type": exc_type,
                "message": exc_msg,
                "line_no": line_no
            }
        finally:
            # Guarantee that trace hook is cleanly removed, recursion limit restored, and streams restored
            sys.settrace(None)
            sys.stdout = original_stdout
            sys.stdin = original_stdin
            try:
                sys.setrecursionlimit(orig_recursion_limit)
            except Exception:
                pass

        final_stdout = self.stdout_buffer.getvalue()
        if len(final_stdout) > self.max_stdout_chars:
            final_stdout = final_stdout[:self.max_stdout_chars] + "\n... [stdout truncated]"

        if error_info:
            error_info["diagnosis"] = diagnose_error(
                error_info,
                code_str,
                self.steps[-1] if self.steps else None
            )

        recognition = recognize_algorithm(code_str)

        # Enrich semantic events with algorithm-specific finality and success
        enrich_semantic_events(self.steps, recognition, code_str)

        # Generate step explanations
        for i, st in enumerate(self.steps):
            prev_st = self.steps[i - 1] if i > 0 else None
            st["explanation"] = generate_step_explanation(st, prev_st, recognition)

        return {
            "status": trace_status,
            "total_steps": len(self.steps),
            "steps": self.steps,
            "error": error_info,
            "stdout": final_stdout,
            "recognition": recognition,
            "has_input": has_input,
            "operation_metrics": copy.deepcopy(self.op_counts)
        }
