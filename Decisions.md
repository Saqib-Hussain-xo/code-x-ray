# Technical Decisions Record: X-Ray Execution Agent

## ADR-001: Tracer Interception Architecture
* **Date:** 2026-10-29
* **Decision:** Use Python standard library `sys.settrace` combined with `io.StringIO` stdout redirection and `ast` validation.
* **Context:** The engine must inspect line-by-line runtime state without bloated third-party dependencies (such as debugger daemons, gdb, or heavy bytecode instruments).
* **Consequences:** Minimal dependency footprint, cross-platform portability, deterministic execution timeline capture. Requires careful handling of internal tracer frame filtering to capture only user code lines.

## ADR-002: Infinite Loop and Resource Bound Guard
* **Date:** 2026-10-29
* **Decision:** Enforce a dual-tier safeguard: maximum 1,000 trace steps and 2.0-second wall-clock timeout.
* **Context:** User code containing infinite `while` loops, runaway recursion, or sentinel errors must not lock or crash the backend worker process.
* **Consequences:** Graceful termination of unresponsive executions with structured error payloads (`status: "timeout"` or `status: "step_limit_exceeded"`), allowing users to debug runaway loops up to the exact point of interruption.

## ADR-003: Pointer and Sequence Binding Heuristic
* **Date:** 2026-10-29
* **Decision:** Dynamically identify integer variables whose names match pointer conventions (`i`, `j`, `k`, `left`, `right`, `l`, `r`, `low`, `high`, `mid`, `slow`, `fast`, `start`, `end`, `idx`) or whose values fall within `[0, len(seq)]`, and map them to their corresponding sequence (`list`, `str`, `tuple`).
* **Context:** DSA algorithms rely heavily on index pointers. Visualizing these pointers directly above/below the memory blocks makes algorithmic operations immediately legible.
* **Consequences:** Backend passes structured `pointers` arrays per step, relieving the frontend from complex sequence-pointer deduction logic.

## ADR-004: Zero Third-Party UI Frameworks (Vanilla Web Stack)
* **Date:** 2026-10-29
* **Decision:** Build the frontend with semantic HTML5, strict CSS Grid/Custom Properties, and modular Vanilla ES6 JavaScript.
* **Context:** Avoid build pipeline complexity, npm bundle bloat, and framework abstraction overhead.
* **Consequences:** Instant load times, high rendering performance during timeline scrubbing, complete control over sharp geometric rendering.

## ADR-005: Backend Framework Choice
* **Date:** 2026-10-29
* **Decision:** Use Python `Flask` (with lightweight virtual environment or standard library fallback) serving clean JSON endpoints and static assets.
* **Context:** Minimalist REST API architecture supporting `/api/trace`, `/api/health`, `/privacy`, and `/terms`.
* **Consequences:** Clean separation of concerns, native static asset hosting, simple deployment readiness.

## ADR-006: Independent 2-Column Flex-Column CSS Grid Layout Architecture
* **Date:** 2026-10-29
* **Decision:** Structure the main application workspace as a 2-column grid (`minmax(420px, 1fr) minmax(480px, 1.2fr)`), where each column is an independent vertical flex container (`display: flex; flex-direction: column`).
* **Context:** In a traditional 2x2 grid, row heights are tightly coupled across columns, locking the Console panel to the exact height of the Sequence & Pointer Stage. The user experience requires the sequence stage to have substantial vertical space (expanded to ~64% column height) for pointer tracks and array cells, while the left column needs the code editor to have primary height (~60%) and the console to have compact auxiliary height (~40%).
* **Consequences:** Complete vertical height independence between the left and right panels, zero grid overflow, and clean responsive collapse to a single column on tablet/mobile screens (<= 1024px).

## ADR-007: Preset Synchronization and Non-Destructive Default State Handling
* **Date:** 2026-10-29
* **Decision:** Model the preset selector with a non-destructive default empty option (`<option value="" selected>Load Algorithm Preset...</option>`), explicit re-selection handling, and clean state resets in `#btn-clear`.
* **Context:** Previously, clearing code or re-selecting the currently selected preset failed to fire browser `change` events because the select element's value remained set to the prior preset key, and a `disabled` default option prevented programmatic reset.
* **Consequences:** Selecting, re-selecting, clearing, and typing custom algorithms in the editor operate reliably without desync, without auto-triggering network execution, and without destroying in-progress custom code unless explicitly requested.

## ADR-008: Non-Destructive Synchronized Textarea Highlighting and Gutter Layer
* **Date:** 2026-10-29
* **Decision:** Implement current-line highlighting and line numbers via a dual-layer architecture: a companion gutter `.editor-gutter` and an absolute highlight backdrop `.editor-highlight-layer` synchronized via scroll and input listeners to a native transparent `<textarea id="code-input">`. Active line uses high-contrast amber (`rgba(210, 153, 34, 0.32)` background, `4px solid #d29922` left border), accompanied by an active gutter indicator (`▶` with gold number `#ffd166`).
* **Context:** A plain `<textarea>` cannot format individual lines directly. Native selections (`setSelectionRange`) hijack the user's cursor and destroy text selections during timeline scrubbing and auto-playback. Full code-editor libraries (e.g. Monaco/CodeMirror) introduce massive bundle weights. Previous low-opacity overlay (12%) was mathematically indistinguishable from background canvas, and calling position calculations before `scrollTop` adjustment caused vertical misalignment.
* **Consequences:** 100% native editing, copy/paste, and tab indentation preserved; cursor position and selection remain untouched during playback; line numbers and bold amber active bar `#d29922` scroll in lockstep with zero layout jitter; code transmitted untrimmed preserves 1-based line alignment.

