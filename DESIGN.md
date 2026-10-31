---
name: Code X-Ray
description: Deterministic Python execution inspector and sequence visualizer
colors:
  bg-canvas: "#0b0e14"
  bg-surface: "#11151c"
  bg-header: "#161b22"
  bg-subbar: "#141922"
  bg-cell: "#161b22"
  bg-cell-hover: "#1c222c"
  bg-editor: "#0d1117"
  bg-console: "#080a0f"
  border-color: "#242b35"
  border-subtle: "#1c222b"
  border-elevated: "#30363d"
  border-focus: "#58a6ff"
  text-primary: "#e6edf3"
  text-muted: "#7d8590"
  text-dim: "#484f58"
  accent-active: "#d29922"
  accent-mutation: "#3fb950"
  accent-pointer-a: "#3fb950"
  accent-pointer-b: "#58a6ff"
  accent-danger: "#f85149"
  accent-warning: "#ffd166"
  btn-primary-bg: "#238636"
  btn-primary-border: "#2ea043"
  btn-danger-bg: "#b62324"
  btn-danger-hover: "#da3633"
  badge-blue-bg: "#0d1829"
  badge-blue-border: "#1f3a5f"
  badge-blue-text: "#388bfd"
  btn-play-hover: "#56d364"
  text-white: "#ffffff"
syntax:
  keyword: "#ff7b72"
  def: "#d2a8ff"
  variable: "#e6edf3"
  variable-2: "#79c0ff"
  builtin: "#ffa657"
  string: "#a5d6ff"
  number: "#79c0ff"
  comment: "#8b949e"
  operator: "#ff7b72"
typography:
  display:
    fontFamily: "JetBrains Mono, Fira Code, SF Mono, Consolas, monospace"
    fontSize: "14px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.08em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Inter, Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.04em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Inter, Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0em"
  mono:
    fontFamily: "JetBrains Mono, Fira Code, SF Mono, Consolas, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Inter, Roboto, sans-serif"
    fontSize: "18px"
    fontWeight: 500
    lineHeight: 1
  micro-scale:
    base: "13px"
    sm: "12px"
    xs: "11px"
    xxs: "10px"
    micro: "9px"
rounded:
  sm: "2px"
  md: "4px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "#238636"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "6px 14px"
  button-transport:
    backgroundColor: "{colors.bg-cell}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
  memory-block:
    backgroundColor: "{colors.bg-cell}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    size: "44px"
  card-panel:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "12px"
---

# Code X-Ray Design System

## Overview

Code X-Ray uses a utilitarian, high-density industrial developer interface. The visual design prioritizes information legibility, exact execution state representation, and instantaneous feedback over decorative styling. The aesthetic combines a deep charcoal-black canvas with precision 1px borders, crisp monospaced code and data blocks, and targeted accent highlights for execution lines, pointer indicators, and variable mutations.

## Colors

The color palette is strictly functional, adhering to high-contrast dark-mode principles:
- **Canvas & Surfaces:** Deep charcoal-black (`#0b0e14`) for the global canvas, slate-black (`#11151c`) for panel surfaces, and slightly raised slate (`#161b22`) for headers, memory cells, and transport controls.
- **Borders & Dividers:** Subtle border hairlines (`#242b35` primary, `#1c222b` subtle dividers, `#30363d` elevated modals and transport controls) provide sharp visual separation without high-contrast clutter.
- **Typography:** Crisp white-gray (`#e6edf3`) for primary technical text, muted silver-gray (`#7d8590`) for labels and indexes, and dim charcoal (`#484f58`) for inactive placeholders.
- **Functional Accents:**
  - Active Line / Execution Focus: Warm Amber (`#d29922`)
  - Mutation & Pointer A: Vibrant Green (`#3fb950`)
  - Comparison & Pointer B: Crisp Sky Blue (`#58a6ff`)
  - Error & Danger: Sharp Crimson (`#f85149`)
  - Primary Action CTA: Forest Green (`#238636`, hover `#2ea043`, ring `#3fb950`)

## Typography

