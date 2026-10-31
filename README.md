# X-Ray Execution Agent

A deterministic Python runtime interception engine and visual execution debugger for data structures and algorithms (DSA).

X-Ray steps through Python execution line by line, capturing variable snapshots, mutation diffs, pointer bindings, sequence indices, and standard output at every step.

---

## Architecture Overview

* **Serverless Entrypoint (`api/index.py` & `vercel.json`)**: Configured for single-project deployment on Vercel. Directs web traffic to the unified Flask application runtime.
* **Custom Code Playground (`templates/index.html` & `static/js/app.js`)**: Primary landing experience featuring an interactive CodeMirror Python editor with syntax highlighting, automatic indentation, bracket matching, line numbering, and editable custom code.
* **AST Syntax Pre-Validation (`/api/validate`)**: Real-time syntax validator powered by Python standard library `ast.parse` returning exact line and column offsets before execution.
* **Canonical Preset Library (`presets_data.py` & `static/js/presets.js`)**: 25 preloaded DSA algorithm practice problems accessible via the secondary "Explore Examples" dropdown.
* **Runtime Interception Engine (`tracer.py`)**: Uses Python's native `sys.settrace` frame hooks, AST parsing, and stdout redirection to capture deterministic execution snapshots in under 0.05 seconds.
* **Backend Application Server (`app.py`)**: Lightweight Flask HTTP service providing `/api/trace`, `/api/validate`, `/api/presets`, and `/api/health` endpoints with strict input validation and structured error responses.
* **Frontend Interface (`templates/index.html`, `static/css/styles.css`, `static/js/app.js`)**: Nordic Deep Slate developer interface with synchronized code editor, memory map, sequence and pointer stage, console, and playback transport bar.
* **Unified Animation System (`static/js/animator.js`)**: Physics-inspired projectile swap animations, FLIP pointer transitions, operation-aware motion timing, rapid-navigation cancellation, and reduced-motion support.
* **Sandbox Adapter (`sandbox_adapter.py`)**: Isolated Judge0 CE adapter with fail-closed security for containerized multi-tenant execution.

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

No heavy or third-party debugging libraries are required. CodeMirror vendor assets are bundled locally in `static/vendor/codemirror/`.

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

The test suite covers the backend, tracer, sandbox, preset, and frontend integration contracts:
* `test_app.py`: Health checks, custom code execution, AST syntax validation, empty code handling, preset execution, oversized payload limits, rate limiting, template rendering, and SVG favicon delivery.
* `test_presets.py`: 1:1 schema and content verification between frontend `presets.js` and backend `presets_data.py` across all 25 algorithms.
* `test_tracer.py`: Runtime tracing, dual loop kill switches (step limit and wall-clock timeout), pointer heuristics, sequence extraction, stdout capture, stdout truncation, and recursion depth protection.
* `test_frontend_integration.py`: Custom Code Playground UI elements, editor gutter styling, dirty-state protection, keyboard shortcuts, high-contrast active-line highlight, 2-column grid layout, auto-playback mechanics, reduced-motion behavior, and the unified animation system.
* `test_sandbox_adapter.py`: Standalone unit tests verifying the fallback sandbox adapter.

---

## Features & Usage

### 1. Custom Code Playground (Primary Mode)
* Write or paste custom Python code directly into the editor upon landing.
* Click **Visualize Code** (or press `Ctrl+Enter`) to pre-validate syntax and execute line-by-line tracing.
* Real-time AST syntax validation reports exact line and column errors before execution.
* Click **Reset Example** to restore the introductory two-pointer palindrome demonstration.
* Click **Clear** to wipe the editor and visualizer for a fresh script.
* Changing examples or clearing/resetting modified code prompts for confirmation so unsaved work is not lost.

### 2. Explore Examples (25 Preloaded Problems)
Select any problem from the "Explore Examples" dropdown to load its code into the editor:
* **Two Pointers**: Palindrome, Container With Most Water, 3Sum, Remove Duplicates, Trapping Rain Water, Reverse String.
* **Sliding Window**: Max Sum Subarray, Longest Substring Without Repeating Characters, Minimum Window Substring, Fruit Into Baskets.
* **Searching and Arrays**: Binary Search, Find Peak Element, Search in Rotated Sorted Array, Merge Sorted Arrays, Kadane's Algorithm.
* **Sorting**: Bubble Sort, Selection Sort, Insertion Sort, Dutch National Flag.
* **Matrices**: Matrix Transpose, Spiral Matrix, Set Matrix Zeroes, Rotate Image.
* **Stacks, Queues, and Recursion**: Valid Parentheses, Monotonic Daily Temperatures, Min Stack, Factorial, Fibonacci (Memoized).
* Loaded examples are fully editable and do not modify the canonical preset library.

### 3. Visual Debugging Panels
* **Memory Map**: Displays local variables with clear diff indicators:
  * Newly created variables are highlighted with a `NEW` badge.
  * Mutated variables show value transitions (`prev -> curr`).
  * Unchanged variables remain visually muted.
* **Sequence & Pointer Stage**: Automatically detects 1D and 2D arrays and binds pointer indices (`left`, `right`, `i`, `j`, `mid`) directly to active visual cells.
* **Console Output**: Live incremental standard output capture from `print()` statements.
* **Transport Controls**: Jump to First Step, Step Back, Play/Pause, Step Forward, Jump to Last Step, a timeline scrubber, and adjustable playback speed from 0.5x to 2.0x.
* **Animation Feedback**: Pointer indicators glide between cells, while swap operations animate two values along curved foreground and background trajectories without mutating trace data.
* **Motion Preferences**: Animations respect `prefers-reduced-motion` and are cancelled during rapid navigation so the displayed execution state stays synchronized.
* **Keyboard Shortcuts**: `Ctrl+Enter` visualizes code, `Space` toggles playback, arrow keys step through execution, `Home` and `End` jump to the first and last steps, `?` opens the shortcut reference, and `Esc` closes dialogs.

### 4. Interface Design
* Dense, high-contrast Nordic Deep Slate theme with functional amber, green, blue, and crimson state accents.
* CodeMirror editor with synchronized line numbers, active-line highlighting, inline syntax errors, automatic indentation, and bracket matching.
* Responsive two-column workspace with accessible labels, tooltips, focus-managed dialogs, and sharp geometric controls.

---

## Security Architecture

### In-Process Limits & AST Validation
1. **Request Payload Limit**: Flask `MAX_CONTENT_LENGTH` is enforced at `128 KB` to prevent oversized body attacks.
2. **Code Length Validation**: Code input is capped at `10,000 characters`.
3. **Execution Step Limit**: Strict limit of `1,000 steps` prevents infinite loops.
4. **Wall-Clock Execution Timeout**: Hard cutoff at `2.0 seconds` prevents CPU exhaustion.
5. **Stdout Buffer Truncation**: Standard output is capped at `20,000 characters` to prevent memory exhaustion.
6. **Bounded Recursion Limit**: Recursion limit is bounded to `500 frames` during trace execution to protect the C stack.

### Sandboxed Multi-Tenant Execution
* In production environments where arbitrary user execution is enabled without local developer authorization, the `Judge0SandboxAdapter` routes code to isolated containerized sandboxes with fail-closed security.