## ADR-009: In-Process Execution Hardening vs. OS Sandboxing Architecture
* **Date:** 2026-10-29
* **Decision:** Implement safe in-process boundaries (Flask `MAX_CONTENT_LENGTH` 128 KB, 10,000 code character limit, 20,000 stdout character limit, 500-frame recursion limit, sanitized error returns) while strictly avoiding flawed "AST built-in filtering" pseudo-sandboxing; explicitly document the boundary requiring OS-level isolation (e.g. gVisor, nsjail, Firecracker) for multi-tenant deployment.
* **Context:** Python's in-process `exec()` cannot be safely isolated from arbitrary syscalls, filesystem I/O, or network sockets via AST or `__builtins__` restrictions. Naive keyword/AST whitelisting is easily bypassed via subclass gadget chains and creates a false sense of security. True isolation requires operating system process boundaries.
* **Consequences:** Local and educational usage is protected against denial-of-service, runaway memory from giant payloads/print loops, and C-stack overflow, while clear architectural guidelines prevent unsafe deployment in multi-tenant production without external sandboxing.


## ADR-010: Non-Intrusive Canvas Spark Architecture for Execution Completion
* **Date:** 2026-10-29
* **Decision:** Implement the Diwali celebration spark effect via a lightweight fixed HTML5 canvas (`static/js/spark.js`) with `pointer-events: none` and an auto-terminating particle animation loop.
* **Context:** Successful algorithm completion requires celebratory feedback while strictly adhering to industrial tool performance and accessibility standards.
* **Consequences:** Zero UI click interference; stops instantly on manual scrub, clear, or step back; automatically halts animation loops when particles decay (~2.5s) to prevent memory or CPU leaks; respects `prefers-reduced-motion`.

## ADR-011: Isolated Remote Sandbox Adapter with Fail-Closed Enforcement
* **Date:** 2026-10-29
* **Decision:** Integrate a dedicated remote sandbox adapter (`sandbox_adapter.py`) targeting Judge0 CE containerized runtimes for public code evaluation. The Flask web process defaults to sandbox mode and enforces fail-closed behavior: under no circumstances does it fall back to in-process `exec()` if the remote sandbox is unconfigured or fails. In-process execution is restricted to explicitly authorized local developer environments (`XRAY_EXECUTION_MODE=local` and `XRAY_ALLOW_LOCAL_EXEC=true`).
* **Context:** Public exposure of arbitrary Python code execution requires strict OS and container isolation. Self-contained execution runner scripts embed the standard-library tracer and return delimited JSON to the web tier. Sliding-window rate limiting (20 req/min/IP) prevents free-tier quota exhaustion.
* **Consequences:** Safe public web tier deployment; zero host process vulnerability to arbitrary code execution; complete preservation of the existing frontend trace JSON schema.

## ADR-012: Vercel Serverless Deployment with Allowlisted Preset Execution
* **Date:** 2026-10-29
* **Decision:** Deploy the application as a single Vercel project combining the static frontend and Python serverless API (`api/index.py` via `vercel.json`). Restrict execution strictly to a canonical backend allowlist of 25 pre-approved algorithms (`presets_data.py`). Submitting arbitrary Python code is explicitly rejected with HTTP 400 (`ARBITRARY_CODE_EXECUTION_DISABLED`). Trusted preset code is traced directly via in-process `tracer.py`.
* **Context:** Free-tier multi-service deployments (e.g. Vercel frontend + Render backend) suffer from 50 to 90 second spin-up cold starts, cross-origin preflight overhead, and external code execution API rate limits (e.g. Judge0 free tiers). For demonstration and educational showcase purposes, hosting frontend and API on the same Vercel origin provides instant sub-second responses, zero infrastructure cost, and absolute security against remote code execution because the server only executes frozen, vetted algorithm code.
* **Consequences:** Single repository and single Vercel deployment; instant zero-cold-start execution; 100% immune to arbitrary code injection; frontend editor functions in read-only mode with clear preset runner branding; all visual debugging, memory diffs, pointer bindings, step scrubbing, playback, and Diwali animations function identically to previous iterations. Remote sandbox adapter (`sandbox_adapter.py`) and Render manifests (`render.yaml`, `Procfile`) remain preserved in the codebase as inactive reference assets for future multi-tenant sandbox upgrades.

## ADR-013: Custom Code Playground as Primary Experience with CodeMirror and AST Pre-Validation
* **Date:** 2026-10-30
* **Decision:** Transform Code X-Ray into a Custom Code Playground first, with preloaded problems shifted into a secondary "Explore Examples" section. Integrate CodeMirror with dark industrial theme token alignment for Python syntax highlighting, automatic indentation, bracket matching, and line numbering. Provide AST-driven syntax validation via `/api/validate` returning line and column offsets before execution, with error line highlighting in the editor.
* **Context:** Users need an interactive Python visualizer playground where they can immediately write, paste, and debug custom algorithmic code rather than solely stepping through static presets.
* **Consequences:** Default landing experience is an editable Python playground with an introductory palindrome example and primary "Visualize Code" CTA; all 25 presets remain accessible via Explore Examples; syntax errors are caught pre-execution with line/column feedback; execution safety is preserved through input limits, AST validation, and fail-closed sandbox routing. Zero regressions across the full 50-test regression suite.
