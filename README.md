# Code X-Ray

Python execution visualizer and debugger.

Code X-Ray provides deterministic, step-by-step runtime interception, AST algorithm recognition, memory mapping, sequence animation, and structured educational diagnostics for Python data structures and algorithms.

---

## Overview

Code X-Ray steps through Python execution line by line, capturing variable snapshots, mutation diffs, pointer bindings, sequence indices, call stack frames, and standard output at every step. It bridges the gap between static code and dynamic runtime semantics, rendering complex pointer interactions, sorting passes, search partitions, and 2D grid traversals through an industrial developer interface.

---

## Key Features

### Code Execution and Visualization
- **Python Code Editor:** CodeMirror-powered editor with syntax highlighting, auto-indentation, bracket matching, line numbering, and syntax pre-validation.
- **Step-by-Step Execution:** Single-step forward/backward navigation, continuous autoplay with variable speed control (0.5x, 1x, 2x, 5x), and jump to start/end.
- **Timeline Navigation:** Interactive timeline scrubber with operation counters (comparisons, assignments, swaps, loop cycles).
- **Console Output and Stdin:** Standard output capture and real-time execution feedback.
- **Variable Inspection:** Live memory map showing local scope variables, types, and values at each step.
- **Variable History:** Mutation tracking highlighting changes with visual diff badges.
- **Breakpoints and Watchpoints:** Clickable line numbers to pause execution at critical junctures and watchpoints for specific variable modifications.
- **Call Stack and Recursion:** Active frame tree displaying recursion depth, frame parameters, return values, and call traces.

### Algorithm Intelligence
- **Algorithm Recognition:** AST-based pattern matcher identifying algorithmic families (Sorting, Searching, Two-Pointer, Sliding Window, Matrix Traversal, Tree/Graph, Dynamic Programming).
- **Sorting Visualizations:** Pass-by-pass tracking with physics-inspired projectile swap animations, partition boundaries, and finalized placement indicators.
- **Searching Visualizations:** Target inspection, active comparison highlight, discarded partition dimming, and target-found confirmation.
- **Matrix Visualization:** 2D grid viewer with coordinate badges, row/column indices, scroll support, and cell access tracking.
- **Sequence and Pointer Stage:** Dedicated memory block sequence track with dynamic pointer arrows (e.g., `left`, `right`, `slow`, `fast`, `mid`).
- **Universal Semantic Visualization Engine:** Visual states strictly distinguish `neutral`, `active` (blue), `visited` (slate), `modified` (amber), `discovered` (teal), `found` (green), `finalized` (green), and `rejected` (crimson).
- **Confirmed Sorting Finality:** Green is strictly reserved for mathematically proven final positions (e.g., Bubble Sort pass boundaries, Selection Sort placed minimums) and never applied prematurely.
- **Search Result Verification:** Found targets are confirmed; missing targets leave 0 false-green elements.
- **Reversible Timeline Scrubbing:** Scrubbing backward removes future finalizations and restores past states deterministically.

### Learning and Debugging
- **Learning and Debugging Modes:** Toggle between detailed explanations with variable predictions (Learning) and high-density performance tracing (Debugging).
- **Step Explanations:** Automated semantic explanations contextualizing what occurred on each executed line.
- **Predict-Before-Execute:** Interactive student prompts to guess variable mutations before advancing steps.
- **Error Diagnostics:** Beginner-friendly root-cause analysis for runtime exceptions (IndexError, TypeError, ZeroDivisionError, RecursionError) with remediation hints.
- **Complexity Analysis:** Theoretical time and space complexity breakdown derived from AST loop nesting and recursion.
- **Operation Counters:** Real-time counters tracking comparison, assignment, swap, and loop cycle counts.
- **Algorithm Comparison:** Side-by-side execution comparison tool benchmarking multiple algorithms on identical inputs.
- **Custom Test Cases:** Multi-case validation runner verifying user code against test suites.
- **Glossary:** Comprehensive built-in terminology guide covering foundational algorithmic concepts.

