# Technical Decisions Record: Code X-Ray

This file records the reasoning behind implementation choices. Older entries may describe an earlier project state. The **Current implementation clarifications** section takes precedence wherever a historical ADR conflicts with the current source tree.

## ADR-001: Runtime interception
- **Decision:** Use Python `sys.settrace`, stdout capture, and AST parsing.
- **Reason:** Capture line-level runtime state without a heavyweight debugger dependency.
- **Trade-off:** Tracing is line/frame based; semantic operations require enrichment and should not be presented as native events unless supported by runtime evidence.

## ADR-002: Execution limits
- **Decision:** Apply a maximum of 1,000 trace steps and a 2-second wall-clock limit in the in-process tracer.
- **Reason:** Bound ordinary educational runs and stop runaway examples.
- **Trade-off:** These are application-level limits, not an OS sandbox or a guarantee against every hostile workload. Do not advertise a fixed millisecond termination guarantee.

## ADR-003: Pointer and sequence binding
- **Decision:** Infer likely pointer variables from names and values, then associate them with visible sequences.
- **Reason:** Index variables are central to common DSA algorithms.
- **Trade-off:** This is heuristic. A variable name or an integer falling within a sequence's index range does not prove semantic intent. The UI must not present uncertain associations as guaranteed facts.

## ADR-004: Vanilla frontend
- **Decision:** Use semantic HTML, CSS custom properties, and modular vanilla JavaScript.
- **Reason:** Keep the client lightweight and avoid a build pipeline.
- **Trade-off:** UI state and DOM contracts must be maintained explicitly across modules.

## ADR-005: Flask API
- **Decision:** Use Flask for HTML routes and JSON endpoints.
- **Reason:** Provide a small Python backend that shares tracing implementation with local development.

## ADR-006: Independent workspace columns
- **Decision:** Use a responsive two-column workspace with independent vertical panel stacks.
- **Reason:** Editor/console and runtime visualization need different height allocations.
- **Trade-off:** Responsive breakpoints must preserve usable controls on narrower screens.

## ADR-007: Preset synchronization
- **Decision:** Keep a canonical backend preset allowlist and synchronize it with the frontend.
- **Reason:** Presets should be predictable and repeatable.
- **Trade-off:** The preset API returns metadata summaries; clients should not assume it exposes all source code.

## ADR-008: Code editor
- **Decision:** Use CodeMirror 5 for the editable Python workspace.
- **Reason:** Syntax highlighting, line numbers, indentation, and editor behavior without a frontend build framework.
- **Historical note:** Earlier descriptions referring to a native textarea/highlight overlay are obsolete.

## ADR-009: In-process safeguards versus isolation
- **Decision:** Keep AST validation, request-size limits, output limits, rate limiting, and tracer limits as defensive application safeguards.
- **Reason:** Reduce accidental resource exhaustion and malformed requests.
- **Trade-off:** Python executed in the web process is not safely isolated from OS access. AST filtering or restricted builtins are not a secure sandbox.

## ADR-010: Celebration canvas
- **Historical proposal:** An earlier iteration referenced a canvas spark effect in `static/js/spark.js`.
- **Current status:** That file is absent from the current tracked frontend. Do not describe the effect as active unless the implementation is restored.

## ADR-011: Judge0 adapter
- **Decision:** Keep a Judge0 adapter for remote, containerized execution when the route selects it.
- **Reason:** Untrusted custom code requires an execution boundary outside Flask.
- **Trade-off:** The adapter depends on a configured provider endpoint and credentials where required. Its presence does not mean every request automatically uses Judge0.

## ADR-012: Vercel entry point
- **Decision:** Use `api/index.py` as the Python serverless entry point, with `vercel.json` rewriting requests to it.
- **Reason:** Serve frontend and API from the same Vercel project.
- **Trade-off:** `Procfile` and `render.yaml` describe a separate hosting path; they are not part of Vercel routing.

## ADR-013: Custom code and presets
- **Decision:** Support an editable custom-code playground alongside 25 allowlisted example presets.
- **Reason:** Users need to inspect their own Python code as well as study canonical examples.
- **Trade-off:** Custom-code execution routing must be configured deliberately; AST validation is not a sandbox.

## ADR-014: Animation layer
- **Decision:** Keep sequence/pointer animation in a frontend module separate from the Python execution engine.
- **Reason:** Visual motion should not alter trace data or execution semantics.
- **Trade-off:** The animation layer must support rapid scrubbing, cancellation, and reduced-motion preferences.

## Current implementation clarifications

These notes are checked against the current `app.py`, `sandbox_adapter.py`, `vercel.json`, frontend markup, and tests:

1. **Trace route defaults:** `XRAY_EXECUTION_MODE` defaults to `local`; `XRAY_ALLOW_LOCAL_EXEC` defaults to `true`.
2. **Preset routing:** Allowlisted presets use the local `ExecutionTracer`.
3. **Custom-code routing:** Custom code uses the local tracer if local execution is allowed, the mode is `local`, or the app is running tests. Otherwise it is sent through `Judge0SandboxAdapter`.
4. **Sandbox configuration:** Setting `XRAY_EXECUTION_MODE=production` alone does not force Judge0 while `XRAY_ALLOW_LOCAL_EXEC=true`. Set `XRAY_ALLOW_LOCAL_EXEC=false`, choose a non-local mode, and configure `JUDGE0_API_URL` plus the provider key if required.
5. **Health endpoint mismatch:** The health endpoint reports `XRAY_EXECUTION_MODE` with fallback `playground`, while the trace route falls back to `local`.
6. **Remote flow:** The adapter submits a packaged runner to Judge0. The remote runner returns trace data in provider output; it does not call back into Flask's local tracer.
7. **Complexity:** Big-O output is a static estimate. Runtime operation counters are measurements from one execution. Neither is a formal proof of algorithmic complexity.
8. **Semantic states:** The eight primary cell states are `neutral`, `active`, `visited`, `modified`, `discovered`, `found`, `finalized`, and `rejected`. A tracer lifecycle event such as `completed` is not an additional persistent cell state.
9. **Current interface:** The standard header and transport bar are each 46px; panel headings use sentence case; legal links are in the footer; secondary utilities are grouped in More.
10. **No unsupported stages:** AST recognition or preset subject matter does not establish a dedicated tree, graph, linked-list, or DP visualizer.
