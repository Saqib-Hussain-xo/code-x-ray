"""
Integration verification for frontend contract, preset options, and layout rules.
"""

import json
import re
import unittest
from app import app


class TestFrontendIntegration(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_and_optgroups(self):
        """Verify homepage renders with 25 presets organized into 6 optgroups."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")

        # Required test strings
        self.assertIn("X-Ray // Runtime Inspector", html)
        self.assertIn("Privacy Policy", html)
        self.assertIn("Terms and Conditions", html)

        # 6 optgroups
        optgroups = [
            'label="Two Pointers"',
            'label="Sliding Window"',
            'label="Searching and Arrays"',
            'label="Sorting"',
            'label="Matrices"',
            'label="Stacks, Queues, and Recursion"'
        ]
        for og in optgroups:
            self.assertIn(og, html)

        # Extract option values from inside #preset-select specifically
        preset_select_match = re.search(r'<select id="preset-select"[^>]*>(.*?)</select>', html, re.DOTALL)
        self.assertIsNotNone(preset_select_match)
        select_inner = preset_select_match.group(1)
        option_values = re.findall(r'<option\s+value="([^"]*)"', select_inner)
        self.assertIn("", option_values)
        preset_keys = [v for v in option_values if v != ""]
        self.assertEqual(len(preset_keys), 25, f"Expected 25 preset option values, found {len(preset_keys)}")

        # Verify presets.js contains every one of these 25 keys
        res_presets = self.client.get("/static/js/presets.js")
        self.assertEqual(res_presets.status_code, 200)
        js_content = res_presets.data.decode("utf-8")

        for key in preset_keys:
            self.assertIn(f"{key}:", js_content, f"Key '{key}' missing from presets.js")

    def test_layout_css_rules(self):
        """Verify CSS contains the 2-column layout with left console and expanded sequence stage."""
        res = self.client.get("/static/css/styles.css")
        self.assertEqual(res.status_code, 200)
        css = res.data.decode("utf-8")

        self.assertIn(".workspace-grid", css)
        self.assertIn(".workspace-column", css)
        self.assertIn(".left-column .panel-editor", css)
        self.assertIn(".left-column .panel-console", css)
        self.assertIn(".right-column .panel-memory", css)
        self.assertIn(".right-column .panel-sequence", css)
        self.assertIn("flex: 1.75", css)  # Sequence stage expanded vertical space

    def test_clear_and_init_rules_in_app_js(self):
        """Verify app.js implements handleClear and robust initialization."""
        res = self.client.get("/static/js/app.js")
        self.assertEqual(res.status_code, 200)
        app_js = res.data.decode("utf-8")

        self.assertIn("function handleClear", app_js)
        self.assertIn('presetSelect.value = ""', app_js)
        self.assertIn('codeInput.value = ""', app_js)
        self.assertIn("resetTraceVisuals", app_js)
        self.assertIn('document.readyState === "loading"', app_js)

    def test_console_height_and_sequence_centering_css(self):
        """Verify console is limited to 20-25% height and sequence stage has centering rules."""
        res = self.client.get("/static/css/styles.css")
        self.assertEqual(res.status_code, 200)
        css = res.data.decode("utf-8")

        # Console height reduced to ~20-25%
        self.assertIn("max-height: 25%", css)
        self.assertIn("flex: 3.5", css)

        # Sequence stage centering
        self.assertIn(".sequence-track-inner", css)
        self.assertIn("width: max-content", css)
        self.assertIn("align-items: center", css)

        # Transport Play button standardized dark slate styling
        self.assertIn(".btn-transport.btn-play", css)
        self.assertIn("background-color: #161b22", css)
        self.assertIn(".btn-transport.btn-play.is-playing", css)

    def test_auto_playback_and_timer_guards_in_app_js(self):
        """Verify app.js auto-starts playback on successful trace and prevents timer overlap."""
        res = self.client.get("/static/js/app.js")
        self.assertEqual(res.status_code, 200)
        app_js = res.data.decode("utf-8")

        # Auto playback on success
        self.assertIn("if (data.total_steps > 1) {", app_js)
        self.assertIn("play();", app_js)

        # Timer overlap protection
        self.assertIn("if (playTimer) {", app_js)
        self.assertIn("clearTimeout(playTimer);", app_js)

        # Auto stop at the end
        self.assertIn("pause();", app_js)

        # Sequence centering wrapper
        self.assertIn("sequence-track-inner", app_js)

    def test_editor_gutter_and_line_highlighting(self):
        """Verify HTML, CSS, and JS implement the line gutter and active line highlighting."""
        # HTML structure
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        html = res_html.data.decode("utf-8")
        self.assertIn('id="editor-gutter"', html)
        self.assertIn('id="editor-active-line"', html)
        self.assertIn('class="editor-workspace"', html)

        # CSS styling
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")
        self.assertIn(".editor-gutter", css)
        self.assertIn(".gutter-line", css)
        self.assertIn(".gutter-line.gutter-active", css)
        self.assertIn(".editor-active-line", css)
        self.assertIn("#d29922", css)  # Amber active line color

        # JS implementation
        res_js = self.client.get("/static/js/app.js")
        self.assertEqual(res_js.status_code, 200)
        app_js = res_js.data.decode("utf-8")
        self.assertIn("updateEditorGutter", app_js)
        self.assertIn("highlightEditorLine", app_js)
        self.assertIn("syncEditorScroll", app_js)

    def test_memory_map_transitions_and_new_variables(self):
        """Verify Memory Map differentiates new vs mutated variables and supports transition indicators."""
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")
        self.assertIn(".val-new", css)
        self.assertIn(".status-badge-inline.new", css)
        self.assertIn(".col-status-quiet", css)

        res_js = self.client.get("/static/js/app.js")
        self.assertEqual(res_js.status_code, 200)
        app_js = res_js.data.decode("utf-8")
        self.assertIn('status-badge-inline new', app_js)
        self.assertIn('NEW', app_js)
        self.assertIn('MUTATED', app_js)
        self.assertIn('→', app_js)  # Transition arrow

    def test_phase2_visual_consistency_contracts(self):
        """Verify Phase 2 visual consistency: removal of Diwali fireworks, restrained status pulse, 2px borders, standardized Play button."""
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        html = res_html.data.decode("utf-8")
        # Ensure diwali canvas and spark.js are removed
        self.assertNotIn('id="diwali-canvas"', html)
        self.assertNotIn('spark.js', html)

        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")
        # Ensure diwali canvas/banner styles are removed
        self.assertNotIn(".diwali-canvas", css)
        self.assertNotIn(".diwali-banner", css)

        # Restrained emerald status pulse
        self.assertIn(".status-badge.status-completed.status-completed-pulse", css)
        self.assertIn("@keyframes statusEmeraldPulse", css)

        # Standardized transport play styling with active emerald highlight
        self.assertIn(".btn-transport.btn-play", css)
        self.assertIn(".btn-transport.btn-play.is-playing", css)
        self.assertIn("border-color: #3fb950", css)

        # Refined 2px active and error editor indicators
        self.assertIn(".cm-active-line", css)
        self.assertIn("border-left: 2px solid #d29922", css)
        self.assertIn(".cm-error-line", css)
        self.assertIn("border-left: 2px solid #f85149", css)

        # App.js execution complete handler
        res_app = self.client.get("/static/js/app.js")
        self.assertEqual(res_app.status_code, 200)
        app_js = res_app.data.decode("utf-8")
        self.assertIn("triggerExecutionComplete", app_js)
        self.assertIn("status-completed-pulse", app_js)
        self.assertNotIn("triggerDiwaliSpark", app_js)
        self.assertNotIn("stopDiwaliSpark", app_js)

    def test_active_line_contrast_and_scroll_sync_contracts(self):
        """Verify active-line has unmistakable high contrast and JS synchronizes scroll offsets."""
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")

        # Unmistakable amber active-line styling
        self.assertIn("rgba(210, 153, 34, 0.32)", css)
        self.assertIn("border-left: 2px solid #d29922", css)
        self.assertIn("transparent !important", css)  # Textarea transparency guarantee
        self.assertIn(".gutter-line.gutter-active", css)
        self.assertIn("border-left: 2px solid #d29922", css)

        res_js = self.client.get("/static/js/app.js")
        self.assertEqual(res_js.status_code, 200)
        app_js = res_js.data.decode("utf-8")

        # Synchronization order: syncEditorScroll called after codeInput.scrollTop update
        self.assertIn("syncEditorScroll();", app_js)
        # Raw code preserved without stripping leading lines
        self.assertIn("rawCode", app_js)

    def test_no_cache_headers_and_asset_versioning(self):
        """Verify server injects no-cache headers and templates append asset versions."""
        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        # Check no-cache headers
        self.assertEqual(res_home.headers.get("Cache-Control"), "no-cache, no-store, must-revalidate")
        self.assertEqual(res_home.headers.get("Pragma"), "no-cache")

        html = res_home.data.decode("utf-8")
        self.assertIn("styles.css?v=1.1.0", html)
        self.assertIn("app.js?v=1.1.0", html)

    def test_custom_code_playground_ui_elements(self):
        """Verify Custom Code Playground is default landing mode with required elements."""
        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        html = res_home.data.decode("utf-8")

        # 1. Navigation elements: Custom Code primary, Explore Examples secondary
        self.assertIn('id="tab-custom-code"', html)
        self.assertIn('id="tab-explore-examples"', html)
        self.assertIn("CUSTOM CODE PLAYGROUND", html)

        # 2. Controls: Visualize Code, Reset Example, Clear, and Explore Examples dropdown
        self.assertIn('id="btn-run"', html)
        self.assertIn("Visualize Code", html)
        self.assertIn('id="btn-reset-example"', html)
        self.assertIn('id="btn-clear"', html)
        self.assertIn('id="preset-select"', html)

        # 3. Validation feedback elements
        self.assertIn('id="syntax-status-badge"', html)
        self.assertIn('id="validation-banner"', html)

        # 4. CodeMirror vendor assets linked
        self.assertIn("vendor/codemirror/codemirror.min.css", html)
        self.assertIn("vendor/codemirror/codemirror.min.js", html)
        self.assertIn("vendor/codemirror/python.min.js", html)

        # 5. JavaScript state and logic in app.js
        res_js = self.client.get("/static/js/app.js")
        self.assertEqual(res_js.status_code, 200)
        app_js = res_js.data.decode("utf-8")
        self.assertIn("DEFAULT_PYTHON_EXAMPLE", app_js)
        self.assertIn("handleResetExample", app_js)
        self.assertIn("showSyntaxError", app_js)
        self.assertIn("clearSyntaxValidation", app_js)
        self.assertIn("initCodeMirror", app_js)

        # 6. CSS rules in styles.css
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")
        self.assertIn(".CodeMirror", css)
        self.assertIn(".cm-active-line", css)
        self.assertIn(".cm-error-line", css)
        self.assertIn(".validation-banner", css)
        self.assertIn(".panel-badge-custom", css)

    def test_phase2_animation_system_contracts(self):
        """Verify Phase 2 Unified Animation System script, styles, and lifecycle hooks."""
        # 1. HTML script inclusion
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        html = res_html.data.decode("utf-8")
        self.assertIn("static/js/animator.js", html)

        # 2. Animator script contracts
        res_anim = self.client.get("/static/js/animator.js")
        self.assertEqual(res_anim.status_code, 200)
        anim_js = res_anim.data.decode("utf-8")
        self.assertIn("window.XRayAnimator", anim_js)
        self.assertIn("beforeStepRender", anim_js)
        self.assertIn("afterStepRender", anim_js)
        self.assertIn("cancelAnimations", anim_js)
        self.assertIn("prefers-reduced-motion", anim_js)
        self.assertIn("translateX", anim_js)
        self.assertIn("animateSwap", anim_js)
        self.assertIn("getSwapDuration", anim_js)
        self.assertIn("cell-comparing", anim_js)
        self.assertIn("ghost-projectile-cell", anim_js)
        self.assertIn("sequence-animation-overlay", anim_js)
        self.assertIn("cell-settling", anim_js)

        # 3. App.js animation lifecycle and DOM persistence integration
        res_app = self.client.get("/static/js/app.js")
        self.assertEqual(res_app.status_code, 200)
        app_js = res_app.data.decode("utf-8")
        self.assertIn("XRayAnimator.beforeStepRender", app_js)
        self.assertIn("XRayAnimator.afterStepRender", app_js)
        self.assertIn("XRayAnimator.cancelAnimations", app_js)
        self.assertIn("data-seq-name", app_js)
        self.assertIn("canReuse", app_js)

        # 4. CSS animation rules and reduced motion support
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")
        self.assertIn("--anim-duration", css)
        self.assertIn("pointer-enter", css)
        self.assertIn("blockMutatePulse", css)
        self.assertIn("row-enter", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("cell-comparing", css)
        self.assertIn("cell-settling", css)
        self.assertIn("cellSettle", css)
        self.assertIn("sequence-animation-overlay", css)
        self.assertIn("ghost-projectile-cell", css)

        # 5. Projectile physics contracts in CSS and JS
        self.assertIn("position: fixed", css)
        self.assertIn("zIndex", anim_js)
        self.assertIn("cubic-bezier(0.4, 0.0, 0.2, 1.0)", anim_js)
        self.assertIn("isSteppingBackward", app_js)

    def test_phase1_critical_ux_contracts(self):
        """Verify Phase 1 critical UX contracts: dirty state tracking, modal confirmation, green CTA, responsive toolbar."""
        # 1. Confirm discard modal markup in index.html
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        html = res_html.data.decode("utf-8")
        self.assertIn('id="confirm-modal"', html)
        self.assertIn('id="confirm-modal-title"', html)
        self.assertIn('id="confirm-modal-message"', html)
        self.assertIn('id="confirm-modal-cancel"', html)
        self.assertIn('id="confirm-modal-proceed"', html)
        self.assertIn('class="editor-controls-actions"', html)
        self.assertIn('class="examples-dropdown-wrapper"', html)

        # 2. Dirty tracking and modal handler contracts in app.js
        res_app = self.client.get("/static/js/app.js")
        self.assertEqual(res_app.status_code, 200)
        app_js = res_app.data.decode("utf-8")
        self.assertIn("isEditorDirty", app_js)
        self.assertIn("lastLoadedCode", app_js)
        self.assertIn("requestDiscardConfirmation", app_js)
        self.assertIn("closeConfirmModal", app_js)
        self.assertIn("setEditorCode(DEFAULT_PYTHON_EXAMPLE, true)", app_js)

        # 3. CSS styles: Green CTA, responsive editor controls, modal card styles
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")
        self.assertIn(".btn-primary", css)
        self.assertIn("background-color: #238636", css)
        self.assertIn("border-color: #2ea043", css)
        self.assertIn(".editor-controls-actions", css)
        self.assertIn(".examples-dropdown-wrapper", css)
        self.assertIn(".modal-backdrop", css)
        self.assertIn(".modal-card", css)
        self.assertIn(".btn-danger", css)

    def test_phase3_discoverability_and_shortcuts(self):
        """Verify Phase 3 discoverability: control tooltips, help button, shortcuts modal, focus trapping."""
        # 1. HTML elements: help button, tooltips, and shortcuts modal
        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        html = res_html.data.decode("utf-8")

        self.assertIn('id="btn-shortcuts-help"', html)
        self.assertIn('id="shortcuts-modal"', html)
        self.assertIn('id="shortcuts-modal-title"', html)
        self.assertIn('id="shortcuts-modal-close"', html)
        self.assertIn('id="shortcuts-modal-dismiss"', html)

        # Tooltip hints on controls
        self.assertIn('title="Visualize Code (Ctrl + Enter)"', html)
        self.assertIn('title="First Step (Home)"', html)
        self.assertIn('title="Step Backward (←)"', html)
        self.assertIn('title="Play / Pause (Space)"', html)
        self.assertIn('title="Step Forward (→)"', html)
        self.assertIn('title="Last Step (End)"', html)

        # Tab buttons action clarification
        self.assertIn('title="Focus Custom Code Workspace"', html)
        self.assertIn('title="Explore Algorithm Examples"', html)

        # 2. CSS styles: shortcuts modal and keyboard badge styling
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")

        self.assertIn(".header-help-btn", css)
        self.assertIn(".modal-card-shortcuts", css)
        self.assertIn(".shortcuts-group", css)
        self.assertIn(".shortcuts-group-title", css)
        self.assertIn(".shortcut-item", css)
        self.assertIn(".shortcut-keys", css)
        self.assertIn(".shortcut-keys kbd", css)

        # 3. JavaScript logic: open/close, focus trapping, background blocking
        res_app = self.client.get("/static/js/app.js")
        self.assertEqual(res_app.status_code, 200)
        app_js = res_app.data.decode("utf-8")

        self.assertIn("openShortcutsModal", app_js)
        self.assertIn("closeShortcutsModal", app_js)
        self.assertIn("trapFocusInModal", app_js)
        self.assertIn('shortcutsModal.classList.contains("is-open")', app_js)

    def test_phase4_design_system_and_typography(self):
        """Verify Phase 4 design system: micro-typography tokens, border tokens, zero literal micro font sizes, updated DESIGN.md."""
        res_css = self.client.get("/static/css/styles.css")
        self.assertEqual(res_css.status_code, 200)
        css = res_css.data.decode("utf-8")

        # Centralized micro-typography custom properties
        self.assertIn("--font-size-xs: 11px;", css)
        self.assertIn("--font-size-xxs: 10px;", css)
        self.assertIn("--font-size-micro: 9px;", css)
        self.assertIn("--border-elevated: #30363d;", css)

        # Ensure no literal font-size: 11px, 10px, or 9px remain in styles.css
        literal_micro_sizes = re.findall(r'font-size:\s*(?:11px|10px|9px)\b', css)
        self.assertEqual(
            literal_micro_sizes,
            [],
            f"Found un-tokenized literal micro font sizes in styles.css: {literal_micro_sizes}"
        )

        # Verify DESIGN.md exists and documents layout, syntax tokens, and typography tokens
        with open("DESIGN.md", "r", encoding="utf-8") as f:
            design_md = f.read()

        self.assertIn("responsive two-column desktop workspace", design_md)
        self.assertIn("--font-size-xs", design_md)
        self.assertIn("--border-elevated", design_md)
        self.assertIn("#ff7b72", design_md)  # CodeMirror keyword token



if __name__ == "__main__":
    unittest.main()
