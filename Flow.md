# Execution Flow: X-Ray Execution Agent

## 1. System High-Level Topology
```
[ User Browser / UI ]
         │
         │  POST /api/trace { code: "..." }
         ▼
[ Flask / HTTP Backend: app.py ]
         │
         │  run_trace(code_string)
         ▼
[ Core Engine: tracer.py ]
  ├── 1. AST Syntax Check (compile/ast.parse)
  ├── 2. Sandbox Setup (isolated globals dict, restricted builtins)
  ├── 3. sys.settrace Hook Installation
  ├── 4. Step-by-Step Interception ('line', 'call', 'return', 'exception')
  │       ├── Step count & timeout check (max 1000 steps, 2.0s)
  │       ├── Deep copy locals snapshot
  │       ├── Calculate variable mutations vs step n-1
  │       ├── Run sequence and pointer heuristic detection
  │       └── Capture incremental stdout buffer
  └── 5. Produce TracePayload (steps array, execution metadata)
         │
         ▼
[ JSON Response Payload ]
         │
         ▼
[ Frontend App State Machine: app.js ]
  ├── Initialize Timeline (steps[], total_steps, current_step = 0)
  ├── Render Source Code View (editor lines, gutter)
  ├── Sync Active Step (user scrub or play loop):
  │     ├── Highlight active code line (line_no)
  │     ├── Update Local Variables Memory Table (diff highlights)
  │     ├── Render Dynamic Array/String Blocks with SVG Pointers
  │     ├── Update Incremental Stdout Console
  │     └── If final step reached successfully: trigger subtle geometric spark canvas
  └── Listen to Transport Controls (Play, Pause, Step Next, Step Prev, Speed Selector)
```

## 2. Tracer Hook Lifecycle
1. User script compiled to code object `<user_script>`.
2. Interceptor filters out foreign frames (libraries, tracer internal frames), isolating only frames where `frame.f_code.co_filename == "<user_script>"`.
3. State capture triggers on line transitions:
   * Record `line_no` (1-based).
   * Snapshot all primitives and compound collections (`list`, `dict`, `set`, `tuple`, `str`, `int`, `float`, `bool`).
   * Compare with previous snapshot to mark `mutations: ["left", "arr"]`.
   * Bind candidate pointers (`i`, `j`, `left`, `right`) to indexed arrays.
4. If step counter > 1000 or duration > 2.0 seconds, raise `TraceLimitExceeded` exception and close execution safely.
