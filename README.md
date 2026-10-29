# X-Ray Execution Agent

A deterministic Python runtime interception engine and visual execution debugger for data structures and algorithms (DSA).

X-Ray steps through Python execution line by line, capturing variable snapshots, mutation diffs, pointer bindings, sequence indices, and standard output at every step.

---

## Architecture Overview

* **Serverless Entrypoint (`api/index.py` & `vercel.json`)**: Configured for single-project deployment on Vercel. Directs web traffic to the unified Flask application runtime.
* **Canonical Preset Allowlist (`presets_data.py`)**: Backend allowlist containing all 25 canonical DSA algorithm presets. Guarantees that only vetted, trusted code can execute on the server.
* **Runtime Interception Engine (`tracer.py`)**: Uses Python's native `sys.settrace` frame hooks, AST parsing, and stdout redirection to capture deterministic execution snapshots in under 0.05 seconds.
* **Backend Application Server (`app.py`)**: Lightweight Flask HTTP service providing `/api/trace`, `/api/presets`, and `/api/health` endpoints with strict input validation and structured error responses.
* **Frontend Interface (`templates/index.html`, `static/css/styles.css`, `static/js/app.js`)**: Industrial dark-grid developer interface with synchronized code editor, memory map, sequence and pointer stage, console, and playback transport bar.
* **Celebration Canvas (`static/js/spark.js`)**: Canvas-based particle burst animation celebrating successful algorithm execution completion.
* **Preserved Fallback Sandbox Adapter (`sandbox_adapter.py`)**: Isolated Judge0 CE adapter kept intact for future sandbox environments if arbitrary user execution is re-enabled.

---

## Deployment to Vercel

The project is structured for single-repository, zero-config deployment on Vercel.

### Option 1: Deploy from GitHub (Recommended)

1. Push this repository to your GitHub account (branch `xray-only` or `main`).
2. Log in to [Vercel](https://vercel.com) and click **Add New Project**.
3. Import the repository.
4. Keep all default project settings:
   * **Framework Preset:** Other
   * **Root Directory:** `./`
   * **Build Command:** None
   * **Output Directory:** None
5. Click **Deploy**.

Vercel automatically detects `vercel.json` and configures the Python serverless runtime at `api/index.py`. The frontend and API are served from the same domain, eliminating cross-origin preflight requests and avoiding any free-tier spin-up sleep delays.

---

## Local Development & Startup

### Prerequisites

* Python 3.10 or newer (tested with Python 3.14).
* Pip package manager.

### Dependencies

```bash
pip install flask
```

No heavy or third-party debugging libraries are required.

### Local Startup

1. Open a terminal and navigate to the project directory:
   ```bash
   cd code-x-ray
   ```

2. Start the local server:
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

The test suite covers 44 automated tests:
* `test_app.py`: Health checks, preset execution, arbitrary code rejection, unknown preset rejection, 128 KB request size limits, template rendering, and SVG favicon delivery.
* `test_presets.py`: 1:1 schema and content verification between frontend `presets.js` and backend `presets_data.py` across all 25 algorithms.
* `test_tracer.py`: Runtime tracing, dual loop kill switches (step limit and wall-clock timeout), pointer heuristics, sequence extraction, stdout capture, stdout truncation, and recursion depth protection.
* `test_frontend_integration.py`: Frontend contracts, editor gutter styling, high-contrast active-line highlight, 2-column grid layout, auto-playback mechanics, and Diwali celebration canvas scripts.
* `test_sandbox_adapter.py`: Standalone unit tests verifying the preserved fallback sandbox adapter.

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

### 2. Preset Runner & Code Tracing
* Select any algorithm from the dropdown. The source code loads automatically into the editor.
* Click **Run & Trace** (or press `Ctrl+Enter`) to intercept and trace execution.
* The editor features an amber active-line marker (`#d29922`) with synchronized gutter line tracking.
* Click **Clear** to reset the editor and memory stage.

### 3. Visual Debugging Panels
* **Memory Map**: Displays local variables with clear diff indicators:
  * Newly created variables are highlighted with a `NEW` badge.
  * Mutated variables show value transitions (`prev -> curr`).
  * Unchanged variables remain visually muted.
* **Sequence & Pointer Stage**: Automatically detects 1D and 2D arrays and binds pointer indices (`left`, `right`, `i`, `j`, `mid`) directly to active visual cells.
* **Console Output**: Live incremental standard output capture from `print()` statements.
* **Transport Controls**: Jump to First Step, Step Back, Play/Pause, Step Forward, Jump to Last Step, and adjustable playback speed slider (0.25x to 4.0x).

---

## Security Architecture

### Public Demo: Server-Side Allowlist Model

To ensure absolute security when deployed publicly on Vercel without requiring external sandbox containers or third-party API quotas:

1. **Allowlist Enforcement**: The backend only executes code associated with a valid `preset_id` from the canonical allowlist (`presets_data.py`).
2. **Arbitrary Code Disabled**: Submissions containing arbitrary Python code without a recognized `preset_id` are rejected immediately with HTTP 400 (`ARBITRARY_CODE_EXECUTION_DISABLED`).
3. **Zero Untrusted Execution**: Because the server never compiles or executes untrusted strings from user requests, remote code execution (RCE) vulnerabilities are completely eliminated by design.
4. **Read-Only Preset Runner**: The frontend editor is configured in read-only mode with a clear `PRESET RUNNER // 25 DSA ALGORITHMS` badge, giving users full freedom to inspect and trace all 25 algorithms without risk of execution faults.

### Multi-Tenant Arbitrary Execution (Future Upgrade Path)

If arbitrary user code execution is re-introduced in a future phase:
* The preserved `sandbox_adapter.py` should be configured with a remote containerized sandbox (such as Judge0 CE or nsjail).
* The web server must enforce fail-closed security, never executing arbitrary user code in-process on the web worker.
