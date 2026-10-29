# X-Ray Execution Agent

A deterministic Python runtime interception engine and visual execution debugger for data structures and algorithms (DSA).

X-Ray steps through Python execution line by line, capturing variable snapshots, mutation diffs, pointer bindings, sequence indices, and standard output at every step.

---

## Architecture Overview

* **Runtime Interception Engine (`tracer.py`)**: Uses Python's native `sys.settrace` frame hooks and AST parsing to capture execution snapshots without external debugging dependencies.
* **Backend Application Server (`app.py`)**: Lightweight Flask HTTP service providing `/api/trace` and `/api/health` endpoints with structured error handling.
* **Frontend Interface (`templates/index.html`, `static/css/styles.css`, `static/js/app.js`)**: Industrial dark-grid developer interface with synchronized code editor, memory map, sequence and pointer stage, console, and playback transport bar.
* **Preset Library (`static/js/presets.js`)**: 25 pre-configured algorithmic examples across 6 categories.
* **Celebration Canvas (`static/js/spark.js`)**: Canvas-based particle burst animation celebrating successful algorithm execution completion.

---

## Prerequisites

* Python 3.10 or newer (tested with Python 3.14).
* Pip package manager.

### Dependencies

```bash
pip install flask
```

No heavy or third-party debugging libraries are required.

---

## Local Startup

1. Open a terminal and navigate to the project directory:
   ```bash
   cd C:\Users\saqib\.gemini\antigravity\scratch\xray
   ```

2. Start the local Flask server:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

To bind to a custom port or host:
```bash
PORT=8080 HOST=0.0.0.0 python app.py
```

---

## Running the Automated Test Suite

Run the complete regression test suite using Python's standard `unittest` runner:

```bash
python -m unittest discover -v
```

The test suite covers:
* `test_tracer.py`: Runtime tracing, dual loop kill switches (steps and timeout), pointer heuristics, sequence extraction, stdout capture, stdout truncation, and recursion depth protection.
* `test_app.py`: Health checks, trace execution, payload validation, code character limits, 128 KB request size limits, template rendering, and SVG favicon delivery.
* `test_presets.py`: Completeness and validity of all 25 algorithm presets across 6 categories.
* `test_frontend_integration.py`: Frontend contracts, editor gutter styling, high-contrast active-line highlight, 2-column grid layout, auto-playback mechanics, and Diwali celebration canvas scripts.

---

## Features & Usage

### 1. Algorithm Presets
Select from 25 algorithms grouped into 6 categories:
* **Two Pointers**: Palindrome, Container With Most Water, 3Sum, Remove Duplicates, Trapping Rain Water, Reverse String.
* **Sliding Window**: Max Sum Subarray, Longest Substring Without Repeating Characters, Minimum Window Substring, Fruit Into Baskets.
* **Searching and Arrays**: Binary Search, Find Peak Element, Search in Rotated Sorted Array, Merge Sorted Arrays, Kadane's Algorithm.
* **Sorting**: Bubble Sort, Selection Sort, Insertion Sort, Dutch National Flag.
* **Matrices**: Matrix Transpose, Spiral Matrix, Set Matrix Zeroes, Rotate Image.
* **Stacks, Queues, and Recursion**: Valid Parentheses, Monotonic Daily Temperatures, Min Stack, Factorial, Fibonacci (Memoized).

### 2. Editor & Code Tracing
* Write custom Python algorithmic code or load presets.
* Click **Run & Trace** (or press `Ctrl+Enter`) to intercept and trace execution.
* The editor features an amber active-line marker (`#d29922`) with synchronized gutter line tracking.
* Click **Clear** to reset the editor and memory stage.

### 3. Visual Debugging Panels
* **Memory Map**: Displays local variables with clear diff indicators:
  * Newly created variables are highlighted with a `NEW` badge.
  * Mutated variables show value transitions (`prev → curr`).
  * Unchanged variables remain visually muted.
* **Sequence & Pointer Stage**: Automatically detects 1D/2D arrays and binds pointer indices (`left`, `right`, `i`, `j`, `mid`) directly to active visual cells.
* **Console Output**: Live incremental standard output capture from `print()` statements.
* **Transport Controls**: Jump to First Step, Step Back, Play/Pause, Step Forward, Jump to Last Step, and adjustable playback speed slider (0.25x to 4.0x).

---

## Security Architecture & Sandboxing Limitations

> [!WARNING]
> **LOCAL DEVELOPMENT AND ISOLATED EDUCATIONAL USE ONLY.**
> This application executes user-submitted Python code using Python's built-in `exec()`. It MUST NOT be exposed directly to untrusted public networks or multi-tenant hosting environments without an external isolation sandbox.

### Built-in In-Process Protections

The application enforces several in-process safeguards:
1. **Request Payload Limit**: Flask `MAX_CONTENT_LENGTH` is enforced at `128 KB` to prevent oversized body attacks.
2. **Code Length Validation**: Code input is capped at `10,000 characters` (~250-300 lines of algorithmic code).
3. **Execution Step Limit**: Strict limit of `1,000 steps` prevents infinite loops.
4. **Wall-Clock Execution Timeout**: Hard cutoff at `2.0 seconds` prevents CPU hogging.
5. **Stdout Buffer Truncation**: Standard output is capped at `20,000 characters` to prevent memory exhaustion from runaway print statements.
6. **Bounded Recursion Limit**: Recursion limit is bounded to `500 frames` during trace execution to protect the C stack.

### Inherent In-Process Sandboxing Limitations

Because code execution occurs within the parent Python process:
* **No Syscall or OS Isolation**: Python's `exec()` can invoke `__import__('os')` or `__import__('subprocess')` to interact with the underlying host OS.
* **Filesystem and Environment Exposure**: User code runs with the file system permissions and environment variables of the running server process.
* **Network Access**: Sockets and HTTP connections are not blocked by `sys.settrace`.
* **C-Extension Blocking**: Calls to blocking C functions (e.g. `time.sleep()`, catastrophic regular expressions) cannot be interrupted by `sys.settrace` until control returns to Python bytecode.

### Requirements for Multi-Tenant Public Deployment

To safely run this service in a production or public multi-tenant environment, the execution tier must be separated from the web tier and executed inside an isolated sandbox runtime:
* **Linux Namespaces / `nsjail` / `seccomp`**: Restrict syscalls, filesystem mounts (read-only root, no `/proc`), network access (disabled), and CPU/memory quotas.
* **gVisor (`runsc`)**: Run execution workers inside a user-space kernel sandbox intercepting all syscalls.
* **MicroVM Isolation (Firecracker / AWS Lambda)**: Execute each trace in an isolated, ephemeral microVM destroyed immediately upon completion.
* **Worker Process Segregation**: Run trace jobs in a non-root, unprivileged subprocess pool over a job queue rather than directly inside the Flask request handler thread.
