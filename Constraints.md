# Engineering Constraints & Bans: X-Ray Execution Agent

## 1. Architectural & Dependency Limits
* **Backend:** Python 3 standard library (`sys.settrace`, `ast`, `inspect`, `copy`, `time`, `io`, `json`). Zero external debugger or bytecode instrumentation libraries.
* **Frontend:** Zero bloated UI frameworks, zero component libraries, zero heavy charting packages. Semantic HTML5, CSS Grid / Custom Properties, Vanilla JavaScript only.
* **Network & Security:** No third-party analytics, tracking scripts, or telemetry. All trace executions run locally.

## 2. Strict UI/UX Anti-Vibe-Coding Bans (Zero Tolerance)
* **Banned Gradients:** NO purple gradients, NO neon cyberpunk glows, NO multi-stop linear gradient text fills.
* **Banned Radii:** NO pill-shaped buttons (`border-radius: 9999px` or `50px` is forbidden). Use sharp corners (`0px` to `4px` maximum).
* **Banned Icons:** NO emoji characters anywhere in UI, headers, buttons, logs, or error prompts. Use crisp inline `<svg>` geometric paths only.
* **Banned Punctuation:** NO em dashes (`—`) in UI copy, labels, legal pages, or documentation. Use standard hyphens (`-`), colons (`:`), or periods (`.`).
* **Banned Copy:** NO AI marketing fluff, NO vague hype phrases (e.g., "Unleash the power", "Supercharge", "Next-gen magic"). Use precise technical terminology (e.g., "Deterministic Python Runtime Inspector and Pointer Visualizer").
* **Banned Elements:** NO fake reviews, NO fake testimonials, NO fake metric badges, NO AI-generated stock illustrations.
* **Banned Animations:** NO intrusive scroll animations, NO parallax scrolling, NO custom circle mouse cursors.
* **Banned Watermarks:** NO "Made with AI" labels, generator badges, or automated framework banners.

## 3. Strict Color System Specifications
* Background Primary: `#0b0e14`
* Surface / Panel Background: `#11151c`
* Border Hairlines: `1px solid #242b35`
* Text Primary: `#e6edf3`
* Text Muted: `#7d8590`
* Accent Active Line: `#d29922` (amber highlight)
* Accent Mutation / Pointer A: `#3fb950` (crisp green)
* Accent Pointer B: `#58a6ff` (crisp blue)

## 4. Typography Rules
* Monospace Font Stack: `JetBrains Mono`, `Fira Code`, `SF Mono`, `Consolas`, `monospace`.
* Interface Font Stack: `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Inter`, `Roboto`, `sans-serif`.