### Data and Sharing
- **Trace Export and Import:** Export complete execution sessions as portable JSON files; re-import traces in fresh sessions with 100% state fidelity.
- **Shareable Code Links:** Compact URL fragment encoding for sharing code snippets without storing user code on the server.
- **25 Preloaded Programming Presets:** Curated collection of canonical DSA problems spanning arrays, two-pointers, sorting, searching, linked lists, trees, graphs, and dynamic programming.

### Interface
- **Responsive Workspace:** Adaptive multi-column layout supporting desktop (1440px, 1280px, 1024px) down to mobile viewport widths.
- **Workspace Density:** Density modes tailored for code analysis and visualization.
- **Collapsible Panels:** Collapsible panels allowing full customization of workspace focus.
- **Contextual More Menu:** Consolidated secondary navigation grouping Testing, Learning, Sharing, and Documentation.
- **Accessible Keyboard Shortcuts:** Comprehensive keyboard navigation (`Space` for play/pause, `Arrow Right`/`Left` for step forward/back, `Home`/`End` for boundaries).

---

## Screenshots

### Initial Workspace
![Initial Code X-Ray Workspace](docs/screenshots/initial_workspace.png)

### Executed Algorithm & Runtime Inspection
![Executed Algorithm Visualization](docs/screenshots/executed_algorithm.png)

---

## Technology Stack

- **Backend:** Python 3.10+ / 3.14, Flask, `sys.settrace`, `ast`
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3 Custom Properties (Design Tokens)
- **Editor:** CodeMirror 5 (Python syntax mode, line numbers, bracket matchers)
- **Styling:** Custom dark-grid theme inspired by industrial developer tooling
- **Testing:** Python `unittest` framework, headless Chrome DOM automation
- **Deployment:** Vercel Serverless Functions (`api/index.py`, `vercel.json`)

---

## Architecture Overview

```
                      +---------------------------------------+
                      |           Browser Frontend            |
                      |  (CodeMirror + SVG Pointer Tracks +   |
                      |   Canvas Animator + Matrix Stage)     |
                      +-------------------+-------------------+
                                          | HTTP / JSON
                                          v
                      +---------------------------------------+
                      |               Flask App               |
                      |               (app.py)                |
                      +----+-------------+---------------+----+
                           |             |               |
             +-------------+             |               +-------------+
             v                           v                             v
+-------------------------+ +-------------------------+ +-------------------------+
|     Execution Tracer    | |   Algorithm Recognizer  | |   Complexity Analyzer   |
|       (tracer.py)       | |     (recognizer.py)     | |      (analyzer.py)      |
+------------+------------+ +------------+------------+ +-------------------------+
             |                           |
             +-------------+-------------+
                           |
                           v
            +------------------------------+
            |  Step Explainer & Diagnoser  |
            |   (explainer.py / diag.py)   |
            +------------------------------+
```

### Module Responsibilities

- **`app.py`:** Main Flask application exposing REST endpoints (`/api/trace`, `/api/validate`, `/api/presets`, `/api/health`, `/api/compare`, `/api/batch-test`), request validation, rate limiting, and HTML route rendering.
- **`tracer.py`:** Core runtime interception engine utilizing `sys.settrace`, AST line preprocessing, dual loop guards (step limit and wall-clock timeout), stdout capture, and the second-pass semantic enrichment engine.
- **`recognizer.py`:** AST pattern recognition system identifying algorithm categories, specific implementations, and confidence ratings.
- **`explainer.py`:** Generates human-readable, educational explanations for each step based on active AST nodes and runtime mutations.
- **`diagnostics.py`:** Exception diagnostic analyzer translating raw Python tracebacks into plain-language explanations with actionable fixes.
- **`analyzer.py`:** Static AST loop analyzer estimating Big-O time and space complexity heuristics.
- **`comparison.py`:** Parallel execution comparator generating step and operation deltas across two algorithm implementations.
- **`sandbox_adapter.py`:** Containerized multi-tenant Judge0 CE fallback adapter with fail-closed security.
- **`static/js/app.js`:** Central frontend application controller orchestrating CodeMirror, playback transport, state hydration, keyboard navigation, and modal management.
- **`static/js/animator.js`:** Physics-based projectile animation engine rendering arc-based swap trajectories across sequence memory blocks.
- **`static/js/matrix-stage.js`:** Adaptive 2D grid rendering controller supporting row/column indexing, responsive cell sizing, and historical access tracking.
- **`static/css/styles.css`:** Comprehensive design system utilizing semantic CSS tokens, CSS grid layouts, and accessibility-compliant focus states.
- **`templates/index.html`:** Semantic HTML5 workspace shell with accessible ARIA landmarks and responsive panel structure.

