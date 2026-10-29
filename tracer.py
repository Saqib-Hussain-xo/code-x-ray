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
            # Format elements for visual memory stage
            element_list = []
            for item in val[:50]:  # Cap stage display items
                element_list.append(serialize_value(item))

            sequences[var_name] = {
                "name": var_name,
                "type": type(val).__name__,
                "length": len(val),
                "elements": element_list,
                "is_nested": any(isinstance(sub, (list, tuple)) for sub in val) if val else False
            }

        elif isinstance(val, str) and len(val) <= 100:
            # Strings are visualized as character cells
            sequences[var_name] = {
                "name": var_name,
                "type": "str",
                "length": len(val),
                "elements": list(val),
                "is_nested": False
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
            "stdout": current_stdout
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

    def run_trace(self, code_str: str) -> Dict[str, Any]:
        """
        Execute user code inside an isolated namespace with runtime tracing.
        Returns complete execution trace payload and execution metadata.
        """
        self.steps = []
        self.step_count = 0
        self.last_locals = {}
        self.aborted = False
        self.abort_reason = None
        self.stdout_buffer = io.StringIO()

        # Phase A: AST Syntax Validation
        try:
            compiled_code = compile(code_str, self.user_filename, "exec")
        except SyntaxError as syn_err:
            return {
                "status": "syntax_error",
                "total_steps": 0,
                "steps": [],
                "error": {
                    "type": "SyntaxError",
                    "message": syn_err.msg or "Invalid syntax",
                    "line_no": syn_err.lineno or 1,
                    "offset": syn_err.offset or 0
                },
                "stdout": ""
            }

        # Phase B: Execution with redirected stdout, guarded recursion limit, and sys.settrace
        original_stdout = sys.stdout
        sys.stdout = self.stdout_buffer
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
            # Guarantee that trace hook is cleanly removed, recursion limit restored, and stdout is restored
            sys.settrace(None)
            sys.stdout = original_stdout
            try:
                sys.setrecursionlimit(orig_recursion_limit)
            except Exception:
                pass

        final_stdout = self.stdout_buffer.getvalue()
        if len(final_stdout) > self.max_stdout_chars:
            final_stdout = final_stdout[:self.max_stdout_chars] + "\n... [stdout truncated]"

        return {
            "status": trace_status,
            "total_steps": len(self.steps),
            "steps": self.steps,
            "error": error_info,
            "stdout": final_stdout
        }
