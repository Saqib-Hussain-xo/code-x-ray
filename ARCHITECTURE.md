# Code X-Ray: Architecture and System Design

Code X-Ray is an interactive Python execution visualizer. Its architecture separates static source analysis, runtime capture, semantic enrichment, and browser presentation.

## 1. System topology

```text
Browser
  | CodeMirror editor, input, playback controls
  v
Flask application (app.py)
  |-- /api/validate --> Python AST syntax validation
  |-- /api/presets  --> allowlisted preset metadata
  |-- /api/trace
  |     |-- local route --> ExecutionTracer (tracer.py)
  |     |-- sandbox route --> Judge0SandboxAdapter (sandbox_adapter.py)
  |                              |-- runner submitted to Judge0
  |                              <-- serialized trace in provider output
  |-- /api/compare --> comparison.py
  |-- /api/batch-test --> repeated test-case execution
  |-- recognizer.py: AST pattern recognition
  |-- analyzer.py: static complexity estimates
  |-- explainer.py: step explanations
  |-- diagnostics.py: error diagnostics
  v
JSON response --> browser timeline
  |-- static/js/app.js
  |-- static/js/animator.js
  |-- static/js/matrix-stage.js
  |-- templates/index.html
  |-- static/css/styles.css
```

Judge0 receives a packaged runner remotely. It does not call back into Flask's local `ExecutionTracer`; Flask decodes and parses the trace returned by the provider.

## 2. Backend modules

- **`app.py`:** Flask application, HTML routes, REST endpoints, request validation, rate limiting, and execution-route selection.
- **`tracer.py`:** `sys.settrace` runtime capture; local-variable snapshots, stdout, sequence/matrix data, pointer candidates, call-stack information, operation evidence, semantic events, and configured execution limits.
- **`recognizer.py`:** AST pattern recognition and confidence information. Recognition does not prove algorithm correctness.
- **`analyzer.py`:** Static AST estimates of time and auxiliary-space complexity. These are heuristics, not measurements or formal proofs.
- **`explainer.py`:** Human-readable step explanations based on trace events and source context.
- **`diagnostics.py`:** Explanations and suggestions for supported syntax/runtime errors.
- **`comparison.py`:** Executes two implementations on equivalent inputs and reports output agreement and observed operation deltas.
- **`sandbox_adapter.py`:** Builds a runner, submits it to Judge0, decodes the provider response, and extracts the serialized trace.

### Frontend modules

- `templates/index.html`: workspace structure, navigation, panels, and dialogs.
- `static/js/app.js`: application state, editor integration, execution requests, playback, and timeline rendering.
- `static/js/animator.js`: sequence/pointer visual transitions.
- `static/js/matrix-stage.js`: 2D matrix rendering.
- `static/css/styles.css`: layout, tokens, semantic states, responsive behavior, and reduced-motion rules.

## 3. Execution lifecycle

1. Browser submits source or a preset identifier to `POST /api/trace`.
2. Flask validates the payload and parses source with Python AST.
3. Flask selects local tracing or remote Judge0 according to routing conditions.
4. The selected execution path produces a trace result.
5. Recognition, complexity estimates, explanations, diagnostics, and metadata are attached where available.
6. Flask returns JSON.
7. The frontend renders the selected timeline step. Rewinding must remove semantic states whose events lie in the future.

## 4. Execution routing and trust boundaries

Current `app.py` conditions:

- Trace route defaults `XRAY_EXECUTION_MODE` to `local`.
- `XRAY_ALLOW_LOCAL_EXEC` defaults to `true`.
- Allowlisted presets always use `ExecutionTracer`.
- Custom code uses `ExecutionTracer` when local execution is allowed, when mode is `local`, or when Flask is running tests.
- Only custom-code requests outside tests reach `Judge0SandboxAdapter` when local execution is disabled and mode is not `local`.

Therefore, `XRAY_EXECUTION_MODE=production` alone does **not** force sandbox execution while `XRAY_ALLOW_LOCAL_EXEC=true`. To route custom code through Judge0, set `XRAY_ALLOW_LOCAL_EXEC=false`, choose a non-local mode, and configure `JUDGE0_API_URL` plus provider credentials if required.

The health endpoint independently reports `XRAY_EXECUTION_MODE` with fallback `playground`; the trace route uses `local`.

### Remote request path

```text
Browser -> Flask /api/trace -> Judge0SandboxAdapter
       -> runner submitted to Judge0
       <- encoded provider output containing delimited trace JSON
       -> Flask decodes/parses trace
       -> Browser renders timeline
```

## 5. Semantic event model

The eight primary visual cell states are `neutral`, `active`, `visited`, `modified`, `discovered`, `found`, `finalized`, and `rejected`.

The tracer may also emit lifecycle events such as `completed`. Do not conflate those event types with persistent cell states.

- **Search:** Only the current inspection may receive transient active styling; earlier inspected elements return to neutral. Green is reserved for a runtime-confirmed match.
- **Sorting:** Green finality requires evidence that the final position is proven, not merely that an element was compared or moved.
- **Timeline:** State is derived from events up to the selected step. Rewinding removes future states; reset clears the visualization.

## 6. Analysis versus observation

1. **Static analysis:** syntax validation, AST recognition, and estimated complexity.
2. **Runtime capture:** line/frame events, snapshots, stdout, and observed operation counts.
3. **Semantic enrichment:** explanations and visual-state events derived from source context and runtime evidence.
4. **Presentation:** frontend rendering of the captured trace.

Complexity is estimated statically. Operation counters describe one run. Neither proves theoretical performance.

## 7. Security model

The in-process tracer is not a secure sandbox. AST validation, request/rate limits, step limits, and wall-clock limits are application safeguards only. They do not isolate arbitrary Python from OS access. Use remote Judge0 for untrusted custom code in multi-tenant deployment and verify local execution is disabled in the deployed environment.

## 8. Deployment

Vercel uses `api/index.py` as its Python entry point; `vercel.json` rewrites requests to that function. `Procfile` and `render.yaml` are manifests for a separate hosting workflow, not part of Vercel routing.