---

## Project Structure

```
code-x-ray/
├── .gitignore
├── ARCHITECTURE.md
├── IMPLEMENTATION_PROGRESS.md
├── README.md
├── requirements.txt
├── vercel.json
├── app.py
├── tracer.py
├── recognizer.py
├── explainer.py
├── diagnostics.py
├── analyzer.py
├── comparison.py
├── presets_data.py
├── sandbox_adapter.py
├── api/
│   └── index.py
├── docs/
│   └── screenshots/
│       ├── initial_workspace.png
│       └── executed_algorithm.png
├── templates/
│   ├── index.html
│   ├── privacy.html
│   └── terms.html
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── animator.js
│   │   ├── app.js
│   │   ├── matrix-stage.js
│   │   ├── presets.js
│   │   └── spark.js
│   ├── vendor/
│   │   └── codemirror/
│   └── favicon.svg
└── tests/
    ├── test_analyzer.py
    ├── test_app.py
    ├── test_comparison.py
    ├── test_diagnostics.py
    ├── test_explainer.py
    ├── test_frontend_integration.py
    ├── test_presets.py
    ├── test_recognizer.py
    ├── test_sandbox_adapter.py
    ├── test_security_and_edge_cases.py
    ├── test_semantic_visualization.py
    └── test_tracer.py
```

---

## Installation Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Git

### Setup on Windows PowerShell

1. Clone the repository:
   ```powershell
   git clone https://github.com/Saqib-Hussain-xo/code-x-ray.git
   cd code-x-ray
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## Local Development Instructions

Start the local Flask development server:

```powershell
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

To bind to a custom port or host:
```powershell
$env:PORT="8080"; $env:HOST="0.0.0.0"; python app.py
```

---

## Configuration and Environment Variables

Code X-Ray operates out of the box with zero required environment variables for local execution. In production multi-tenant environments, external sandbox execution can be configured via Judge0:

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_ENV` | `production` | Flask runtime environment (`development` / `production`) |
| `PORT` | `5000` | Port for the HTTP server |
| `HOST` | `127.0.0.1` | Network interface to bind |
| `JUDGE0_API_URL` | *(empty)* | Optional Judge0 API endpoint for isolated container execution |
| `JUDGE0_API_KEY` | *(empty)* | Optional Judge0 authentication key |

### Local vs Production Execution
- **Local Mode (Default):** Python execution is handled directly via `ExecutionTracer` with dual loop guards (`max_steps=1000`, `max_seconds=2.0`), isolated namespaces, and stdout truncation (`max_chars=20000`).
- **Sandbox Mode:** When `JUDGE0_API_URL` is set, requests can be routed to an isolated sandbox container with fail-closed security.

---

## Execution Modes

- **Learning Mode:** Designed for students and interview preparation. Displays detailed step explanations, highlights pointer relationships, and prompts students with predict-before-execute challenges.
- **Debugging Mode:** High-density, performance-oriented interface for developers. Displays raw variable mutations, memory addresses, call frame depth, and execution operation metrics with minimal visual commentary.

---

## API Overview

### `POST /api/trace`
Executes Python source code and returns the complete execution trace.
- **Request Body:** `{"code": "string", "mode": "learning"|"debugging"}`
- **Response:**
  ```json
  {
    "status": "completed",
    "total_steps": 23,
    "steps": [
      {
        "step_no": 1,
        "line_no": 2,
        "locals_snapshot": {"left": 0, "right": 6},
        "mutations": ["left"],
        "sequences": {"text": {"elements": ["r","a","c","e","c","a","r"], "length": 7}},
        "events": [{"type": "compare", "indices": [0, 6], "semantic_state": "active"}],
        "explanation": "Comparing text[0] and text[6]"
      }
    ],
    "recognition": {"algorithm": "two_pointer_palindrome", "category": "two_pointer", "confidence": 0.95},
    "complexity": {"time": "O(N)", "space": "O(1)"}
  }
  ```

### `POST /api/validate`
Validates Python syntax before execution using AST parsing.
- **Request Body:** `{"code": "string"}`
- **Response:** `{"valid": true}` or `{"valid": false, "error": "SyntaxError: ...", "line": 3, "column": 5}`

### `GET /api/presets`
Returns metadata and code for all 25 preloaded algorithm presets.

### `GET /api/health`
Health check endpoint reporting service status and runtime version.

### `POST /api/compare`
Executes two algorithms on identical inputs and returns comparison metrics.

### `POST /api/batch-test`
Executes user code against test cases and reports pass/fail assertions.

---

## Testing Instructions

Code X-Ray maintains a comprehensive test suite of 131 automated unit and integration tests.

### Running All Automated Tests
```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

