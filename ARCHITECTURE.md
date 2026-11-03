# Code X-Ray: Architecture & System Design

Code X-Ray is an interactive, deterministic execution visualizer and educational code debugger for Data Structures and Algorithms (DSA) in Python.

---

## 1. System Topology

```
+-----------------------------------------------------------------------------------+
|                                 USER BROWSER                                      |
|                                                                                   |
|  [ CodeMirror Editor ] <========> [ Playback Controller / Animator ]             |
|          |                                        |                               |
|          | (User Code / Stdin)                    | (Events, Snapshots, Metrics)  |
|          v                                        v                               |
|  [ /api/trace ] [ /api/validate ] [ /api/compare ] [ /api/batch-test ]            |
+-----------------------------------------------------------------------------------+
                                   |  HTTP JSON API
                                   v
+-----------------------------------------------------------------------------------+
|                             BACKEND RUNTIME (app.py)                              |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |  ExecutionTracer   |   |  AlgorithmRecognizer  |   |   ComplexityAnalyzer   |  |
|  |    (tracer.py)     |   |    (recognizer.py)    |   |     (analyzer.py)      |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
|            |                          |                            |              |
|            v                          v                            v              |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  |   StepExplainer    |   |    ErrorDetective     |   |  ComparisonEngine      |  |
|  |   (explainer.py)   |   |   (diagnostics.py)    |   |    (comparison.py)     |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Modules

### 2.1 Runtime Interception Engine (`tracer.py`)
- Leverages Python's native `sys.settrace` callback dispatch for line-by-line frame inspection.
- Captures serializable local variable states, memory diffs, sequence structures (1D arrays and 2D matrices), pointer variable tracking, standardized execution events, and call stacks.
- Enforces strict dual kill switches:
  - Step Limit: maximum 1000 steps (configurable).
  - Wall-clock Limit: maximum 2.0 seconds execution cutoff.
  - Recursion Limit: bounded recursion depth protection (500 frames) prevents process stack exhaustion.
- Operation Tracking: tracks live runtime metrics for comparisons, swaps, assignments, array accesses, loop iterations, function calls, and recursive calls.

### 2.2 AST Algorithm Recognition (`recognizer.py`)
- Inspects code structure using standard library `ast.walk` and pattern visitors.
- Detects nested iteration passes, tuple swaps, binary search mid-calculation and interval narrowing, sentinel checks, 2D matrix indexing, and recursion.
- Categorizes algorithms with confidence scoring and classifies visualization profiles: `sorting`, `searching`, `matrix`, `recursion`, `two_pointers`, `sliding_window`, and `generic`.

### 2.3 Step-by-Step Explanations (`explainer.py`)
- Synthesizes clear, beginner-friendly textual narratives explaining each execution step.
- Converts normalized events (`compare`, `swap`, `mutation`, `matrix_access`, `search_range`, `visit`, `found`) into educational English text.

### 2.4 Error Detective (`diagnostics.py`)
- Intercepts syntax errors and runtime exceptions (`IndexError`, `ZeroDivisionError`, `NameError`, `TypeError`, `RecursionError`, `TraceLimitExceeded`).
- Generates beginner-friendly explanations with actionable suggestions and line-targeted remediation tips.

### 2.5 Complexity Analyzer (`analyzer.py`)
- Analyzes loop nesting depth, logarithmic steps, dynamic allocations, and recognized algorithm families.
- Computes estimated Big-O time and auxiliary space complexity.
- Pairs static estimates with measured runtime operation metrics and appropriate educational disclaimers.

### 2.6 Comparative Execution Engine (`comparison.py`)
- Executes two code snippets on equivalent input under sandbox safety guards.
- Verifies output equivalence (stdout and terminal variables).
- Calculates operation deltas (comparisons, swaps, assignments, loops, total steps).
- Generates balanced qualitative verdicts without unproven performance claims.

### 2.7 Frontend Architecture
- `templates/index.html`: semantic HTML5 workspace layout with CodeMirror editor, 2D matrix stage, 1D sequence stage, call stack, operation counters, and accessible modal dialogs.
- `static/css/styles.css`: Nordic Deep Slate industrial design system, CSS custom properties, micro-typography tokens (`--font-size-xs`, `--font-size-xxs`, `--font-size-micro`), high-contrast active lines, and reduced-motion compliance.
- `static/js/app.js`: central application state machine controlling playback transport, CodeMirror integration, breakpoints, variable watchpoints, time travel bookmarks, test cases, and glossary.
- `static/js/matrix-stage.js`: dedicated 2D matrix visualizer rendering grid rows, columns, coordinate badges, and cell access highlights.
- `static/js/animator.js`: DOM coordinate projection and projectile swap physics engine.

---

## 3. Data Flow & Event Lifecycle

1. **Submission**: User code is submitted via `/api/trace` or `/api/validate`.
2. **Pre-Validation**: AST parser inspects syntax, loops, and algorithm patterns.
3. **Execution**: `ExecutionTracer` instruments frames via `sys.settrace`, redirecting stdout and tracking cumulative operation metrics.
4. **Enrichment**: Diagnostician attaches error root-cause advice if exceptions occur; Recognizer and Explainer annotate steps with narratives; Analyzer computes Big-O bounds.
5. **Serialization**: JSON timeline payload is delivered to frontend and loaded into the timeline scrubber.
6. **Visualization**: Scrubber updates CodeMirror active line, memory map, sequence/matrix stage, console, operation counter pills, and call stack in lockstep.