Typography establishes clear visual hierarchy between technical data and interface controls:
- **Monospace Stack (`JetBrains Mono`, `Fira Code`, `SF Mono`, `Consolas`, `monospace`):** Applied to all code editors, memory block values, memory map tables, line numbers, variable types, pointer labels, and execution console outputs.
- **Interface Sans Stack (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Inter`, `Roboto`, `sans-serif`):** Applied to panel headers, button labels, modal controls, and settings dialogs.
- **Scale:**
  - Panel Titles: 11px uppercase monospace (`var(--font-size-xs)`) with 0.06em letter spacing.
  - Editor Code: 13px monospace (`var(--font-size-base)`) with 1.5 line height.
  - Line Numbers: 11px monospace (`var(--font-size-xs)`).
  - Memory Cell Content: 13px bold monospace centered within cells.
  - Memory Table Headers & Badges: 10px monospace (`var(--font-size-xxs)`).
  - Pointer Labels & Gutter Markers: 9px bold monospace (`var(--font-size-micro)`).
  - Console Stream: 12px monospace (`var(--font-size-sm)`) with 1.4 line height.

## Layout

The application utilizes a responsive two-column desktop workspace configured via CSS Grid:
- **Header Bar (46px height):** Global branding, Custom Code workspace action, Explore Examples preset launcher, Keyboard Shortcuts help button (`?`), Python 3 runtime badge, and policy links.
- **Left Column:**
  - Panel 1 (Top): Source Script Editor / Custom Code Playground (CodeMirror editor with syntax validation banner and responsive toolbar).
  - Panel 2 (Bottom): Live Execution Console Output (limited to 20-25% height with clear stream and auto-scroll).
- **Right Column:**
  - Panel 3 (Top): Memory Map / Local Scope variable table with change badges (NEW, MUTATED, UNCHANGED).
  - Panel 4 (Bottom): Sequence & Pointer Stage (expanded with `flex: 1.75`) featuring memory blocks and physics-inspired curved projectile swap animations.
- **Transport Bar (52px height):** Fixed bar anchored at the bottom with First, Previous, Play/Pause, Next, and Last controls, timeline scrubber slider, step counter, and playback speed selector (0.5x to 2.0x).

## Indicators & Interactive Feedback

- **Editor Active Line:** Refined 2px solid border (`#d29922`) with `rgba(210, 153, 34, 0.32)` background tint.
- **Editor Error Line:** Refined 2px solid border (`#f85149`) with `rgba(248, 81, 73, 0.25)` background tint.
- **Execution Complete Indicator:** Restrained emerald status pulse (`@keyframes statusEmeraldPulse`) on the status badge displaying `EXECUTION COMPLETE // N STEPS`.
- **Play/Pause Transport Button:** Standardized dark slate styling (`#161b22`, border `#30363d`) during idle or paused states, transitioning to an active emerald highlight (`border-color: #3fb950; color: #3fb950; background-color: rgba(63, 185, 80, 0.15)`) while playing.

## Elevation & Depth

Depth is conveyed through structural border contrasts, subtle dark elevation shadows, and purposeful flight dynamics rather than blurry ambient lighting:
- **Panel Cards:** 1px solid border (`#242b35`) with zero drop shadow to maintain flat technical precision.
- **Elevated Modals & Popovers:** `0 12px 32px rgba(0, 0, 0, 0.7)` with `1px solid var(--border-elevated)` (`#30363d`).
- **Active Swapping Projectiles:** During element swaps, dynamic 3D elevation is applied via Web Animations API:
  - Higher Foreground Arc: `scale(1.16)` with elevated drop shadow `0 24px 36px rgba(0, 0, 0, 0.6), 0 0 20px rgba(88, 166, 255, 0.7)` at apex.
  - Lower Background Arc: `scale(0.92)` with tighter shadow `0 14px 22px rgba(0, 0, 0, 0.45)` at apex.

## Shapes

Shapes are strictly geometric, rectilinear, and utilitarian:
- **Corner Radii:** Strictly limited to `2px` for small controls, buttons, memory blocks, and tags; `4px` maximum for panel cards and dialogs.
- **Pill Buttons:** Strictly prohibited (`border-radius: 9999px` or `50px` is never used).
- **Memory Blocks:** Uniform square cells (44px by 44px) with 2px corner radius and 1px border.

## Components

Standardized UI components:
- **Buttons:**
  - Primary Action (Visualize Code): Solid green background (`#238636`), sharp corners (`2px`), crisp text.
  - Transport Controls: Slate background (`#161b22`), border (`#30363d`), SVG icon glyphs.
  - Ghost / Secondary Buttons: Transparent or slate background, border outline, subtle hover highlight.
- **Modals:** Accessible dialogs with dark backdrop blur, header, title, body, and action buttons (`#confirm-modal` for unsaved custom code protection, `#shortcuts-modal` for keyboard shortcuts reference).
- **Memory Block Cells:** Rectilinear boxes containing value text, subscript/superscript index labels, and color-coded pointer triangles.
- **Timeline Range Scrubber:** Horizontal custom range track with high-contrast amber progress indication.
- **Validation Banner:** Inline notification bar at the top of the editor displaying syntax error line and column without modal interruption.

## Do's and Don'ts

### Do
- Maintain high information density and sharp 1px borders.
- Use monospaced fonts for all execution data, variables, and memory values.
- Keep corner radii sharp (`2px` to `4px`).
- Use inline SVG geometric paths for all interface icons.
- Support `prefers-reduced-motion` across all transition and swap animations.

### Don't
- Do not use purple gradients, multi-stop gradient text, or neon glow effects.
- Do not use pill-shaped buttons or rounded circular bubbles.
- Do not use emoji characters anywhere in UI controls, headers, buttons, or logs.
- Do not use em dashes in user interface labels, error prompts, or documentation.
- Do not add marketing fluff, celebratory badges, or unnecessary decorative illustrations.