### Test Suite Structure
- **`test_app.py`:** API endpoints, validation, error handling, rate limiting, and route security.
- **`test_tracer.py`:** Dual loop guards, runtime interception, pointer detection, stdout capture, and AST indexing.
- **`test_semantic_visualization.py`:** Universal semantic states, search correctness, sorting finality, and timeline reversibility.
- **`test_recognizer.py`:** AST algorithm pattern detection across canonical DSA problem types.
- **`test_explainer.py`:** Educational explanation generation and formatting.
- **`test_diagnostics.py`:** Runtime exception root-cause diagnostics and remediation suggestions.
- **`test_analyzer.py`:** Big-O time and space complexity heuristics.
- **`test_comparison.py`:** Algorithm comparison benchmarking.
- **`test_presets.py`:** Schema parity between frontend presets and backend definitions.
- **`test_security_and_edge_cases.py`:** Malformed payloads, timeouts, infinite loops, and empty inputs.
- **`test_frontend_integration.py`:** Frontend UI component integration.
- **`test_sandbox_adapter.py`:** Isolated Judge0 CE container fallback adapter.

---

## Security and Sandbox Considerations

- **Dual Loop Kill Switches:** Execution is bounded by a maximum step threshold (`max_steps=1000`) and a strict wall-clock timeout (`max_seconds=2.0`). Infinite loops terminate cleanly without hanging the server.
- **AST Pre-Validation:** Syntax validation rejects malformed code prior to execution.
- **Zero Unsafe Evaluation:** The application does not use `eval()` on user inputs.
- **Payload Limits:** Request bodies are bounded (`max_content_length=1MB`) to prevent denial-of-service.
- **Sensitive Data Isolation:** Server environment variables, credentials, and internals are strictly excluded from execution trace outputs and error responses.
- **Fail-Closed Sandbox:** In multi-tenant environments, the sandbox adapter isolates execution inside ephemeral containers.

---

## Limitations

- Code execution is scoped to pure Python DSA algorithms. Operating system syscalls, filesystem operations, and network sockets are not supported.
- Third-party packages requiring native compilation (e.g., NumPy, Pandas) are not included by design to preserve lightweight execution speed.
- Interactive terminal input (`input()`) is handled via predefined inputs rather than blocking TTY prompts.

---

## Future Improvements

- Tree and Graph visual stages supporting dynamic node-edge layout animations.
- Step-by-step memory pointer address visualization for linked list nodes.
- Execution recording export to animated GIF and SVG formats.
- Python 3 to JavaScript/C++ multi-language execution comparison.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
