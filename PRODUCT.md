# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users: Python developers, computer science students, educators, and software engineers preparing for technical interviews or debugging algorithms. They use Code X-Ray to inspect step-by-step runtime execution, variable mutability, pointer mechanics, and memory allocation.

## Product Purpose

Code X-Ray (X-Ray Execution Agent) is an interactive developer tool that executes Python code step-by-step and renders live visual representations of local scopes, memory blocks, pointer movements, and console outputs. Success means making abstract programmatic execution and data mutations immediately intuitive and observable without complex IDE setup.

## Positioning

Unlike cloud-heavy, slow, or black-box visualizers, Code X-Ray runs deterministic Python tracing directly in a high-density, multi-panel developer workstation. It combines a live custom code editor, 25 curated algorithmic presets, a synchronized memory table, and a dedicated sequence and pointer stage with physical projectile swap animations.

## Operating Context

Modern desktop and laptop web browsers in educational, development, and interview preparation settings. The user interacts through a unified four-panel layout featuring an interactive code editor, execution transport controls, timeline scrubber, and synchronized memory/sequence stages.

## Capabilities and Constraints

Confirmed capabilities:
- Interactive Custom Code Playground powered by CodeMirror with Python syntax highlighting and validation.
- Standard library execution tracer capturing variable snapshots, sequence mutations, pointer shifts, and comparisons.
- Preset library of 25 algorithms spanning Searching, Sorting, Two Pointers, Sliding Window, Matrices, and Recursion.
- Sequence and pointer stage with physics-inspired 3D curved projectile animations during element swaps.
- Execution transport bar supporting Play, Pause, Step Forward, Step Back, First Step, Last Step, and variable playback speeds (0.25x to 4.0x).
- Live execution console capturing stdout output incrementally.

Confirmed constraints:
- Backend: Standard Python 3 libraries (`sys.settrace`, `ast`, `inspect`, `json`, `copy`). No heavy debugger frameworks.
- Frontend: Vanilla JavaScript, semantic HTML5, CSS Grid / Custom Properties. Zero external component libraries or tracking telemetry.
- Aesthetics: High-density dark industrial palette, sharp corners (0px to 4px maximum, zero pill buttons), zero purple gradients, zero neon glows, zero emojis, zero em dashes.

## Brand Commitments

- Name: Code X-Ray (X-Ray Execution Agent).
- Voice: Precise, technical, concise, authoritative, and educational.
- Color Identity: Canvas `#0b0e14`, Surface `#11151c`, Borders `#242b35`, Text `#e6edf3`, Accent Amber `#d29922`, Accent Green `#3fb950`, Accent Blue `#58a6ff`.
- Typography: Monospace `JetBrains Mono, Fira Code, SF Mono, Consolas, monospace` for data and code; Clean sans-serif for UI labels.

## Evidence on Hand

- Application backend: `app.py`, `tracer.py`, `sandbox_adapter.py`, `presets_data.py`.
- Application frontend: `templates/index.html`, `static/css/styles.css`, `static/js/app.js`, `static/js/animator.js`, `static/js/presets.js`.
- Test suite: 52 unit and integration tests passing cleanly (`python -m unittest discover -v`).
- Documentation: `README.md`, `Constraints.md`, `Decisions.md`, `Bug.md`, `Flow.md`, `Handover.md`.

## Product Principles

1. Truthful Runtime Semantics: Visual state must accurately reflect real Python execution, scoping, reference mutation, and pointer indexing.
2. High-Density Utility: Avoid decorative distractions; prioritize clear code, structured memory blocks, and legible variable tracking.
3. Physical Movement: Algorithmic changes (such as swaps and pointer traversals) must be unmistakably visible through smooth, curved, physics-inspired motion.
4. Uncompromising Accessibility: Maintain sharp contrast, accessible keyboard navigation, ARIA landmarks, and respect for `prefers-reduced-motion`.
5. Zero Vibe-Coding Bloat: Adhere to strict design discipline with zero generic gradients, zero emojis, and zero marketing hype.

## Accessibility & Inclusion

- Keyboard navigability across all transport buttons, timeline scrubber, and editor controls.
- Full contrast compliance between text and background surfaces.
- Accessible focus rings (`:focus-visible`) with 2px solid `#58a6ff` outline.
- Built-in detection and respect for system `prefers-reduced-motion` settings.
