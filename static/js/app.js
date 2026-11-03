/**
 * X-Ray Execution Agent: Frontend Interactive Controller
 * File: static/js/app.js
 *
 * Implements deterministic timeline navigation, live memory diffing,
 * dynamic sequence/pointer rendering, cumulative console synchronization,
 * algorithm preset loading, and custom Python code playground.
 *
 * Strict security & anti-vibe-coding rules:
 * - Zero eval() or unsafe innerHTML insertion of runtime data
 * - Zero em dashes, zero emojis, zero gradients
 * - Monospace precision and robust state synchronization
 */

(function () {
    "use strict";

    // Default introductory Python example for the Custom Code Playground
    const DEFAULT_PYTHON_EXAMPLE = `# Custom Code Playground // Two-Pointer Palindrome Check
def is_palindrome(text: str) -> bool:
    left = 0
    right = len(text) - 1
    while left < right:
        if text[left] != text[right]:
            return False
        left += 1
        right -= 1
    return True

text = "racecar"
result = is_palindrome(text)
print("Is palindrome:", result)
`;

    // 1. State Store
    let traceData = null;           // Full trace payload from /api/trace
    let currentStepIndex = 0;       // Active step pointer
    let isPlaying = false;          // Playback active state
    let playTimer = null;           // Active playback timeout ID
    let isTracing = false;          // API request in-flight flag
    let currentActiveLineNo = null; // Active highlighted source line
    let currentErrorLineNo = null;  // Active syntax error line in editor
    let hasTriggeredCompletionThisRun = false; // Execution completion indicator single-fire guard
    let cmEditor = null;            // CodeMirror editor instance
    const API_BASE_URL = window.XRAY_API_BASE_URL || "";

    // 2. DOM Elements Cache
    const presetSelect = document.getElementById("preset-select");
    const btnRun = document.getElementById("btn-run");
    const btnClear = document.getElementById("btn-clear");
    const btnResetExample = document.getElementById("btn-reset-example");
    const traceStatus = document.getElementById("trace-status");
    const syntaxStatusBadge = document.getElementById("syntax-status-badge");
    const recognitionBadge = document.getElementById("recognition-badge");
    const validationBanner = document.getElementById("validation-banner");
    const validationMessage = document.getElementById("validation-message");
    const tabCustomCode = document.getElementById("tab-custom-code");
    const tabExploreExamples = document.getElementById("tab-explore-examples");

    const codeInput = document.getElementById("code-input");
    const editorGutter = document.getElementById("editor-gutter");
    const editorActiveLine = document.getElementById("editor-active-line");

    const memoryTableBody = document.getElementById("memory-table-body");
    const stageEmpty = document.getElementById("stage-empty");
    const sequencesContainer = document.getElementById("sequences-container");
    const matrixContainer = document.getElementById("matrix-container");
    const consoleOutput = document.getElementById("console-output");
    const consolePre = consoleOutput ? consoleOutput.closest(".console-pre") : null;

    const btnFirst = document.getElementById("btn-first");
    const btnPrev = document.getElementById("btn-prev");
    const btnPlay = document.getElementById("btn-play");
    const btnNext = document.getElementById("btn-next");
    const btnLast = document.getElementById("btn-last");
    const btnBookmark = document.getElementById("btn-bookmark");
    const stepExplanationText = document.getElementById("step-explanation-text");
    const stdinContainer = document.getElementById("stdin-container");
    const stdinInput = document.getElementById("stdin-input");
    const btnToggleStdin = document.getElementById("btn-toggle-stdin");
    const watchpointBadge = document.getElementById("watchpoint-badge");
    const btnPredictToggle = document.getElementById("btn-predict-toggle");
    const predictScoreBadge = document.getElementById("predict-score-badge");

    const varHistoryModal = document.getElementById("variable-history-modal");
    const varHistoryClose = document.getElementById("var-history-close");
    const varHistoryDismiss = document.getElementById("var-history-dismiss");
    const varHistoryName = document.getElementById("var-history-name");
    const varHistoryMutationsCount = document.getElementById("var-history-mutations-count");
    const varHistoryTableBody = document.getElementById("var-history-table-body");

    const predictModal = document.getElementById("predict-modal");
    const predictModalClose = document.getElementById("predict-modal-close");
    const predictModalSkip = document.getElementById("predict-modal-skip");
    const predictModalSubmit = document.getElementById("predict-modal-submit");
    const predictModalPrompt = document.getElementById("predict-modal-prompt");
    const predictInputValue = document.getElementById("predict-input-value");
    const predictFeedback = document.getElementById("predict-feedback");

    const bookmarks = new Set();
    const watchpoints = new Set();
    const breakpoints = new Set();
    let isPredictMode = false;
    let predictStats = { total: 0, correct: 0 };
    let pendingPredictionStep = null;

    const btnContinue = document.getElementById("btn-continue");
    const callStackContainer = document.getElementById("call-stack-container");
    const callStackFrames = document.getElementById("call-stack-frames");
    const callStackDepthLabel = document.getElementById("call-stack-depth-label");
    const recursionBadge = document.getElementById("recursion-badge");

    const errorDetectiveCard = document.getElementById("error-detective-card");
    const errorDetectiveTitle = document.getElementById("error-detective-title");
    const errorDetectiveExplanation = document.getElementById("error-detective-explanation");
    const errorDetectiveSuggestion = document.getElementById("error-detective-suggestion");

    // Phase 4: Code Intelligence & Comparison DOM Cache
    const complexityBadge = document.getElementById("complexity-badge");
    const opCompares = document.querySelector("#op-compares .op-val");
    const opSwaps = document.querySelector("#op-swaps .op-val");
    const opAssignments = document.querySelector("#op-assignments .op-val");
    const opLoops = document.querySelector("#op-loops .op-val");
    const opTotal = document.querySelector("#op-total .op-val");

    const btnCompareModal = document.getElementById("btn-compare-modal");
    const comparisonModal = document.getElementById("comparison-modal");
    const comparisonModalClose = document.getElementById("comparison-modal-close");
    const comparisonModalDismiss = document.getElementById("comparison-modal-dismiss");
    const compareSelectA = document.getElementById("compare-select-a");
    const compareSelectB = document.getElementById("compare-select-b");
    const compareCodeA = document.getElementById("compare-code-a");
    const compareCodeB = document.getElementById("compare-code-b");
    const compareSharedStdin = document.getElementById("compare-shared-stdin");
    const btnRunComparison = document.getElementById("btn-run-comparison");
    const comparisonResults = document.getElementById("comparison-results");
    const comparisonVerdictText = document.getElementById("comparison-verdict-text");
    const comparisonTableBody = document.getElementById("comparison-table-body");
    const compThA = document.getElementById("comp-th-a");
    const compThB = document.getElementById("comp-th-b");

    const timelineScrubber = document.getElementById("timeline-scrubber");
    const stepCounter = document.getElementById("step-counter");
    const speedSelect = document.getElementById("speed-select");

    const confirmModal = document.getElementById("confirm-modal");
    const confirmModalMessage = document.getElementById("confirm-modal-message");
    const confirmModalClose = document.getElementById("confirm-modal-close");
    const confirmModalCancel = document.getElementById("confirm-modal-cancel");
    const confirmModalProceed = document.getElementById("confirm-modal-proceed");

    const btnShortcutsHelp = document.getElementById("btn-shortcuts-help");
    const shortcutsModal = document.getElementById("shortcuts-modal");
    const shortcutsModalClose = document.getElementById("shortcuts-modal-close");
    const shortcutsModalDismiss = document.getElementById("shortcuts-modal-dismiss");

    // Phase 5: Platform Expansion DOM Cache
    const btnModeToggle = document.getElementById("btn-mode-toggle");
    const btnExportTrace = document.getElementById("btn-export-trace");
    const btnImportTrace = document.getElementById("btn-import-trace");
    const inputImportFile = document.getElementById("input-import-file");
    const btnShareLink = document.getElementById("btn-share-link");

    const btnTestCases = document.getElementById("btn-test-cases");
    const testCasesModal = document.getElementById("test-cases-modal");
    const testCasesModalClose = document.getElementById("test-cases-modal-close");
    const testCasesModalDismiss = document.getElementById("test-cases-modal-dismiss");
    const testCasesList = document.getElementById("test-cases-list");
    const btnAddTestCase = document.getElementById("btn-add-test-case");
    const btnRunAllTests = document.getElementById("btn-run-all-tests");
    const testBatchResults = document.getElementById("test-batch-results");
    const testBatchSummary = document.getElementById("test-batch-summary");
    const testBatchDetails = document.getElementById("test-batch-details");

    const btnGlossary = document.getElementById("btn-glossary");
    const glossaryModal = document.getElementById("glossary-modal");
    const glossaryModalClose = document.getElementById("glossary-modal-close");
    const glossaryModalDismiss = document.getElementById("glossary-modal-dismiss");
    const glossarySearchInput = document.getElementById("glossary-search-input");
    const glossaryList = document.getElementById("glossary-list");

    let lastFocusedElementBeforeModal = null;

    let lastLoadedCode = "";
    let activePresetId = "";
    let pendingConfirmAction = null;
    let pendingCancelAction = null;

    // 3. Formatting Helpers
    function formatValue(val) {
        if (val === null) return "None";
        if (val === undefined) return "-";
        if (typeof val === "boolean") return val ? "True" : "False";
        if (typeof val === "string") return `"${val}"`;
        if (typeof val === "number") return String(val);
        if (Array.isArray(val) || (typeof val === "object" && val !== null)) {
            try {
                const str = JSON.stringify(val);
                return str.length > 50 ? str.slice(0, 47) + "..." : str;
            } catch (_) {
                return String(val);
            }
        }
        return String(val);
    }

    function formatCellValue(val) {
        if (val === null) return "None";
        if (val === undefined) return "";
        if (typeof val === "boolean") return val ? "T" : "F";
        if (typeof val === "string") return val;
        if (typeof val === "number") return String(val);
        if (Array.isArray(val)) {
            try {
                const str = JSON.stringify(val);
                return str.length > 10 ? str.slice(0, 8) + ".." : str;
            } catch (_) {
                return "[..]";
            }
        }
        return String(val);
    }

    function updateStatus(text, typeClass) {
        if (!traceStatus) return;
        traceStatus.textContent = text;
        traceStatus.classList.remove("status-running", "status-completed", "status-error");
        if (typeClass) {
            traceStatus.classList.add(typeClass);
        }
    }

    function getEditorCode() {
        if (cmEditor) {
            return cmEditor.getValue();
        }
        return codeInput ? codeInput.value : "";
    }

    function isEditorDirty() {
        const current = getEditorCode().trim();
        if (!current) return false;
        return current !== lastLoadedCode.trim();
    }

    function setEditorCode(code, markClean = false) {
        if (cmEditor) {
            cmEditor.setValue(code);
        }
        if (codeInput) {
            codeInput.value = code;
        }
        if (markClean) {
            lastLoadedCode = code;
        }
        updateEditorGutter();
        syncEditorScroll();
    }

    function requestDiscardConfirmation(message, onProceed, onCancel) {
        if (!isEditorDirty()) {
            onProceed();
            return;
        }

        pendingConfirmAction = onProceed;
        pendingCancelAction = onCancel;

        if (confirmModal) {
            if (confirmModalMessage && message) {
                confirmModalMessage.textContent = message;
            }
            confirmModal.classList.add("is-open");
            confirmModal.setAttribute("aria-hidden", "false");
            if (confirmModalCancel) {
                confirmModalCancel.focus();
            }
        } else {
            if (window.confirm(message || "Discard current custom code?")) {
                onProceed();
            } else if (onCancel) {
                onCancel();
            }
        }
    }

    function closeConfirmModal(proceed = false) {
        if (!confirmModal) return;
        confirmModal.classList.remove("is-open");
        confirmModal.setAttribute("aria-hidden", "true");

        if (proceed) {
            if (pendingConfirmAction) pendingConfirmAction();
        } else {
            if (pendingCancelAction) pendingCancelAction();
        }
        pendingConfirmAction = null;
        pendingCancelAction = null;
    }

    function openShortcutsModal() {
        if (!shortcutsModal) return;
        lastFocusedElementBeforeModal = document.activeElement;
        shortcutsModal.classList.add("is-open");
        shortcutsModal.setAttribute("aria-hidden", "false");
        if (shortcutsModalClose) {
            shortcutsModalClose.focus();
        }
    }

    function closeShortcutsModal() {
        if (!shortcutsModal) return;
        shortcutsModal.classList.remove("is-open");
        shortcutsModal.setAttribute("aria-hidden", "true");
        if (lastFocusedElementBeforeModal && typeof lastFocusedElementBeforeModal.focus === "function") {
            lastFocusedElementBeforeModal.focus();
        }
    }

    function trapFocusInModal(modalEl, e) {
        if (e.key !== "Tab" || !modalEl) return;
        const focusable = modalEl.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey) {
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    }

    // Syntax validation feedback handling
    function clearSyntaxValidation() {
        if (validationBanner) {
            validationBanner.style.display = "none";
        }
        if (validationMessage) {
            validationMessage.textContent = "";
        }
        if (syntaxStatusBadge) {
            syntaxStatusBadge.textContent = "Syntax Ready";
            syntaxStatusBadge.className = "syntax-badge syntax-badge-idle";
        }
        if (cmEditor && currentErrorLineNo) {
            cmEditor.removeLineClass(currentErrorLineNo - 1, "background", "cm-error-line");
            cmEditor.removeLineClass(currentErrorLineNo - 1, "gutter", "cm-gutter-error");
        }
        currentErrorLineNo = null;
    }

    function showSyntaxError(message, lineNo, colNo) {
        if (validationBanner) {
            validationBanner.style.display = "flex";
        }
        if (validationMessage) {
            validationMessage.textContent = `Syntax Error (line ${lineNo || 1}, col ${colNo || 1}): ${message}`;
        }
        if (syntaxStatusBadge) {
            syntaxStatusBadge.textContent = `SYNTAX ERROR: L${lineNo || 1}`;
            syntaxStatusBadge.className = "syntax-badge syntax-badge-error";
        }
        if (cmEditor && lineNo) {
            if (currentErrorLineNo) {
                cmEditor.removeLineClass(currentErrorLineNo - 1, "background", "cm-error-line");
                cmEditor.removeLineClass(currentErrorLineNo - 1, "gutter", "cm-gutter-error");
            }
            currentErrorLineNo = lineNo;
            cmEditor.addLineClass(lineNo - 1, "background", "cm-error-line");
            cmEditor.addLineClass(lineNo - 1, "gutter", "cm-gutter-error");
            cmEditor.scrollIntoView({ line: lineNo - 1, ch: (colNo || 1) - 1 }, 40);
        }
    }

    function showSyntaxValid() {
        clearSyntaxValidation();
        if (syntaxStatusBadge) {
            syntaxStatusBadge.textContent = "Syntax Valid";
            syntaxStatusBadge.className = "syntax-badge syntax-badge-valid";
        }
    }

    // Gutter and Highlighting Synchronization
    function updateEditorGutter() {
        if (!editorGutter || !codeInput) return;
        const rawCode = getEditorCode();
        const lines = rawCode.split("\n");
        const lineCount = Math.max(1, lines.length);

        const fragment = document.createDocumentFragment();
        for (let i = 1; i <= lineCount; i++) {
            const lineDiv = document.createElement("div");
            lineDiv.className = "gutter-line";
            lineDiv.setAttribute("data-line", String(i));
            if (currentActiveLineNo === i) {
                lineDiv.classList.add("gutter-active");
            }
            if (breakpoints.has(i)) {
                lineDiv.classList.add("gutter-breakpoint");
            }
            lineDiv.textContent = String(i);
            fragment.appendChild(lineDiv);
        }

        editorGutter.replaceChildren(fragment);
    }

    function syncEditorScroll() {
        if (!codeInput) return;
        if (editorGutter) {
            editorGutter.scrollTop = codeInput.scrollTop;
        }
        updateActiveLineVisual();
    }

    function updateActiveLineVisual() {
        if (!editorActiveLine || !codeInput) return;
        if (typeof currentActiveLineNo !== "number" || currentActiveLineNo < 1) {
            editorActiveLine.style.display = "none";
            return;
        }
        const lineHeight = 20;
        const paddingTop = 10;
        const visualTop = (paddingTop + (currentActiveLineNo - 1) * lineHeight) - codeInput.scrollTop;
        editorActiveLine.style.top = visualTop + "px";
        editorActiveLine.style.display = "block";
    }

    function highlightEditorLine(lineNo) {
        const code = getEditorCode();
        const lines = code.split("\n");

        // 1. Update CodeMirror active line styling
        if (cmEditor) {
            if (typeof currentActiveLineNo === "number" && currentActiveLineNo >= 1) {
                cmEditor.removeLineClass(currentActiveLineNo - 1, "background", "cm-active-line");
                cmEditor.removeLineClass(currentActiveLineNo - 1, "gutter", "cm-gutter-active");
            }
            if (typeof lineNo === "number" && lineNo >= 1 && lineNo <= lines.length) {
                cmEditor.addLineClass(lineNo - 1, "background", "cm-active-line");
                cmEditor.addLineClass(lineNo - 1, "gutter", "cm-gutter-active");
                cmEditor.scrollIntoView({ line: lineNo - 1, ch: 0 }, 40);
            }
        }

        // 2. Update native gutter & highlight layer for fallback & test contracts
        if (typeof lineNo !== "number" || lineNo < 1 || lineNo > lines.length) {
            currentActiveLineNo = null;
            if (editorGutter) {
                const prev = editorGutter.querySelectorAll(".gutter-line.gutter-active");
                prev.forEach(el => el.classList.remove("gutter-active"));
            }
            updateActiveLineVisual();
            return;
        }

        currentActiveLineNo = lineNo;

        // Update gutter active indicator
        if (editorGutter) {
            const prev = editorGutter.querySelectorAll(".gutter-line.gutter-active");
            prev.forEach(el => el.classList.remove("gutter-active"));
            const targetLine = editorGutter.querySelector(`.gutter-line[data-line="${lineNo}"]`);
            if (targetLine) {
                targetLine.classList.add("gutter-active");
            }
        }

        // Scroll editor to keep active line visible without modifying user cursor or text selection
        if (codeInput && !cmEditor) {
            const lineHeight = 20;
            const paddingTop = 10;
            const targetTop = paddingTop + (lineNo - 1) * lineHeight;
            const targetBottom = targetTop + lineHeight;
            const viewTop = codeInput.scrollTop;
            const viewBottom = viewTop + codeInput.clientHeight;

            if (targetTop < viewTop + 15) {
                codeInput.scrollTop = Math.max(0, targetTop - 30);
            } else if (targetBottom > viewBottom - 15) {
                codeInput.scrollTop = targetBottom + 30 - codeInput.clientHeight;
            }
        }

        // CRITICAL: Synchronize gutter and active line position AFTER codeInput.scrollTop is updated
        syncEditorScroll();
    }

    // 4. Algorithm Presets Loader (Explore Examples)
    function initPresets() {
        if (!presetSelect) return;
        presetSelect.addEventListener("change", function () {
            const key = presetSelect.value;
            // Default option ("Explore Examples..."): do NOT overwrite editor
            if (!key) return;

            const presets = window.ALGORITHM_PRESETS || {};
            if (Object.prototype.hasOwnProperty.call(presets, key)) {
                const previousPreset = activePresetId;
                requestDiscardConfirmation(
                    "You have modified the code in the editor. Loading this example will discard your custom Python code. Do you want to proceed?",
                    function () {
                        activePresetId = key;
                        pause();
                        resetTraceVisuals();
                        clearSyntaxValidation();
                        setEditorCode(presets[key], true);
                        highlightEditorLine(null);
                        updateStatus(`Example Loaded · ${key}`);
                    },
                    function () {
                        presetSelect.value = previousPreset;
                    }
                );
            }
        });
    }

    // 5. Visualize Code API Client (Syntax Validation + Execution Trace)
    async function runTrace() {
        if (isTracing) return;
        const rawCode = getEditorCode();

        // 1. Client-side empty validation check
        if (!rawCode.trim()) {
            showSyntaxError("Code submission cannot be empty. Please enter Python code to visualize.", 1, 1);
            updateStatus("Code cannot be empty", "status-error");
            if (consoleOutput) {
                consoleOutput.textContent = "Error: Code submission cannot be empty.\n";
                consoleOutput.classList.remove("console-empty");
            }
            return;
        }

        clearSyntaxValidation();
        isTracing = true;
        pause();
        if (btnRun) btnRun.disabled = true;
        if (btnClear) btnClear.disabled = true;
        updateStatus("Validating...", "status-running");

        // 2. Syntax validation pre-flight via /api/validate
        try {
            const valResp = await fetch(`${API_BASE_URL}/api/validate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code: rawCode })
            });
            const valData = await valResp.json();

            if (!valData.valid) {
                isTracing = false;
                if (btnRun) btnRun.disabled = false;
                if (btnClear) btnClear.disabled = false;
                const err = valData.error || {};
                showSyntaxError(err.message || "Invalid Python syntax", err.line_no || 1, err.offset || 1);
                updateStatus(`Syntax Error · Line ${err.line_no || 1}`, "status-error");
                if (consoleOutput) {
                    consoleOutput.textContent = `SyntaxError: ${err.message || "Invalid syntax"} (line ${err.line_no || 1}, col ${err.offset || 1})\n`;
                    consoleOutput.classList.remove("console-empty");
                }
                return;
            }
        } catch (valErr) {
            // If validation endpoint has network error, proceed to trace endpoint
        }

        showSyntaxValid();
        hasTriggeredCompletionThisRun = false;
        updateStatus("Running trace...", "status-running");

        try {
            // Determine if active code matches an unmodified preset
            const presetId = presetSelect ? presetSelect.value : "";
            const presets = window.ALGORITHM_PRESETS || {};
            const isUnmodifiedPreset = presetId && presets[presetId] && presets[presetId].trim() === rawCode.trim();

            const stdinVal = stdinInput ? stdinInput.value : "";
            const requestPayload = isUnmodifiedPreset
                ? { preset_id: presetId, code: rawCode, stdin: stdinVal }
                : { code: rawCode, stdin: stdinVal };

            const response = await fetch(`${API_BASE_URL}/api/trace`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestPayload)
            });

            const data = await response.json();

            // Handle errors or HTTP non-200 responses
            if (!response.ok || data.status === "syntax_error") {
                resetTraceVisuals();
                const errMsg = typeof data.error === "string"
                    ? data.error
                    : (data.error && data.error.message ? data.error.message : (data.details || "Execution failed"));

                if (data.status === "syntax_error" && data.error) {
                    showSyntaxError(data.error.message || errMsg, data.error.line_no || 1, data.error.offset || 1);
                }

                if (data.error && data.error.diagnosis) {
                    showErrorDetective(data.error.diagnosis, data.error.type, errMsg);
                }

                if (consoleOutput) {
                    consoleOutput.textContent = `Error: ${errMsg}\n`;
                    consoleOutput.classList.remove("console-empty");
                }
                updateStatus("Execution Error · Check console", "status-error");
                return;
            }

            // Verify trace payload has recorded steps
            if (!data.steps || !Array.isArray(data.steps) || data.steps.length === 0) {
                resetTraceVisuals();
                updateStatus("Trace Empty · 0 steps", "status-error");
                return;
            }

            // Store trace payload and configure timeline
            traceData = data;
            currentStepIndex = 0;
            hideErrorDetective();
            updateStatus(`Trace Loaded · ${data.total_steps} steps`);

            // Update AST algorithm recognition badge
            if (recognitionBadge) {
                const rec = data.recognition;
                const algoType = rec ? (rec.algorithm || rec.type || rec.name) : null;
                if (algoType && algoType !== "generic" && algoType !== "custom") {
                    const rawName = (rec.name || algoType).replace(/_/g, " ");
                    const algoName = rawName.split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(" ");
                    const pct = Math.round((rec.confidence || 0) * 100);
                    recognitionBadge.textContent = algoName;
                    recognitionBadge.title = `Recognized Algorithm: ${algoName} (${pct}% confidence)`;
                    recognitionBadge.style.display = "inline-flex";
                } else {
                    recognitionBadge.style.display = "none";
                }
            }

            // Update Complexity Badge (Feature 15)
            if (complexityBadge) {
                if (data.complexity && data.complexity.estimated_time && data.complexity.estimated_time !== "Unable to determine reliably") {
                    complexityBadge.textContent = `${data.complexity.estimated_time} · ${data.complexity.estimated_space || "O(1)"}`;
                    complexityBadge.title = `Estimated Complexity: Time ${data.complexity.estimated_time}, Space ${data.complexity.estimated_space || "O(1)"} - ${data.complexity.explanation || ""}`;
                    complexityBadge.style.display = "inline-flex";
                } else {
                    complexityBadge.style.display = "none";
                }
            }

            // Reflect status based on tracer termination cause
            if (data.status === "completed") {
                updateStatus(`Ready · ${data.total_steps} steps`, "status-completed");
            } else if (data.status === "step_limit_exceeded") {
                updateStatus(`Step Limit Exceeded · ${data.total_steps} steps`, "status-running");
            } else if (data.status === "timeout") {
                updateStatus("Timeout · 2.0s limit", "status-error");
            } else if (data.status === "exception") {
                const exc = data.error || {};
                updateStatus(`Exception · ${exc.type || "Runtime Error"}`, "status-error");
                if (exc.diagnosis) {
                    showErrorDetective(exc.diagnosis, exc.type, exc.message);
                }
            } else {
                updateStatus(`Ready · ${data.total_steps} steps`, "status-completed");
            }

            // Enable transport controls
            if (timelineScrubber) {
                timelineScrubber.disabled = false;
                timelineScrubber.min = "0";
                timelineScrubber.max = String(data.total_steps - 1);
                timelineScrubber.value = "0";
            }
            if (btnPlay) btnPlay.disabled = false;
            if (btnBookmark) btnBookmark.disabled = false;
            if (btnContinue) btnContinue.disabled = false;

            if (data.has_input && stdinContainer) {
                stdinContainer.style.display = "flex";
            }

            renderStep(0);

            // Automatically start playback if there are multiple steps
            if (data.total_steps > 1) {
                play();
            } else {
                pause();
            }

        } catch (fetchErr) {
            resetTraceVisuals();
            updateStatus("Network Error · Request failed", "status-error");
            if (consoleOutput) {
                consoleOutput.textContent = `Network Error: ${fetchErr.message}\n`;
                consoleOutput.classList.remove("console-empty");
            }
        } finally {
            isTracing = false;
            if (btnRun) btnRun.disabled = false;
            if (btnClear) btnClear.disabled = false;
        }
    }

    // 6. Step Renderer (Syncs Memory Map, Sequences, Pointers, Console)
    function renderStep(stepIndex) {
        if (!traceData || !traceData.steps || traceData.steps.length === 0) return;

        stepIndex = Math.max(0, Math.min(stepIndex, traceData.steps.length - 1));
        const step = traceData.steps[stepIndex];
        const prevStep = (stepIndex > 0) ? traceData.steps[stepIndex - 1] : null;

        if (window.XRayAnimator && window.XRayAnimator.beforeStepRender) {
            window.XRayAnimator.beforeStepRender(step, prevStep);
        }

        const isSteppingBackward = (stepIndex < currentStepIndex);
        currentStepIndex = stepIndex;

        // 6A. Update Transport Navigation Controls
        if (timelineScrubber) timelineScrubber.value = String(stepIndex);
        if (stepCounter) stepCounter.textContent = `STEP ${stepIndex + 1} / ${traceData.total_steps}`;

        if (btnFirst) btnFirst.disabled = (stepIndex === 0);
        if (btnPrev) btnPrev.disabled = (stepIndex === 0);
        if (btnNext) btnNext.disabled = (stepIndex === traceData.total_steps - 1);
        if (btnLast) btnLast.disabled = (stepIndex === traceData.total_steps - 1);

        // Update step-by-step explanation strip
        if (stepExplanationText) {
            stepExplanationText.textContent = step.explanation || `Step ${stepIndex + 1}: Executed line ${step.line_no}.`;
        }

        const explanationStepBadge = document.getElementById("explanation-step-badge");
        if (explanationStepBadge) {
            explanationStepBadge.textContent = `STEP ${stepIndex + 1} / ${traceData.total_steps}`;
        }

        const explanationVarDiff = document.getElementById("explanation-var-diff");
        const explanationVarDiffText = document.getElementById("explanation-var-diff-text");
        if (explanationVarDiff && explanationVarDiffText) {
            if (step.mutations && step.mutations.length > 0) {
                const parts = step.mutations.map(m => {
                    const curr = step.locals_snapshot ? step.locals_snapshot[m] : undefined;
                    const prev = prevStep && prevStep.locals_snapshot ? prevStep.locals_snapshot[m] : undefined;
                    if (prev !== undefined && curr !== undefined) {
                        return `${m}: ${JSON.stringify(prev)} -> ${JSON.stringify(curr)}`;
                    } else if (curr !== undefined) {
                        return `${m} = ${JSON.stringify(curr)}`;
                    }
                    return m;
                });
                explanationVarDiffText.textContent = parts.join(", ");
                explanationVarDiff.style.display = "flex";
            } else {
                explanationVarDiff.style.display = "none";
            }
        }

        // Active pointers summary in Sequence Stage
        const pointerSummaryContainer = document.getElementById("sequence-pointer-summary");
        const pointerSummaryContent = document.getElementById("pointer-summary-content");
        if (pointerSummaryContainer && pointerSummaryContent) {
            if (step.active_pointers && Object.keys(step.active_pointers).length > 0) {
                const parts = Object.entries(step.active_pointers).map(([ptr, idx]) => `${ptr} = [${idx}]`);
                pointerSummaryContent.textContent = parts.join(", ");
                pointerSummaryContainer.style.display = "flex";
            } else {
                pointerSummaryContainer.style.display = "none";
            }
        }

        // Update bookmark button state for active step
        updateBookmarkVisual();

        // Check Watchpoint hit during playback
        if (isPlaying && step.mutations && step.mutations.length > 0) {
            for (const watched of watchpoints) {
                if (step.mutations.includes(watched)) {
                    pause();
                    updateStatus(`Watchpoint Hit · '${watched}' changed`, "status-running");
                    break;
                }
            }
        }

        // 6B. Highlight Editor Source Line
        highlightEditorLine(step.line_no);

        // 6C. Render Variables Table, Call Stack, and Recursion
        renderMemoryTable(step, prevStep);
        renderCallStack(step);
        if (recursionBadge) {
            if (step.recursion_info && (step.recursion_info.is_recursive || step.recursion_info.depth > 1)) {
                recursionBadge.textContent = `Recursion · Depth ${step.recursion_info.depth}`;
                recursionBadge.style.display = "inline-flex";
            } else {
                recursionBadge.style.display = "none";
            }
        }

        // 6D. Render Memory Visualization Stage
        renderSequenceStage(step);

        // 6E. Synchronize Console Output
        renderConsole(step);

        // Update live runtime operation counters (Feature 14)
        if (step.cumulative_operations) {
            const cum = step.cumulative_operations;
            if (opCompares) opCompares.textContent = String(cum.comparisons || 0);
            if (opSwaps) opSwaps.textContent = String(cum.swaps || 0);
            if (opAssignments) opAssignments.textContent = String(cum.assignments || 0);
            if (opLoops) opLoops.textContent = String(cum.loop_iterations || 0);
            if (opTotal) opTotal.textContent = String(cum.total || 0);
        }

        if (window.XRayAnimator && window.XRayAnimator.afterStepRender) {
            window.XRayAnimator.afterStepRender(step, prevStep, isSteppingBackward);
        }

        // 6F. Trigger restrained execution complete indicator if final step reached on completed execution
        if (stepIndex === traceData.total_steps - 1 && traceData.status === "completed") {
            if (!hasTriggeredCompletionThisRun) {
                hasTriggeredCompletionThisRun = true;
                triggerExecutionComplete();
            }
        } else {
            hasTriggeredCompletionThisRun = false;
        }
    }

    function triggerExecutionComplete() {
        if (!traceStatus || !traceData) return;
        updateStatus(`Execution Complete · ${traceData.total_steps} steps`, "status-completed");
        traceStatus.classList.remove("status-completed-pulse");
        void traceStatus.offsetWidth;
        traceStatus.classList.add("status-completed-pulse");
    }

    // 6C. Sub-renderer: Variables Table
    function renderMemoryTable(step, prevStep) {
        if (!memoryTableBody) return;
        memoryTableBody.replaceChildren();

        const locals = step.locals_snapshot || {};
        const varNames = Object.keys(locals).sort();

        if (varNames.length === 0) {
            const emptyRow = document.createElement("tr");
            const emptyCell = document.createElement("td");
            emptyCell.colSpan = 4;
            emptyCell.className = "table-empty-message";
            emptyCell.textContent = "No variables currently in local scope.";
            emptyRow.appendChild(emptyCell);
            memoryTableBody.appendChild(emptyRow);
            return;
        }

        const prevLocals = (prevStep && prevStep.locals_snapshot) ? prevStep.locals_snapshot : null;

        for (const varName of varNames) {
            const row = document.createElement("tr");
            const currVal = locals[varName];

            // Determine if variable is newly initialized in scope
            const isNew = (!prevLocals || !Object.prototype.hasOwnProperty.call(prevLocals, varName));
            const typeStr = (step.types && step.types[varName]) ? step.types[varName] : typeof currVal;

            // Col 1: Variable Name & Type
            const tdVar = document.createElement("td");
            tdVar.className = "col-var";
            if (isNew) {
                tdVar.classList.add("val-new");
            }
            const varGroup = document.createElement("div");
            varGroup.className = "var-badge-group";
            const nameSpan = document.createElement("span");
            nameSpan.className = "var-name";
            nameSpan.textContent = varName;
            const typeSpan = document.createElement("span");
            typeSpan.className = "var-type-tag";
            typeSpan.textContent = typeStr;
            typeSpan.title = `Type: ${typeStr}`;
            varGroup.appendChild(nameSpan);
            varGroup.appendChild(typeSpan);
            tdVar.appendChild(varGroup);

            // Col 2: Current Value
            const tdVal = document.createElement("td");
            tdVal.className = "col-val";
            tdVal.textContent = formatValue(currVal);

            // Col 3: Change Status & Transition
            const tdStatus = document.createElement("td");
            tdStatus.className = "col-status";

            if (isNew) {
                const badgeNew = document.createElement("span");
                badgeNew.className = "status-badge-inline new";
                badgeNew.dataset.status = "NEW";
                badgeNew.textContent = "New";
                badgeNew.title = `Variable '${varName}' initialized in local scope`;
                tdStatus.appendChild(badgeNew);
            } else {
                const prevVal = prevLocals[varName];
                const prevFmt = formatValue(prevVal);
                const currFmt = formatValue(currVal);

                let isChanged = false;
                try {
                    isChanged = JSON.stringify(prevVal) !== JSON.stringify(currVal);
                } catch (_) {
                    isChanged = String(prevVal) !== String(currVal);
                }

                if (isChanged) {
                    tdVal.classList.add("val-mutated");
                    const badgeMutated = document.createElement("span");
                    badgeMutated.className = "status-badge-inline mutated";
                    badgeMutated.dataset.status = "MUTATED";
                    badgeMutated.title = `Mutated from ${prevFmt} to ${currFmt}`;

                    // Concise transition indicator if values are compact
                    if (prevFmt.length <= 10 && currFmt.length <= 10) {
                        badgeMutated.textContent = `${prevFmt} → ${currFmt}`;
                    } else {
                        badgeMutated.textContent = "Mutated";
                    }
                    tdStatus.appendChild(badgeMutated);
                } else {
                    const quiet = document.createElement("span");
                    quiet.className = "col-status-quiet";
                    quiet.textContent = "-";
                    tdStatus.appendChild(quiet);
                }
            }

            // Col 4: Actions (Watchpoint Pin & History Drawer)
            const tdActions = document.createElement("td");
            tdActions.className = "col-actions";

            const btnWatch = document.createElement("button");
            btnWatch.type = "button";
            btnWatch.className = "btn-watchpoint";
            if (watchpoints.has(varName)) {
                btnWatch.classList.add("is-watching");
                btnWatch.textContent = "PINNED";
                btnWatch.title = `Watchpoint active: pauses execution when '${varName}' mutates`;
            } else {
                btnWatch.textContent = "PIN";
                btnWatch.title = `Pin watchpoint for '${varName}'`;
            }
            btnWatch.addEventListener("click", function (evt) {
                evt.stopPropagation();
                toggleWatchpoint(varName);
            });

            const btnHist = document.createElement("button");
            btnHist.type = "button";
            btnHist.className = "btn-var-history";
            btnHist.textContent = "HIST";
            btnHist.title = `Inspect historical mutations of '${varName}'`;
            btnHist.addEventListener("click", function (evt) {
                evt.stopPropagation();
                openVariableHistory(varName);
            });

            tdActions.appendChild(btnWatch);
            tdActions.appendChild(btnHist);

            row.appendChild(tdVar);
            row.appendChild(tdVal);
            row.appendChild(tdStatus);
            row.appendChild(tdActions);

            memoryTableBody.appendChild(row);
        }
    }

    function toggleWatchpoint(varName) {
        if (watchpoints.has(varName)) {
            watchpoints.delete(varName);
        } else {
            watchpoints.add(varName);
        }
        updateWatchpointBadge();
        if (traceData && traceData.steps && traceData.steps[currentStepIndex]) {
            renderMemoryTable(traceData.steps[currentStepIndex], currentStepIndex > 0 ? traceData.steps[currentStepIndex - 1] : null);
        }
    }

    function updateWatchpointBadge() {
        if (!watchpointBadge) return;
        if (watchpoints.size > 0) {
            watchpointBadge.textContent = `WATCHPOINTS: ${watchpoints.size}`;
            watchpointBadge.className = "syntax-badge syntax-badge-valid";
            watchpointBadge.style.display = "inline-flex";
        } else {
            watchpointBadge.style.display = "none";
        }
    }

    function openVariableHistory(varName) {
        if (!varHistoryModal || !traceData || !traceData.steps) return;
        if (varHistoryName) varHistoryName.textContent = varName;

        let mutationCount = 0;
        let prevValFormatted = "-";
        if (varHistoryTableBody) {
            varHistoryTableBody.replaceChildren();

            for (let i = 0; i < traceData.steps.length; i++) {
                const step = traceData.steps[i];
                const locals = step.locals_snapshot || {};
                if (!Object.prototype.hasOwnProperty.call(locals, varName)) continue;

                const currVal = locals[varName];
                const currValFormatted = formatValue(currVal);
                const isMutated = (i > 0 && step.mutations && step.mutations.includes(varName));
                if (isMutated) mutationCount++;

                const tr = document.createElement("tr");

                const tdStep = document.createElement("td");
                tdStep.textContent = `Step ${i + 1}`;

                const tdLine = document.createElement("td");
                tdLine.textContent = `L${step.line_no}`;

                const tdVal = document.createElement("td");
                tdVal.textContent = currValFormatted;
                if (isMutated) tdVal.classList.add("val-mutated");

                const tdChange = document.createElement("td");
                if (isMutated) {
                    tdChange.textContent = `${prevValFormatted} → ${currValFormatted}`;
                } else if (i === 0 || prevValFormatted === "-") {
                    tdChange.textContent = "INIT";
                } else {
                    tdChange.textContent = "-";
                }

                prevValFormatted = currValFormatted;

                tr.appendChild(tdStep);
                tr.appendChild(tdLine);
                tr.appendChild(tdVal);
                tr.appendChild(tdChange);
                varHistoryTableBody.appendChild(tr);
            }
        }

        if (varHistoryMutationsCount) {
            varHistoryMutationsCount.textContent = `${mutationCount} mutations recorded`;
        }

        varHistoryModal.classList.add("is-open");
        varHistoryModal.setAttribute("aria-hidden", "false");
    }

    function closeVariableHistory() {
        if (!varHistoryModal) return;
        varHistoryModal.classList.remove("is-open");
        varHistoryModal.setAttribute("aria-hidden", "true");
    }

    function toggleBookmark(stepIdx) {
        if (!traceData || !traceData.steps) return;
        if (typeof stepIdx !== "number") stepIdx = currentStepIndex;

        if (bookmarks.has(stepIdx)) {
            bookmarks.delete(stepIdx);
        } else {
            bookmarks.add(stepIdx);
        }
        updateBookmarkVisual();
    }

    function updateBookmarkVisual() {
        if (!btnBookmark) return;
        const isBookmarked = bookmarks.has(currentStepIndex);
        btnBookmark.classList.toggle("is-bookmarked", isBookmarked);
        btnBookmark.title = isBookmarked ? `Step ${currentStepIndex + 1} Bookmarked (Click to remove)` : "Bookmark Current Step (B)";
    }

    function togglePredictMode() {
        isPredictMode = !isPredictMode;
        if (btnPredictToggle) {
            btnPredictToggle.classList.toggle("active", isPredictMode);
            btnPredictToggle.textContent = isPredictMode ? "PREDICT: ON" : "PREDICT: OFF";
        }
        if (predictScoreBadge) {
            predictScoreBadge.style.display = isPredictMode ? "inline-block" : "none";
            updatePredictScore();
        }
    }

    function updatePredictScore() {
        if (!predictScoreBadge) return;
        const pct = predictStats.total > 0 ? Math.round((predictStats.correct / predictStats.total) * 100) : 0;
        predictScoreBadge.textContent = `SCORE: ${predictStats.correct}/${predictStats.total} (${pct}%)`;
    }

    function openPredictModal(targetStepIndex, onResolved) {
        if (!predictModal || !traceData || targetStepIndex >= traceData.steps.length) {
            onResolved();
            return;
        }

        const nextStep = traceData.steps[targetStepIndex];
        const nextLocals = nextStep.locals_snapshot || {};
        const mutatedVars = nextStep.mutations || [];
        const candidateVar = mutatedVars.length > 0 ? mutatedVars[0] : Object.keys(nextLocals)[0];

        if (!candidateVar) {
            onResolved();
            return;
        }

        if (predictModalPrompt) {
            predictModalPrompt.textContent = `Predict the next value of '${candidateVar}' after executing line ${nextStep.line_no}:`;
        }
        if (predictInputValue) {
            predictInputValue.value = "";
        }
        if (predictFeedback) {
            predictFeedback.style.display = "none";
            predictFeedback.textContent = "";
            predictFeedback.className = "predict-feedback";
        }

        predictModal.classList.add("is-open");
        predictModal.setAttribute("aria-hidden", "false");
        if (predictInputValue) predictInputValue.focus();

        pendingPredictionStep = {
            targetIndex: targetStepIndex,
            variable: candidateVar,
            expectedValue: nextLocals[candidateVar],
            callback: onResolved
        };
    }

    function closePredictModal() {
        if (!predictModal) return;
        predictModal.classList.remove("is-open");
        predictModal.setAttribute("aria-hidden", "true");
        pendingPredictionStep = null;
    }

    function submitPrediction() {
        if (!pendingPredictionStep) return;

        const userPred = predictInputValue ? predictInputValue.value.trim() : "";
        const expected = pendingPredictionStep.expectedValue;
        const expectedStr = String(expected);
        const expectedFormatted = formatValue(expected);

        predictStats.total++;
        const isCorrect = (userPred === expectedStr || userPred === expectedFormatted || userPred.toLowerCase() === expectedStr.toLowerCase());

        if (isCorrect) {
            predictStats.correct++;
            if (predictFeedback) {
                predictFeedback.textContent = `Correct! '${pendingPredictionStep.variable}' is indeed ${expectedFormatted}. (+1)`;
                predictFeedback.className = "predict-feedback correct";
                predictFeedback.style.display = "block";
            }
        } else {
            if (predictFeedback) {
                predictFeedback.textContent = `Incorrect. Expected ${expectedFormatted}, predicted '${userPred}'.`;
                predictFeedback.className = "predict-feedback incorrect";
                predictFeedback.style.display = "block";
            }
        }

        updatePredictScore();

        const cb = pendingPredictionStep.callback;
        setTimeout(function () {
            closePredictModal();
            if (cb) cb();
        }, 600);
    }

    // Phase 4: Algorithm & Code Comparison Helpers
    function openComparisonModal() {
        if (!comparisonModal) return;
        lastFocusedElementBeforeModal = document.activeElement;
        comparisonModal.classList.add("is-open");
        comparisonModal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");

        const presets = window.ALGORITHM_PRESETS || {};
        if (compareSelectA && compareCodeA && !compareCodeA.value) {
            const selA = compareSelectA.value;
            if (presets[selA]) compareCodeA.value = presets[selA].trim();
        }
        if (compareSelectB && compareCodeB && !compareCodeB.value) {
            const selB = compareSelectB.value;
            if (presets[selB]) compareCodeB.value = presets[selB].trim();
        }
    }

    function closeComparisonModal() {
        if (!comparisonModal) return;
        comparisonModal.classList.remove("is-open");
        comparisonModal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");
        if (lastFocusedElementBeforeModal && typeof lastFocusedElementBeforeModal.focus === "function") {
            lastFocusedElementBeforeModal.focus();
        }
    }

    function handleComparePresetChange(selectEl, textareaEl) {
        if (!selectEl || !textareaEl) return;
        const val = selectEl.value;
        const presets = window.ALGORITHM_PRESETS || {};
        if (val !== "custom" && presets[val]) {
            textareaEl.value = presets[val].trim();
        }
    }

    async function runAlgorithmComparison() {
        if (!compareCodeA || !compareCodeB || !btnRunComparison) return;
        const codeA = compareCodeA.value.trim();
        const codeB = compareCodeB.value.trim();
        const sharedStdin = compareSharedStdin ? compareSharedStdin.value : "";
        const nameA = compareSelectA ? compareSelectA.options[compareSelectA.selectedIndex].text : "Algorithm A";
        const nameB = compareSelectB ? compareSelectB.options[compareSelectB.selectedIndex].text : "Algorithm B";

        if (!codeA || !codeB) {
            alert("Please provide Python code for both Algorithm A and Algorithm B.");
            return;
        }

        btnRunComparison.disabled = true;
        btnRunComparison.textContent = "Executing Comparison...";

        try {
            const resp = await fetch(`${API_BASE_URL}/api/compare`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code_a: codeA,
                    code_b: codeB,
                    name_a: nameA,
                    name_b: nameB,
                    stdin: sharedStdin
                })
            });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                throw new Error(errData.error || errData.message || `Comparison error HTTP ${resp.status}`);
            }

            const data = await resp.json();
            renderComparisonResults(data);
        } catch (err) {
            if (comparisonVerdictText) {
                comparisonVerdictText.textContent = `Comparison failed: ${err.message}`;
            }
            if (comparisonResults) comparisonResults.style.display = "flex";
        } finally {
            btnRunComparison.disabled = false;
            btnRunComparison.textContent = "Run Comparison";
        }
    }

    function renderComparisonResults(data) {
        if (!comparisonResults) return;
        const comp = data.comparison || {};
        const implA = data.implementation_a || {};
        const implB = data.implementation_b || {};

        if (compThA) compThA.textContent = implA.name || "Algorithm A";
        if (compThB) compThB.textContent = implB.name || "Algorithm B";

        if (comparisonVerdictText) {
            comparisonVerdictText.textContent = comp.verdict || "Comparison complete.";
        }

        if (comparisonTableBody) {
            const rows = [
                { label: "Status", a: implA.status, b: implB.status, delta: implA.status === implB.status ? "Matched" : "Differs" },
                { label: "Output Equivalence", a: comp.output_note || "", b: comp.output_note || "", delta: comp.outputs_match ? "Equivalent" : "Differing" },
                { label: "Total Steps", a: implA.total_steps, b: implB.total_steps, delta: (implB.total_steps - implA.total_steps) },
                { label: "Element Comparisons", a: implA.metrics?.comparisons || 0, b: implB.metrics?.comparisons || 0, delta: comp.operations_delta?.comparisons?.diff_b_minus_a || 0 },
                { label: "Element Swaps", a: implA.metrics?.swaps || 0, b: implB.metrics?.swaps || 0, delta: comp.operations_delta?.swaps?.diff_b_minus_a || 0 },
                { label: "Variable Assignments", a: implA.metrics?.assignments || 0, b: implB.metrics?.assignments || 0, delta: comp.operations_delta?.assignments?.diff_b_minus_a || 0 },
                { label: "Loop Iterations", a: implA.metrics?.loop_iterations || 0, b: implB.metrics?.loop_iterations || 0, delta: comp.operations_delta?.loop_iterations?.diff_b_minus_a || 0 },
                { label: "Estimated Time Complexity", a: implA.complexity?.estimated_time || "N/A", b: implB.complexity?.estimated_time || "N/A", delta: "-" },
                { label: "Estimated Space Complexity", a: implA.complexity?.estimated_space || "N/A", b: implB.complexity?.estimated_space || "N/A", delta: "-" },
                { label: "AST Node Count", a: implA.structure?.node_count || 0, b: implB.structure?.node_count || 0, delta: (implB.structure?.node_count || 0) - (implA.structure?.node_count || 0) }
            ];

            const fragment = document.createDocumentFragment();
            for (const r of rows) {
                const tr = document.createElement("tr");
                const tdLabel = document.createElement("td");
                tdLabel.textContent = r.label;
                const tdA = document.createElement("td");
                tdA.textContent = String(r.a);
                const tdB = document.createElement("td");
                tdB.textContent = String(r.b);
                const tdDelta = document.createElement("td");
                tdDelta.textContent = String(r.delta);
                tr.append(tdLabel, tdA, tdB, tdDelta);
                fragment.appendChild(tr);
            }
            comparisonTableBody.replaceChildren(fragment);
        }

        comparisonResults.style.display = "flex";
    }

    // Phase 3: Advanced Debugging Helpers
    function toggleBreakpoint(lineNo) {
        if (typeof lineNo !== "number" || lineNo < 1) return;
        if (breakpoints.has(lineNo)) {
            breakpoints.delete(lineNo);
            if (cmEditor) {
                cmEditor.removeLineClass(lineNo - 1, "gutter", "cm-gutter-breakpoint");
            }
            if (editorGutter) {
                const el = editorGutter.querySelector(`.gutter-line[data-line="${lineNo}"]`);
                if (el) el.classList.remove("gutter-breakpoint");
            }
        } else {
            breakpoints.add(lineNo);
            if (cmEditor) {
                cmEditor.addLineClass(lineNo - 1, "gutter", "cm-gutter-breakpoint");
            }
            if (editorGutter) {
                const el = editorGutter.querySelector(`.gutter-line[data-line="${lineNo}"]`);
                if (el) el.classList.add("gutter-breakpoint");
            }
        }
    }

    function continueToBreakpoint() {
        if (!traceData || !traceData.steps) return;
        pause();

        for (let i = currentStepIndex + 1; i < traceData.steps.length; i++) {
            const step = traceData.steps[i];
            if (breakpoints.has(step.line_no)) {
                goToStep(i);
                updateStatus(`Paused at breakpoint · Line ${step.line_no}`, "status-running");
                return;
            }
        }

        // If no breakpoint encountered ahead, step to final step
        goToStep(traceData.total_steps - 1);
    }

    function renderCallStack(step) {
        if (!callStackContainer || !callStackFrames) return;
        const stack = Array.isArray(step.call_stack) ? step.call_stack : [];
        const isRecursive = Boolean(step.recursion_info && step.recursion_info.is_recursive);
        const isDeep = stack.length > 1;

        // If only root module frame and not recursive, hide call stack
        if (!isRecursive && stack.length <= 1) {
            callStackContainer.style.display = "none";
            return;
        }

        callStackContainer.style.display = "block";
        if (callStackDepthLabel) {
            callStackDepthLabel.textContent = `Depth: ${stack.length}`;
        }

        // Auto-expand only if active recursion with multiple frames
        if (isRecursive && isDeep) {
            callStackContainer.open = true;
        }

        callStackFrames.replaceChildren();

        for (let i = stack.length - 1; i >= 0; i--) {
            const frame = stack[i];
            const pill = document.createElement("span");
            pill.className = "call-frame-pill";
            if (i === stack.length - 1) {
                pill.classList.add("active");
            }

            const argsList = [];
            const argsObj = frame.args || {};
            for (const [k, v] of Object.entries(argsObj)) {
                argsList.push(`${k}=${v}`);
            }
            const argsStr = argsList.length > 0 ? argsList.join(", ") : "";

            pill.textContent = `${frame.func_name}(${argsStr}) : L${frame.line_no}`;
            callStackFrames.appendChild(pill);
        }
    }

    function showErrorDetective(diagnosis, errType, errMsg) {
        if (!errorDetectiveCard) return;
        if (!diagnosis) {
            errorDetectiveCard.style.display = "none";
            return;
        }

        if (errorDetectiveTitle) {
            errorDetectiveTitle.textContent = diagnosis.title || errType || "Error";
        }
        if (errorDetectiveExplanation) {
            errorDetectiveExplanation.textContent = diagnosis.explanation || errMsg || "An error occurred.";
        }
        if (errorDetectiveSuggestion) {
            errorDetectiveSuggestion.textContent = diagnosis.suggestion || "Inspect code on the failing line.";
        }

        errorDetectiveCard.style.display = "flex";
    }

    function hideErrorDetective() {
        if (!errorDetectiveCard) return;
        errorDetectiveCard.style.display = "none";
    }

    // Phase 5: Platform Expansion & Polish Helpers

    // Feature 18: Interface Mode (Learning vs Debugging)
    let currentUIMode = "debugging";

    function applyUIMode(mode) {
        currentUIMode = mode;
        if (mode === "learning") {
            document.body.classList.remove("mode-debugging");
            document.body.classList.add("mode-learning");
            if (btnModeToggle) btnModeToggle.textContent = "Mode: Learning";
        } else {
            document.body.classList.remove("mode-learning");
            document.body.classList.add("mode-debugging");
            if (btnModeToggle) btnModeToggle.textContent = "Mode: Debug";
        }
        try {
            localStorage.setItem("xray_ui_mode", mode);
        } catch (_) {}
    }

    function toggleUIMode() {
        const nextMode = currentUIMode === "learning" ? "debugging" : "learning";
        applyUIMode(nextMode);
    }

    // Feature 19: Trace Export and Import
    function exportTraceJSON() {
        if (!traceData || !traceData.steps) {
            alert("No active execution trace to export. Run a trace first.");
            return;
        }

        const exportPayload = {
            schema_version: "1.0",
            exported_at: new Date().toISOString(),
            code: getEditorCode(),
            status: traceData.status,
            total_steps: traceData.total_steps,
            steps: traceData.steps,
            recognition: traceData.recognition,
            complexity: traceData.complexity,
            operation_metrics: traceData.operation_metrics,
            stdout: traceData.stdout
        };

        const jsonStr = JSON.stringify(exportPayload, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `xray-trace-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        updateStatus("Trace Exported · JSON saved", "status-completed");
    }

    function handleImportFile(e) {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        // Bounded file size limit check: 5 MB maximum
        if (file.size > 5 * 1024 * 1024) {
            alert("Trace file exceeds maximum allowed size (5 MB).");
            e.target.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = function (ev) {
            try {
                const parsed = JSON.parse(ev.target.result);
                if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.steps) || parsed.steps.length === 0) {
                    alert("Invalid X-Ray trace file format. Missing steps array.");
                    return;
                }

                pause();
                if (parsed.code && typeof parsed.code === "string") {
                    setEditorCode(parsed.code, true);
                }

                const totalSteps = typeof parsed.total_steps === "number" ? parsed.total_steps : parsed.steps.length;
                parsed.total_steps = totalSteps;

                traceData = parsed;
                currentStepIndex = 0;
                hideErrorDetective();

                if (timelineScrubber) {
                    timelineScrubber.disabled = false;
                    timelineScrubber.min = "0";
                    timelineScrubber.max = String(parsed.total_steps - 1);
                    timelineScrubber.value = "0";
                }
                if (btnPlay) btnPlay.disabled = false;
                if (btnBookmark) btnBookmark.disabled = false;
                if (btnContinue) btnContinue.disabled = false;

                goToStep(0);
                updateStatus(`Trace Imported · ${parsed.total_steps} steps`, "status-completed");
            } catch (err) {
                alert("Failed to parse trace JSON file: " + err.message);
            }
        };
        reader.readAsText(file);
        e.target.value = "";
    }

    // Feature 20: Shareable Code Link
    function copyShareLink() {
        const code = getEditorCode();
        if (!code.trim()) {
            alert("Editor is empty. Enter some code to generate a shareable link.");
            return;
        }

        const shareUrl = window.location.origin + window.location.pathname + "#code=" + encodeURIComponent(code);
        if (shareUrl.length > 8192) {
            alert("Notice: Code is very large. Some browsers may truncate URLs exceeding 8KB. Consider exporting a trace JSON file for large code.");
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(shareUrl).then(() => {
                updateStatus("Share Link Copied", "status-completed");
            }).catch(() => {
                prompt("Copy this shareable link:", shareUrl);
            });
        } else {
            prompt("Copy this shareable link:", shareUrl);
        }
    }

    function checkUrlHashForCode() {
        const hash = window.location.hash;
        if (hash && hash.startsWith("#code=")) {
            try {
                const decoded = decodeURIComponent(hash.substring(6));
                if (decoded && decoded.trim()) {
                    setEditorCode(decoded, true);
                    updateStatus("Code Loaded from Share Link", "status-completed");
                }
            } catch (_) {}
        }
    }

    // Feature 21: Custom Test Cases Modal
    function openTestCasesModal() {
        if (!testCasesModal) return;
        lastFocusedElementBeforeModal = document.activeElement;
        testCasesModal.classList.add("is-open");
        testCasesModal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");
    }

    function closeTestCasesModal() {
        if (!testCasesModal) return;
        testCasesModal.classList.remove("is-open");
        testCasesModal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");
        if (lastFocusedElementBeforeModal && typeof lastFocusedElementBeforeModal.focus === "function") {
            lastFocusedElementBeforeModal.focus();
        }
    }

    function addTestCaseRow() {
        if (!testCasesList) return;
        const count = testCasesList.querySelectorAll(".test-case-row").length;
        if (count >= 10) {
            alert("Maximum 10 test cases allowed.");
            return;
        }

        const row = document.createElement("div");
        row.className = "test-case-row";
        row.setAttribute("data-index", String(count));

        const fieldIn = document.createElement("div");
        fieldIn.className = "test-case-field";
        const labelIn = document.createElement("label");
        labelIn.className = "test-label";
        labelIn.textContent = `Input #${count + 1} (stdin):`;
        const inputIn = document.createElement("input");
        inputIn.type = "text";
        inputIn.className = "test-input tc-input";
        inputIn.placeholder = "e.g. 10";
        fieldIn.append(labelIn, inputIn);

        const fieldExp = document.createElement("div");
        fieldExp.className = "test-case-field";
        const labelExp = document.createElement("label");
        labelExp.className = "test-label";
        labelExp.textContent = "Expected Output:";
        const inputExp = document.createElement("input");
        inputExp.type = "text";
        inputExp.className = "test-input tc-expected";
        inputExp.placeholder = "e.g. 100";
        fieldExp.append(labelExp, inputExp);

        row.append(fieldIn, fieldExp);
        testCasesList.appendChild(row);
    }

    async function runBatchTests() {
        if (!testCasesList || !btnRunAllTests) return;
        const code = getEditorCode().trim();
        if (!code) {
            alert("Please enter Python code in the editor before running test cases.");
            return;
        }

        const rows = testCasesList.querySelectorAll(".test-case-row");
        const cases = [];
        rows.forEach(r => {
            const inEl = r.querySelector(".tc-input");
            const expEl = r.querySelector(".tc-expected");
            cases.push({
                input: inEl ? inEl.value : "",
                expected_output: expEl ? expEl.value : ""
            });
        });

        if (cases.length === 0) {
            alert("Add at least one test case.");
            return;
        }

        btnRunAllTests.disabled = true;
        btnRunAllTests.textContent = "Running Batch Tests...";

        try {
            const resp = await fetch(`${API_BASE_URL}/api/batch-test`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code: code,
                    test_cases: cases
                })
            });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                throw new Error(errData.error || `HTTP ${resp.status}`);
            }

            const data = await resp.json();
            renderBatchTestResults(data);
        } catch (err) {
            if (testBatchSummary) testBatchSummary.textContent = `Batch execution failed: ${err.message}`;
            if (testBatchResults) testBatchResults.style.display = "flex";
        } finally {
            btnRunAllTests.disabled = false;
            btnRunAllTests.textContent = "Run Batch Tests";
        }
    }

    function renderBatchTestResults(data) {
        if (!testBatchResults) return;
        const summary = testBatchSummary;
        const details = testBatchDetails;

        if (summary) {
            const allPassed = data.failed_cases === 0;
            summary.textContent = allPassed
                ? `ALL TESTS PASSED: ${data.passed_cases} / ${data.total_cases} CASES SUCCESSFUL`
                : `TESTS FAILED: ${data.passed_cases} PASSED, ${data.failed_cases} FAILED (TOTAL ${data.total_cases})`;
            summary.style.color = allPassed ? "var(--accent-mutation)" : "var(--accent-error)";
        }

        if (details) {
            const fragment = document.createDocumentFragment();
            (data.results || []).forEach(res => {
                const item = document.createElement("div");
                item.className = `test-result-item ${res.passed ? "passed" : "failed"}`;
                const label = document.createElement("span");
                label.textContent = `Case #${res.case_index} [Input: "${res.input}"] => Got: "${res.actual_output}" (Expected: "${res.expected_output}")`;
                const status = document.createElement("strong");
                status.textContent = res.passed ? "PASS" : "FAIL";
                item.append(label, status);
                fragment.appendChild(item);
            });
            details.replaceChildren(fragment);
        }

        testBatchResults.style.display = "flex";
    }

    // Feature 22: Concept Glossary Modal
    function openGlossaryModal() {
        if (!glossaryModal) return;
        lastFocusedElementBeforeModal = document.activeElement;
        glossaryModal.classList.add("is-open");
        glossaryModal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");
        if (glossarySearchInput) {
            glossarySearchInput.value = "";
            filterGlossary("");
            glossarySearchInput.focus();
        }
    }

    function closeGlossaryModal() {
        if (!glossaryModal) return;
        glossaryModal.classList.remove("is-open");
        glossaryModal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");
        if (lastFocusedElementBeforeModal && typeof lastFocusedElementBeforeModal.focus === "function") {
            lastFocusedElementBeforeModal.focus();
        }
    }

    function filterGlossary(query) {
        if (!glossaryList) return;
        const q = (query || "").trim().toLowerCase();
        const items = glossaryList.querySelectorAll(".glossary-item");
        items.forEach(item => {
            const terms = (item.getAttribute("data-term") || "").toLowerCase();
            const text = item.textContent.toLowerCase();
            if (!q || terms.includes(q) || text.includes(q)) {
                item.style.display = "block";
            } else {
                item.style.display = "none";
            }
        });
    }

    // 6D. Sub-renderer: Sequence & Pointer Stage
    function getCellEventClasses(step, seqName, idx) {
        if (!traceData || !traceData.steps) return ["semantic-neutral"];

        const events = Array.isArray(step.events) ? step.events : [];
        const classes = [];

        // 1. Check if finalized at or before currentStepIndex
        let isFinalized = false;
        for (let s = 0; s <= currentStepIndex; s++) {
            const pastEvents = traceData.steps[s].events || [];
            for (let k = 0; k < pastEvents.length; k++) {
                const pe = pastEvents[k];
                if (pe.target === seqName && (pe.type === "position_finalized" || pe.semantic_state === "finalized")) {
                    if (pe.index === idx || (Array.isArray(pe.indices) && pe.indices.includes(idx))) {
                        isFinalized = true;
                        break;
                    }
                }
            }
            if (isFinalized) break;
        }

        if (isFinalized) {
            classes.push("semantic-finalized", "cell-sorted");
            return classes;
        }

        // 2. Check if search target found at or before currentStepIndex
        let isFound = false;
        for (let s = 0; s <= currentStepIndex; s++) {
            const pastEvents = traceData.steps[s].events || [];
            for (let k = 0; k < pastEvents.length; k++) {
                const pe = pastEvents[k];
                if (pe.target === seqName && (pe.type === "found" || pe.type === "search_found" || pe.semantic_state === "found")) {
                    if (pe.index === idx || (Array.isArray(pe.indices) && pe.indices.includes(idx))) {
                        isFound = true;
                        break;
                    }
                }
            }
            if (isFound) break;
        }

        if (isFound) {
            classes.push("semantic-found", "cell-found");
            return classes;
        }

        // 3. Current step active operations & states
        let isModified = false;
        let isActive = false;
        let isRejected = false;
        let isDiscovered = false;

        for (let i = 0; i < events.length; i++) {
            const e = events[i];
            if (e.target !== seqName) continue;

            if (e.type === "swap" || e.type === "mutation" || e.type === "shift" || e.semantic_state === "modified") {
                if (e.index === idx || (Array.isArray(e.indices) && e.indices.includes(idx))) {
                    isModified = true;
                }
            }
            if (e.type === "compare" || e.type === "visit" || e.semantic_state === "active") {
                if (e.index === idx || (Array.isArray(e.indices) && e.indices.includes(idx))) {
                    isActive = true;
                }
            }
            if (e.type === "search_range") {
                if (typeof e.low === "number" && typeof e.high === "number") {
                    if (idx < e.low || idx > e.high) {
                        isRejected = true;
                    }
                }
                if (typeof e.mid === "number" && e.mid === idx) {
                    isActive = true;
                }
            }
            if (e.type === "reject" || e.type === "search_rejected" || e.semantic_state === "rejected") {
                if (e.index === idx || (Array.isArray(e.indices) && e.indices.includes(idx))) {
                    isRejected = true;
                }
            }
            if (e.type === "segment_sorted" || e.semantic_state === "discovered") {
                if (e.index === idx || (Array.isArray(e.indices) && e.indices.includes(idx))) {
                    isDiscovered = true;
                }
            }
        }

        if (isModified) {
            classes.push("semantic-modified", "cell-mutated");
            return classes;
        }
        if (isActive) {
            classes.push("semantic-active", "cell-searching");
            return classes;
        }
        if (isRejected) {
            classes.push("semantic-rejected", "cell-rejected");
            return classes;
        }
        if (isDiscovered) {
            classes.push("semantic-discovered");
            return classes;
        }

        // 4. Past visited elements (processed in past steps 0..currentStepIndex-1)
        let isVisited = false;
        for (let s = 0; s < currentStepIndex; s++) {
            const pastEvents = traceData.steps[s].events || [];
            for (let k = 0; k < pastEvents.length; k++) {
                const pe = pastEvents[k];
                if (pe.target === seqName) {
                    if (pe.index === idx || (Array.isArray(pe.indices) && pe.indices.includes(idx))) {
                        isVisited = true;
                        break;
                    }
                }
            }
            if (isVisited) break;
        }

        if (isVisited) {
            classes.push("semantic-visited");
            return classes;
        }

        // 5. Default neutral
        classes.push("semantic-neutral");
        return classes;
    }

    function createSequenceContainer(seq, seqPointers, isSeqMutated, step) {
        // Container for this individual sequence
        const seqBox = document.createElement("div");
        seqBox.className = "sequence-container";
        seqBox.setAttribute("data-seq-name", seq.name);

        // Row A: Sequence Label Row (explicit margin-bottom separation)
        const labelRow = document.createElement("div");
        labelRow.className = "sequence-label-row";

        const nameSpan = document.createElement("span");
        nameSpan.className = "seq-label-name";
        nameSpan.textContent = seq.name;

        const typeSpan = document.createElement("span");
        typeSpan.className = "seq-label-type";
        typeSpan.textContent = seq.type;

        const lenSpan = document.createElement("span");
        lenSpan.className = "seq-label-len";
        lenSpan.textContent = `[${seq.length}]`;

        labelRow.appendChild(nameSpan);
        labelRow.appendChild(typeSpan);
        labelRow.appendChild(lenSpan);
        seqBox.appendChild(labelRow);

        // Row B: Horizontal Scrolling Track for Elements and Indices
        const track = document.createElement("div");
        track.className = "sequence-cells-track";

        const trackInner = document.createElement("div");
        trackInner.className = "sequence-track-inner";

        // Sub-row 1: Indices
        const indicesRow = document.createElement("div");
        indicesRow.className = "sequence-indices-row";

        // Sub-row 2: Memory Block Cells
        const blocksRow = document.createElement("div");
        blocksRow.className = "sequence-blocks-row";

        // Sub-row 3: Pointer Slots
        const pointersRow = document.createElement("div");
        pointersRow.className = "sequence-pointers-row";

        const elements = Array.isArray(seq.elements) ? seq.elements : [];

        for (let idx = 0; idx < seq.length; idx++) {
            const matchedPtrs = seqPointers.filter(p => p.value === idx);

            // Index Cell
            const idxCell = document.createElement("div");
            idxCell.className = "sequence-index-cell";
            idxCell.textContent = String(idx);
            if (matchedPtrs.length > 0) {
                idxCell.classList.add("index-active");
            }
            indicesRow.appendChild(idxCell);

            // Memory Block Cell
            const blockCell = document.createElement("div");
            blockCell.className = "memory-block-cell";
            blockCell.setAttribute("data-index", String(idx));
            blockCell.textContent = formatCellValue(elements[idx]);

            if (isSeqMutated) {
                blockCell.classList.add("cell-mutated");
            }

            if (matchedPtrs.length > 0) {
                const hasPtrA = matchedPtrs.some(p => p.name === "left" || p.name === "i" || p.name === "start" || p.name === "slow");
                if (hasPtrA) {
                    blockCell.classList.add("cell-pointer-a");
                } else {
                    blockCell.classList.add("cell-pointer-b");
                }
            }

            if (step) {
                const eventClasses = getCellEventClasses(step, seq.name, idx);
                for (let c = 0; c < eventClasses.length; c++) {
                    blockCell.classList.add(eventClasses[c]);
                }
            }

            blocksRow.appendChild(blockCell);

            // Pointer Slot
            const ptrSlot = document.createElement("div");
            ptrSlot.className = "pointer-slot";

            for (let pi = 0; pi < matchedPtrs.length; pi++) {
                const ptr = matchedPtrs[pi];
                const ptrIndicator = document.createElement("span");
                const isA = (ptr.name === "left" || ptr.name === "i" || ptr.name === "start" || ptr.name === "slow" || pi === 0);
                ptrIndicator.className = `pointer-indicator ${isA ? "ptr-a" : "ptr-b"}`;
                ptrIndicator.textContent = ptr.name;
                ptrIndicator.setAttribute("data-ptr-name", ptr.name);
                ptrSlot.appendChild(ptrIndicator);
            }
            pointersRow.appendChild(ptrSlot);
        }

        trackInner.appendChild(indicesRow);
        trackInner.appendChild(blocksRow);
        trackInner.appendChild(pointersRow);
        track.appendChild(trackInner);
        seqBox.appendChild(track);

        return seqBox;
    }

    function renderSequenceStage(step) {
        if (!sequencesContainer || !stageEmpty) return;

        // Adaptive 2D Matrix Stage delegation
        let has2D = false;
        if (window.XRayMatrixStage && matrixContainer) {
            has2D = window.XRayMatrixStage.render(matrixContainer, step, currentStepIndex, traceData ? traceData.steps : null);
        }

        const sequences = step.sequences || {};
        const allSeqNames = Object.keys(sequences).sort();
        const seqNames = allSeqNames.filter(name => !sequences[name].is_2d_matrix);

        if (seqNames.length === 0) {
            if (has2D) {
                stageEmpty.style.display = "none";
                sequencesContainer.style.display = "none";
            } else {
                stageEmpty.style.display = "block";
                sequencesContainer.style.display = "block";
                sequencesContainer.replaceChildren();
            }
            return;
        }

        stageEmpty.style.display = "none";
        sequencesContainer.style.display = "block";

        // Remove obsolete sequence containers
        const existingBoxes = Array.from(sequencesContainer.querySelectorAll(".sequence-container"));
        for (const box of existingBoxes) {
            const name = box.getAttribute("data-seq-name");
            if (!seqNames.includes(name)) {
                box.remove();
            }
        }

        const allPointers = Array.isArray(step.pointers) ? step.pointers : [];
        const mutations = Array.isArray(step.mutations) ? step.mutations : [];

        for (const seqName of seqNames) {
            const seq = sequences[seqName];
            const seqPointers = allPointers.filter(p => p.target === seqName);
            const isSeqMutated = mutations.includes(seqName);
            const elements = Array.isArray(seq.elements) ? seq.elements : [];

            const existingBox = sequencesContainer.querySelector(`.sequence-container[data-seq-name="${seqName}"]`);
            let canReuse = false;

            if (existingBox) {
                const blocksRow = existingBox.querySelector(".sequence-blocks-row");
                if (blocksRow && blocksRow.children.length === seq.length) {
                    canReuse = true;
                }
            }

            if (canReuse) {
                // Update in-place to preserve DOM element stability and prevent flickering
                const labelRow = existingBox.querySelector(".sequence-label-row");
                if (labelRow) {
                    const nameSpan = labelRow.querySelector(".seq-label-name");
                    const typeSpan = labelRow.querySelector(".seq-label-type");
                    const lenSpan = labelRow.querySelector(".seq-label-len");
                    if (nameSpan) nameSpan.textContent = seq.name;
                    if (typeSpan) typeSpan.textContent = seq.type;
                    if (lenSpan) lenSpan.textContent = `[${seq.length}]`;
                }

                const indicesRow = existingBox.querySelector(".sequence-indices-row");
                const blocksRow = existingBox.querySelector(".sequence-blocks-row");
                const pointersRow = existingBox.querySelector(".sequence-pointers-row");

                for (let idx = 0; idx < seq.length; idx++) {
                    const matchedPtrs = seqPointers.filter(p => p.value === idx);

                    // Update Index Cell
                    const idxCell = indicesRow.children[idx];
                    if (idxCell) {
                        idxCell.textContent = String(idx);
                        if (matchedPtrs.length > 0) {
                            idxCell.classList.add("index-active");
                        } else {
                            idxCell.classList.remove("index-active");
                        }
                    }

                    // Update Block Cell
                    const blockCell = blocksRow.children[idx];
                    if (blockCell) {
                        const formattedVal = formatCellValue(elements[idx]);
                        if (blockCell.textContent !== formattedVal) {
                            blockCell.textContent = formattedVal;
                        }
                        // Reset transient classes cleanly
                        blockCell.className = "memory-block-cell";
                        if (isSeqMutated) {
                            blockCell.classList.add("cell-mutated");
                        }
                        if (matchedPtrs.length > 0) {
                            const hasPtrA = matchedPtrs.some(p => p.name === "left" || p.name === "i" || p.name === "start" || p.name === "slow");
                            if (hasPtrA) {
                                blockCell.classList.add("cell-pointer-a");
                            } else {
                                blockCell.classList.add("cell-pointer-b");
                            }
                        }

                        const eventClasses = getCellEventClasses(step, seq.name, idx);
                        for (let c = 0; c < eventClasses.length; c++) {
                            blockCell.classList.add(eventClasses[c]);
                        }
                    }

                    // Update Pointer Slot
                    const ptrSlot = pointersRow.children[idx];
                    if (ptrSlot) {
                        ptrSlot.replaceChildren();
                        for (let pi = 0; pi < matchedPtrs.length; pi++) {
                            const ptr = matchedPtrs[pi];
                            const ptrIndicator = document.createElement("span");
                            const isA = (ptr.name === "left" || ptr.name === "i" || ptr.name === "start" || ptr.name === "slow" || pi === 0);
                            ptrIndicator.className = `pointer-indicator ${isA ? "ptr-a" : "ptr-b"}`;
                            ptrIndicator.textContent = ptr.name;
                            ptrIndicator.setAttribute("data-ptr-name", ptr.name);
                            ptrSlot.appendChild(ptrIndicator);
                        }
                    }
                }
            } else {
                const newSeqBox = createSequenceContainer(seq, seqPointers, isSeqMutated, step);
                if (existingBox) {
                    existingBox.replaceWith(newSeqBox);
                } else {
                    sequencesContainer.appendChild(newSeqBox);
                }
            }
        }
    }

    // 6E. Sub-renderer: Console Output (Cumulative with Jump Stability)
    function renderConsole(step) {
        if (!consoleOutput) return;

        const output = (typeof step.stdout === "string") ? step.stdout : "";
        if (output.length > 0) {
            consoleOutput.textContent = output;
            consoleOutput.classList.remove("console-empty");
        } else {
            consoleOutput.textContent = "No standard output recorded. Run a trace to view print() outputs.";
            consoleOutput.classList.add("console-empty");
        }

        if (consolePre) {
            consolePre.scrollTop = consolePre.scrollHeight;
        }
    }

    // 7. Transport Playback Controller
    function updatePlayButtonIcon() {
        if (!btnPlay) return;
        btnPlay.replaceChildren();

        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "14");
        svg.setAttribute("height", "14");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("fill", "currentColor");

        if (isPlaying) {
            // Pause icon (two vertical bars)
            const rect1 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect1.setAttribute("x", "6");
            rect1.setAttribute("y", "4");
            rect1.setAttribute("width", "4");
            rect1.setAttribute("height", "16");

            const rect2 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect2.setAttribute("x", "14");
            rect2.setAttribute("y", "4");
            rect2.setAttribute("width", "4");
            rect2.setAttribute("height", "16");

            svg.appendChild(rect1);
            svg.appendChild(rect2);
            btnPlay.title = "Pause (Space)";
            btnPlay.setAttribute("aria-label", "Pause execution");
        } else {
            // Play icon (triangle)
            const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            polygon.setAttribute("points", "7 4 19 12 7 20 7 4");
            svg.appendChild(polygon);
            btnPlay.title = "Play (Space)";
            btnPlay.setAttribute("aria-label", "Play execution");
        }

        btnPlay.appendChild(svg);
        btnPlay.classList.toggle("is-playing", isPlaying);
    }

    function play() {
        if (!traceData || !traceData.steps || traceData.steps.length === 0) return;

        // If at the final step, loop back to step 0
        if (currentStepIndex >= traceData.steps.length - 1) {
            goToStep(0);
        }

        // Prevent overlapping timers
        if (playTimer) {
            clearTimeout(playTimer);
            playTimer = null;
        }

        isPlaying = true;
        if (btnPlay) {
            btnPlay.classList.add("is-playing");
        }
        updatePlayButtonIcon();
        scheduleNextTick();
    }

    function pause() {
        isPlaying = false;
        if (btnPlay) {
            btnPlay.classList.remove("is-playing");
        }
        if (playTimer) {
            clearTimeout(playTimer);
            playTimer = null;
        }
        updatePlayButtonIcon();
    }

    function togglePlay() {
        if (isPlaying) {
            pause();
        } else {
            play();
        }
    }

    function scheduleNextTick() {
        if (!isPlaying) return;

        const speed = parseFloat(speedSelect ? speedSelect.value : "1.0") || 1.0;
        let delay = Math.round(700 / speed);

        // If current step executed a swap operation, guarantee sufficient duration for visible flight and landing
        const currentStep = (traceData && traceData.steps) ? traceData.steps[currentStepIndex] : null;
        const hasSwap = currentStep && Array.isArray(currentStep.operations) && currentStep.operations.some(op => op.type === "swap");

        if (hasSwap && window.XRayAnimator && window.XRayAnimator.getSwapDuration) {
            const swapDur = window.XRayAnimator.getSwapDuration();
            delay = Math.max(delay, swapDur + 120);
        }

        if (playTimer) {
            clearTimeout(playTimer);
            playTimer = null;
        }

        playTimer = setTimeout(function () {
            if (!isPlaying || !traceData) return;

            if (currentStepIndex < traceData.steps.length - 1) {
                goToStep(currentStepIndex + 1);
                if (currentStepIndex < traceData.steps.length - 1) {
                    scheduleNextTick();
                } else {
                    pause();
                }
            } else {
                pause();
            }
        }, delay);
    }

    function nextStep() {
        if (!traceData || !traceData.steps) return;
        if (currentStepIndex >= traceData.steps.length - 1) return;

        if (isPredictMode) {
            pause();
            openPredictModal(currentStepIndex + 1, function () {
                goToStep(currentStepIndex + 1);
            });
        } else {
            goToStep(currentStepIndex + 1);
        }
    }

    function goToStep(index) {
        if (!traceData || !traceData.steps || traceData.steps.length === 0) return;
        renderStep(index);
    }

    // 8. Visual State Reset & Clear Handlers
    function resetTraceVisuals() {
        pause();
        traceData = null;
        currentStepIndex = 0;
        highlightEditorLine(null);
        hasTriggeredCompletionThisRun = false;

        // Reset transport controls
        if (btnFirst) btnFirst.disabled = true;
        if (btnPrev) btnPrev.disabled = true;
        if (btnPlay) btnPlay.disabled = true;
        if (btnNext) btnNext.disabled = true;
        if (btnLast) btnLast.disabled = true;
        if (btnBookmark) {
            btnBookmark.disabled = true;
            btnBookmark.classList.remove("is-bookmarked");
        }
        if (btnContinue) btnContinue.disabled = true;
        hideErrorDetective();
        if (callStackContainer) callStackContainer.style.display = "none";
        if (recursionBadge) recursionBadge.style.display = "none";
        bookmarks.clear();
        watchpoints.clear();
        updateWatchpointBadge();

        if (stepExplanationText) {
            stepExplanationText.textContent = "Run a trace or select an example to view step explanations.";
        }

        const explanationStepBadge = document.getElementById("explanation-step-badge");
        if (explanationStepBadge) {
            explanationStepBadge.textContent = "STEP 0 / 0";
        }
        const explanationVarDiff = document.getElementById("explanation-var-diff");
        if (explanationVarDiff) {
            explanationVarDiff.style.display = "none";
        }
        const pointerSummaryContainer = document.getElementById("sequence-pointer-summary");
        if (pointerSummaryContainer) {
            pointerSummaryContainer.style.display = "none";
        }

        if (timelineScrubber) {
            timelineScrubber.disabled = true;
            timelineScrubber.value = "0";
            timelineScrubber.min = "0";
            timelineScrubber.max = "0";
        }

        if (stepCounter) {
            stepCounter.textContent = "Step 0 / 0";
        }

        // Reset variables table to default empty state
        if (memoryTableBody) {
            memoryTableBody.replaceChildren();
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 4;
            td.className = "table-empty-message";
            td.textContent = "No variables in scope. Run a trace to populate memory.";
            tr.appendChild(td);
            memoryTableBody.appendChild(tr);
        }

        // Reset sequence stage to default empty state
        if (stageEmpty) stageEmpty.style.display = "block";
        if (sequencesContainer) {
            sequencesContainer.style.display = "block";
            sequencesContainer.replaceChildren();
        }
        if (matrixContainer) {
            matrixContainer.style.display = "none";
            matrixContainer.replaceChildren();
        }
        if (recognitionBadge) {
            recognitionBadge.style.display = "none";
        }
        if (complexityBadge) {
            complexityBadge.style.display = "none";
        }
        if (opCompares) opCompares.textContent = "0";
        if (opSwaps) opSwaps.textContent = "0";
        if (opAssignments) opAssignments.textContent = "0";
        if (opLoops) opLoops.textContent = "0";
        if (opTotal) opTotal.textContent = "0";

        // Reset console to default empty state
        if (consoleOutput) {
            consoleOutput.textContent = "No standard output recorded. Run a trace to view print() outputs.";
            consoleOutput.classList.add("console-empty");
        }

        updatePlayButtonIcon();
    }

    function handleClear() {
        requestDiscardConfirmation(
            "Are you sure you want to clear the editor? Your custom Python code will be erased.",
            function () {
                pause();
                traceData = null;
                currentStepIndex = 0;
                hasTriggeredCompletionThisRun = false;

                // Clear editor completely
                setEditorCode("", true);
                activePresetId = "";

                if (presetSelect) {
                    presetSelect.value = "";
                }
                if (codeInput) {
                    codeInput.value = "";
                    codeInput.focus();
                }

                updateEditorGutter();
                highlightEditorLine(null);
                resetTraceVisuals();
                clearSyntaxValidation();
                updateStatus("Editor Cleared");
            }
        );
    }

    function handleResetExample() {
        requestDiscardConfirmation(
            "Reset editor back to the default Palindrome Check example? Your custom Python modifications will be discarded.",
            function () {
                pause();
                traceData = null;
                currentStepIndex = 0;
                hasTriggeredCompletionThisRun = false;

                setEditorCode(DEFAULT_PYTHON_EXAMPLE, true);
                activePresetId = "";

                if (presetSelect) {
                    presetSelect.value = "";
                }

                updateEditorGutter();
                highlightEditorLine(null);
                resetTraceVisuals();
                clearSyntaxValidation();
                updateStatus("Example Reset · Palindrome Check");
            }
        );
    }

    // 9. CodeMirror Initialization
    function initCodeMirror() {
        if (window.CodeMirror && codeInput) {
            try {
                cmEditor = window.CodeMirror.fromTextArea(codeInput, {
                    mode: "python",
                    lineNumbers: true,
                    indentUnit: 4,
                    tabSize: 4,
                    matchBrackets: true,
                    autoCloseBrackets: true,
                    lineWrapping: false,
                    viewportMargin: Infinity
                });

                cmEditor.on("change", function () {
                    const val = cmEditor.getValue();
                    if (codeInput) {
                        codeInput.value = val;
                    }
                    clearSyntaxValidation();
                    updateEditorGutter();
                });

                cmEditor.on("focus", function () {
                    if (tabCustomCode) {
                        tabCustomCode.classList.add("active");
                    }
                });

                cmEditor.on("gutterClick", function (cm, lineIndex) {
                    toggleBreakpoint(lineIndex + 1);
                });

                // Hide native gutter since CodeMirror provides its own
                if (editorGutter) {
                    editorGutter.style.display = "none";
                }
            } catch (cmErr) {
                console.warn("CodeMirror initialization fallback to native textarea:", cmErr);
            }
        }
    }

    // 10. Event Listeners Wiring
    function initEvents() {
        // Code input editor interactions (scrolling, typing, indentation)
        if (codeInput) {
            codeInput.addEventListener("scroll", syncEditorScroll);
            codeInput.addEventListener("input", function () {
                clearSyntaxValidation();
                updateEditorGutter();
                updateActiveLineVisual();
            });
            codeInput.addEventListener("keydown", function (e) {
                if (e.key === "Tab") {
                    e.preventDefault();
                    const start = this.selectionStart;
                    const end = this.selectionEnd;
                    this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
                    this.selectionStart = this.selectionEnd = start + 4;
                    updateEditorGutter();
                    updateActiveLineVisual();
                }
            });
        }

        if (editorGutter) {
            editorGutter.addEventListener("click", function (e) {
                const lineEl = e.target.closest(".gutter-line");
                if (lineEl) {
                    const lineNo = parseInt(lineEl.getAttribute("data-line"), 10);
                    if (!isNaN(lineNo)) {
                        toggleBreakpoint(lineNo);
                    }
                }
            });
        }

        // Visualize Code button
        if (btnRun) {
            btnRun.addEventListener("click", runTrace);
        }

        // Clear button (empties editor, resets dropdown and visual state)
        if (btnClear) {
            btnClear.addEventListener("click", handleClear);
        }

        // Reset Example button
        if (btnResetExample) {
            btnResetExample.addEventListener("click", handleResetExample);
        }

        // Header Navigation Tabs
        if (tabCustomCode) {
            tabCustomCode.addEventListener("click", function () {
                if (cmEditor) {
                    cmEditor.focus();
                } else if (codeInput) {
                    codeInput.focus();
                }
            });
        }

        if (tabExploreExamples) {
            tabExploreExamples.addEventListener("click", function (e) {
                e.preventDefault();
                if (presetSelect) {
                    presetSelect.focus();
                }
            });
        }

        // Transport Controls
        if (btnFirst) {
            btnFirst.addEventListener("click", function () {
                pause();
                if (window.XRayAnimator && window.XRayAnimator.cancelAnimations) window.XRayAnimator.cancelAnimations();
                goToStep(0);
            });
        }

        if (btnPrev) {
            btnPrev.addEventListener("click", function () {
                pause();
                goToStep(currentStepIndex - 1);
            });
        }

        if (btnPlay) {
            btnPlay.addEventListener("click", function () {
                togglePlay();
            });
        }

        if (btnNext) {
            btnNext.addEventListener("click", function () {
                pause();
                nextStep();
            });
        }

        if (btnBookmark) {
            btnBookmark.addEventListener("click", function () {
                toggleBookmark(currentStepIndex);
            });
        }

        if (btnContinue) {
            btnContinue.addEventListener("click", function () {
                continueToBreakpoint();
            });
        }

        if (recursionBadge) {
            recursionBadge.addEventListener("click", function () {
                if (!callStackContainer) return;
                callStackContainer.style.display = "block";
                callStackContainer.open = true;
                callStackContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
            });
        }

        if (btnToggleStdin) {
            btnToggleStdin.addEventListener("click", function () {
                if (!stdinContainer) return;
                const isHidden = (stdinContainer.style.display === "none");
                stdinContainer.style.display = isHidden ? "flex" : "none";
                if (isHidden && stdinInput) stdinInput.focus();
            });
        }

        if (btnPredictToggle) {
            btnPredictToggle.addEventListener("click", togglePredictMode);
        }

        if (predictModalClose) {
            predictModalClose.addEventListener("click", closePredictModal);
        }
        if (predictModalSkip) {
            predictModalSkip.addEventListener("click", function () {
                const cb = pendingPredictionStep ? pendingPredictionStep.callback : null;
                closePredictModal();
                if (cb) cb();
            });
        }
        if (predictModalSubmit) {
            predictModalSubmit.addEventListener("click", submitPrediction);
        }
        if (predictInputValue) {
            predictInputValue.addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    submitPrediction();
                }
            });
        }

        if (varHistoryClose) {
            varHistoryClose.addEventListener("click", closeVariableHistory);
        }
        if (varHistoryDismiss) {
            varHistoryDismiss.addEventListener("click", closeVariableHistory);
        }
        if (varHistoryModal) {
            varHistoryModal.addEventListener("click", function (e) {
                if (e.target === varHistoryModal) closeVariableHistory();
            });
        }
        if (predictModal) {
            predictModal.addEventListener("click", function (e) {
                if (e.target === predictModal) closePredictModal();
            });
        }

        // Comparison Modal Event Listeners (Phase 4)
        if (btnCompareModal) {
            btnCompareModal.addEventListener("click", openComparisonModal);
        }
        if (comparisonModalClose) {
            comparisonModalClose.addEventListener("click", closeComparisonModal);
        }
        if (comparisonModalDismiss) {
            comparisonModalDismiss.addEventListener("click", closeComparisonModal);
        }
        if (comparisonModal) {
            comparisonModal.addEventListener("click", function (e) {
                if (e.target === comparisonModal) closeComparisonModal();
            });
        }
        if (compareSelectA) {
            compareSelectA.addEventListener("change", function () {
                handleComparePresetChange(compareSelectA, compareCodeA);
            });
        }
        if (compareSelectB) {
            compareSelectB.addEventListener("change", function () {
                handleComparePresetChange(compareSelectB, compareCodeB);
            });
        }
        if (btnRunComparison) {
            btnRunComparison.addEventListener("click", runAlgorithmComparison);
        }

        // Phase 5: Platform Expansion Event Listeners
        if (btnModeToggle) {
            btnModeToggle.addEventListener("click", toggleUIMode);
        }
        if (btnExportTrace) {
            btnExportTrace.addEventListener("click", exportTraceJSON);
        }
        if (btnImportTrace && inputImportFile) {
            btnImportTrace.addEventListener("click", function () {
                inputImportFile.click();
            });
            inputImportFile.addEventListener("change", handleImportFile);
        }
        if (btnShareLink) {
            btnShareLink.addEventListener("click", copyShareLink);
        }
        window.addEventListener("hashchange", checkUrlHashForCode);

        // Test cases modal events
        if (btnTestCases) {
            btnTestCases.addEventListener("click", openTestCasesModal);
        }
        if (testCasesModalClose) {
            testCasesModalClose.addEventListener("click", closeTestCasesModal);
        }
        if (testCasesModalDismiss) {
            testCasesModalDismiss.addEventListener("click", closeTestCasesModal);
        }
        if (testCasesModal) {
            testCasesModal.addEventListener("click", function (e) {
                if (e.target === testCasesModal) closeTestCasesModal();
            });
        }
        if (btnAddTestCase) {
            btnAddTestCase.addEventListener("click", addTestCaseRow);
        }
        if (btnRunAllTests) {
            btnRunAllTests.addEventListener("click", runBatchTests);
        }

        // Glossary modal events
        if (btnGlossary) {
            btnGlossary.addEventListener("click", openGlossaryModal);
        }
        if (glossaryModalClose) {
            glossaryModalClose.addEventListener("click", closeGlossaryModal);
        }
        if (glossaryModalDismiss) {
            glossaryModalDismiss.addEventListener("click", closeGlossaryModal);
        }
        if (glossaryModal) {
            glossaryModal.addEventListener("click", function (e) {
                if (e.target === glossaryModal) closeGlossaryModal();
            });
        }
        if (glossarySearchInput) {
            glossarySearchInput.addEventListener("input", function () {
                filterGlossary(glossarySearchInput.value);
            });
        }

        if (btnLast) {
            btnLast.addEventListener("click", function () {
                pause();
                if (window.XRayAnimator && window.XRayAnimator.cancelAnimations) window.XRayAnimator.cancelAnimations();
                if (traceData) goToStep(traceData.total_steps - 1);
            });
        }

        // Timeline range scrubber
        if (timelineScrubber) {
            timelineScrubber.addEventListener("input", function () {
                pause();
                if (window.XRayAnimator && window.XRayAnimator.cancelAnimations) window.XRayAnimator.cancelAnimations();
                const step = parseInt(timelineScrubber.value, 10);
                if (!isNaN(step)) {
                    goToStep(step);
                }
            });
        }

        // Playback speed selector
        if (speedSelect) {
            speedSelect.addEventListener("change", function () {
                if (isPlaying) {
                    if (playTimer) clearTimeout(playTimer);
                    scheduleNextTick();
                }
            });
        }

        // Discard Confirmation Modal Events
        if (confirmModalClose) {
            confirmModalClose.addEventListener("click", function () {
                closeConfirmModal(false);
            });
        }
        if (confirmModalCancel) {
            confirmModalCancel.addEventListener("click", function () {
                closeConfirmModal(false);
            });
        }
        if (confirmModalProceed) {
            confirmModalProceed.addEventListener("click", function () {
                closeConfirmModal(true);
            });
        }
        if (confirmModal) {
            confirmModal.addEventListener("click", function (e) {
                if (e.target === confirmModal) {
                    closeConfirmModal(false);
                }
            });
        }

        // Keyboard Shortcuts Reference Modal Events
        if (btnShortcutsHelp) {
            btnShortcutsHelp.addEventListener("click", function () {
                openShortcutsModal();
            });
        }
        if (shortcutsModalClose) {
            shortcutsModalClose.addEventListener("click", function () {
                closeShortcutsModal();
            });
        }
        if (shortcutsModalDismiss) {
            shortcutsModalDismiss.addEventListener("click", function () {
                closeShortcutsModal();
            });
        }
        if (shortcutsModal) {
            shortcutsModal.addEventListener("click", function (e) {
                if (e.target === shortcutsModal) {
                    closeShortcutsModal();
                }
            });
        }

        // Keyboard Shortcuts (Space, Left, Right, Home, End, Ctrl+Enter, ?, Esc for modals)
        window.addEventListener("keydown", function (e) {
            if (varHistoryModal && varHistoryModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closeVariableHistory();
                    return;
                }
            }

            if (predictModal && predictModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closePredictModal();
                    return;
                }
            }

            if (comparisonModal && comparisonModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closeComparisonModal();
                    return;
                }
            }

            if (testCasesModal && testCasesModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closeTestCasesModal();
                    return;
                }
            }

            if (glossaryModal && glossaryModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closeGlossaryModal();
                    return;
                }
            }

            if (shortcutsModal && shortcutsModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closeShortcutsModal();
                    return;
                }
                if (e.key === "Tab") {
                    trapFocusInModal(shortcutsModal, e);
                }
                return;
            }

            if (confirmModal && confirmModal.classList.contains("is-open")) {
                if (e.key === "Escape") {
                    e.preventDefault();
                    closeConfirmModal(false);
                    return;
                }
                if (e.key === "Tab") {
                    trapFocusInModal(confirmModal, e);
                }
                return;
            }

            const isEditing = (document.activeElement === codeInput) || (cmEditor && cmEditor.hasFocus()) || (document.activeElement === stdinInput) || (document.activeElement === predictInputValue) || (document.activeElement === compareCodeA) || (document.activeElement === compareCodeB) || (document.activeElement === compareSharedStdin);

            // Allow Ctrl+Enter or Cmd+Enter to trigger Visualize Code anytime
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                runTrace();
                return;
            }

            // If ? pressed while not editing code, open keyboard shortcuts dialog
            if (!isEditing && e.key === "?") {
                e.preventDefault();
                openShortcutsModal();
                return;
            }

            if (isEditing) return;
            if (!traceData || traceData.total_steps === 0) return;

            if (e.key === "b" || e.key === "B") {
                e.preventDefault();
                toggleBookmark(currentStepIndex);
            } else if (e.key === "c" || e.key === "C" || e.key === "F5") {
                e.preventDefault();
                continueToBreakpoint();
            } else if (e.code === "Space") {
                e.preventDefault();
                togglePlay();
            } else if (e.code === "ArrowLeft") {
                e.preventDefault();
                pause();
                goToStep(currentStepIndex - 1);
            } else if (e.code === "ArrowRight") {
                e.preventDefault();
                pause();
                nextStep();
            } else if (e.code === "Home") {
                e.preventDefault();
                pause();
                goToStep(0);
            } else if (e.code === "End") {
                e.preventDefault();
                pause();
                goToStep(traceData.total_steps - 1);
            }
        });
    }

    // More menu dropdown handling
    function initMoreMenu() {
        const btnMoreMenu = document.getElementById("btn-more-menu");
        const moreMenuDropdown = document.getElementById("more-menu-dropdown");
        if (!btnMoreMenu || !moreMenuDropdown) return;

        function toggleMoreMenu(forceState) {
            const isCurrentlyOpen = btnMoreMenu.getAttribute("aria-expanded") === "true";
            const willOpen = typeof forceState === "boolean" ? forceState : !isCurrentlyOpen;
            btnMoreMenu.setAttribute("aria-expanded", String(willOpen));
            if (willOpen) {
                moreMenuDropdown.removeAttribute("hidden");
                const firstItem = moreMenuDropdown.querySelector(".menu-item");
                if (firstItem) firstItem.focus();
            } else {
                moreMenuDropdown.setAttribute("hidden", "");
            }
        }

        btnMoreMenu.addEventListener("click", function (e) {
            e.stopPropagation();
            toggleMoreMenu();
        });

        // Close More menu on outside click
        document.addEventListener("click", function (e) {
            if (!moreMenuDropdown.hasAttribute("hidden")) {
                if (!moreMenuDropdown.contains(e.target) && !btnMoreMenu.contains(e.target)) {
                    toggleMoreMenu(false);
                }
            }
        });

        // Close More menu on Escape
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !moreMenuDropdown.hasAttribute("hidden")) {
                toggleMoreMenu(false);
                btnMoreMenu.focus();
            }
        });

        // Close menu when clicking actions inside it (except density toggle)
        moreMenuDropdown.querySelectorAll(".menu-item").forEach(function (item) {
            if (item.id !== "btn-density-toggle") {
                item.addEventListener("click", function () {
                    toggleMoreMenu(false);
                });
            }
        });
    }

    // Workspace Density Preference (Comfortable vs Compact)
    function initDensityPreference() {
        const btnDensityToggle = document.getElementById("btn-density-toggle");
        const densityBadge = document.getElementById("density-badge");

        function applyDensity(density, save = true) {
            const isCompact = (density === "compact");
            document.body.classList.toggle("density-compact", isCompact);
            if (btnDensityToggle) {
                btnDensityToggle.setAttribute("aria-checked", String(isCompact));
            }
            if (densityBadge) {
                densityBadge.textContent = isCompact ? "COMPACT" : "COMFORTABLE";
            }
            if (save) {
                try {
                    sessionStorage.setItem("xray_workspace_density", density);
                } catch (_) {}
            }
        }

        if (btnDensityToggle) {
            btnDensityToggle.addEventListener("click", function (e) {
                e.stopPropagation();
                const currentIsCompact = document.body.classList.contains("density-compact");
                applyDensity(currentIsCompact ? "comfortable" : "compact", true);
            });
        }

        // Restore density preference
        try {
            const savedDensity = sessionStorage.getItem("xray_workspace_density");
            if (savedDensity === "compact") {
                applyDensity("compact", false);
            }
        } catch (_) {}
    }

    // Collapsible Panels Handling
    function initCollapsiblePanels() {
        const collapseButtons = document.querySelectorAll(".panel-collapse-btn");

        function getCollapsedPanelsState() {
            try {
                const raw = sessionStorage.getItem("xray_collapsed_panels");
                return raw ? JSON.parse(raw) : {};
            } catch (_) {
                return {};
            }
        }

        function saveCollapsedPanelsState(state) {
            try {
                sessionStorage.setItem("xray_collapsed_panels", JSON.stringify(state));
            } catch (_) {}
        }

        collapseButtons.forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                const panelId = btn.getAttribute("data-panel");
                const panel = panelId ? document.getElementById(panelId) || document.querySelector("." + panelId) : btn.closest(".panel");
                if (!panel) return;

                const isCurrentlyCollapsed = panel.classList.contains("is-collapsed");
                const willCollapse = !isCurrentlyCollapsed;

                panel.classList.toggle("is-collapsed", willCollapse);
                btn.setAttribute("aria-expanded", String(!willCollapse));

                const key = panelId || panel.className.split(" ").find(c => c.startsWith("panel-")) || "panel";
                const state = getCollapsedPanelsState();
                state[key] = willCollapse;
                saveCollapsedPanelsState(state);
            });
        });

        // Restore collapsed panels
        const savedState = getCollapsedPanelsState();
        collapseButtons.forEach(function (btn) {
            const panelId = btn.getAttribute("data-panel");
            const panel = panelId ? document.getElementById(panelId) || document.querySelector("." + panelId) : btn.closest(".panel");
            if (!panel) return;
            const key = panelId || panel.className.split(" ").find(c => c.startsWith("panel-")) || "panel";
            if (savedState[key]) {
                panel.classList.add("is-collapsed");
                btn.setAttribute("aria-expanded", "false");
            }
        });
    }

    // 11. Initialization
    function init() {
        initPresets();
        initEvents();
        initMoreMenu();
        initDensityPreference();
        initCollapsiblePanels();
        initCodeMirror();

        if (window.XRayAnimator && window.XRayAnimator.init) {
            window.XRayAnimator.init();
        }

        // Populate Custom Code Playground with default introductory example
        setEditorCode(DEFAULT_PYTHON_EXAMPLE, true);

        updateEditorGutter();
        syncEditorScroll();
        resetTraceVisuals();

        const savedMode = (function () {
            try { return localStorage.getItem("xray_ui_mode") || "debugging"; } catch (_) { return "debugging"; }
        })();
        applyUIMode(savedMode);
        if (window.location.hash && window.location.hash.startsWith("#code=")) {
            checkUrlHashForCode();
        } else {
            updateStatus("Ready · Custom Code");
        }

        // Expose inspection hooks for browser testing, automation, and DevTools
        window.__XRAY_APP__ = {
            get traceData() { return traceData; },
            get currentStepIndex() { return currentStepIndex; },
            goToStep: goToStep,
            toggleBreakpoint: toggleBreakpoint,
            continueToBreakpoint: continueToBreakpoint,
            getCodeMirror: () => cmEditor
        };
        try {
            Object.defineProperty(window, "traceData", {
                get: () => traceData,
                configurable: true
            });
            window.goToStep = goToStep;
        } catch (_) {}
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

})();
