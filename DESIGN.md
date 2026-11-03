---
name: Code X-Ray
description: Current visual system and interface contract
colors:
  bg-canvas: "#0b0e14"
  bg-surface: "#11151c"
  bg-header: "#161b22"
  bg-cell: "#161b22"
  border-color: "#242b35"
  text-primary: "#e6edf3"
  text-muted: "#7d8590"
  text-dim: "#484f58"
  accent-active: "#58a6ff"
  accent-mutation: "#d29922"
  accent-discovered: "#39c5bb"
  accent-success: "#3fb950"
  accent-danger: "#f85149"
typography:
  display:
    fontFamily: "JetBrains Mono, Fira Code, SF Mono, Consolas, monospace"
    fontSize: "14px"
    fontWeight: 700
  interface:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Inter, Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  mono:
    fontFamily: "JetBrains Mono, Fira Code, SF Mono, Consolas, monospace"
    fontSize: "12px"
    lineHeight: 1.5
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
rounded:
  sm: "2px"
  md: "4px"
---

# Code X-Ray Design System

## Principles

Code X-Ray is a focused developer workspace, not a marketing dashboard. Prioritize legibility, clear execution state, compact navigation, and predictable timeline behavior. Keep secondary tools discoverable without putting every action in the primary header.

## Palette and semantic meaning

| Meaning | Treatment |
|---|---|
| Neutral | Default cell surface, no semantic highlight |
| Active | Blue, current inspection or execution focus |
| Modified | Amber, value changed |
| Discovered | Teal, candidate/range discovered |
| Found | Green, exact success confirmed by runtime evidence |
| Finalized | Green, final position proven |
| Rejected | Muted red, only where algorithm semantics require it |

Green must not be used for generic activity, comparison, or mutation. Pointer identity colors must not imply success. A previously inspected search item returns to neutral; only the current item may have transient active styling. A missing search target produces no green cell.

## Typography

- Use the interface sans-serif stack for navigation, panel headings, buttons, and prose.
- Use JetBrains Mono or a compatible monospace stack for code, values, indexes, pointer labels, and console output.
- Panel titles use sentence case, standard interface typography, and restrained weight. Avoid all-caps micro-headings.
- Keep metadata secondary to code and visualization.

## Layout

The standard desktop workspace uses two columns: editor and console on the left; runtime inspection and visualization on the right.

- **Header:** 46px standard height. Show Code X-Ray branding and primary workspace navigation. Group secondary utilities in More.
- **Primary workspace:** Python editor, console, variable inspector, sequence/pointer stage, matrix stage when relevant, and step explanation.
- **Step explanation:** Beneath the primary visualization content, not above or inside the main execution controls.
- **Transport bar:** 46px standard height. Keep it focused on first/previous/play/next/last, timeline position, and playback speed.
- **Legal links:** Privacy Policy and Terms belong in the footer, not the primary header.
- **Responsive behavior:** Collapse columns as viewport narrows. Preserve usable editor, timeline, and panel controls without horizontal page overflow.

The stylesheet declares a `--transport-height` token of 60px, while the standard `.transport-bar` rule sets an explicit 46px height. The component rule controls the rendered standard bar; change the token only if the implementation is intentionally changed.

## Components

- **Buttons:** Compact rectangular controls with clear primary/secondary hierarchy.
- **Panels:** Flat surfaces with thin borders and concise sentence-case headings.
- **Editor:** CodeMirror with Python syntax highlighting, line numbers, indentation, and validation feedback.
- **Sequence stage:** 1D values and pointer positions. Motion should explain a real state transition.
- **Matrix stage:** 2D grid with row/column coordinates and trace-backed cell activity.
- **Timeline:** Scrubbing is reversible and derives displayed semantic state from the selected step.
- **More menu:** Group secondary actions such as testing, learning aids, sharing, import/export, density, and help. Do not duplicate all of these as header buttons.

## Motion and accessibility

- Motion clarifies swaps, pointer movement, or state transitions; it must not change trace data.
- Respect `prefers-reduced-motion`.
- Keep focus indicators visible and controls keyboard-operable.
- Avoid distracting persistent animations.

## Do and don't

### Do
- Preserve calm spacing and visual hierarchy.
- Keep semantic colors consistent and evidence-based.
- Make rewind/reset behavior visually exact.
- Use plain language for status labels.

### Don't
- Do not use decorative `//` separators in headings or status text.
- Do not color every visited search cell.
- Do not use green for unconfirmed states.
- Do not claim tree, graph, linked-list, or dynamic-programming visual stages unless implemented.
- Do not crowd the header with secondary actions.
