/**
 * X-Ray Execution Agent: Frontend Interactive Controller
 * File: static/js/app.js
 *
 * Implements deterministic timeline navigation, live memory diffing,
 * dynamic sequence/pointer rendering, cumulative console synchronization,
 * and algorithm preset loading.
 *
 * Strict security & anti-vibe-coding rules:
 * - Zero eval() or unsafe innerHTML insertion of runtime data
 * - Zero em dashes, zero emojis, zero gradients
 * - Monospace precision and robust state synchronization
 */

(function () {
    "use strict";

    // 1. State Store
    let traceData = null;       // Full trace payload from /api/trace
    let currentStepIndex = 0;   // Active step pointer
    let isPlaying = false;      // Playback active state
    let playTimer = null;       // Active playback timeout ID
    let isTracing = false;      // API request in-flight flag
    let currentActiveLineNo = null; // Active highlighted source line
    let hasTriggeredDiwaliThisRun = false; // Diwali animation single-fire guard
    const API_BASE_URL = window.XRAY_API_BASE_URL || "";

    // 2. DOM Elements Cache
    const presetSelect = document.getElementById("preset-select");
    const btnRun = document.getElementById("btn-run");
    const btnClear = document.getElementById("btn-clear");
    const traceStatus = document.getElementById("trace-status");
    const codeInput = document.getElementById("code-input");
    const editorGutter = document.getElementById("editor-gutter");
    const editorActiveLine = document.getElementById("editor-active-line");

    const memoryTableBody = document.getElementById("memory-table-body");
    const stageEmpty = document.getElementById("stage-empty");
    const sequencesContainer = document.getElementById("sequences-container");
    const consoleOutput = document.getElementById("console-output");
    const consolePre = consoleOutput ? consoleOutput.closest(".console-pre") : null;

    const btnFirst = document.getElementById("btn-first");
    const btnPrev = document.getElementById("btn-prev");
    const btnPlay = document.getElementById("btn-play");
    const btnNext = document.getElementById("btn-next");
    const btnLast = document.getElementById("btn-last");
    const timelineScrubber = document.getElementById("timeline-scrubber");
    const stepCounter = document.getElementById("step-counter");
    const speedSelect = document.getElementById("speed-select");

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

    // Gutter and Highlighting Synchronization
    function updateEditorGutter() {
        if (!editorGutter || !codeInput) return;
        const code = codeInput.value;
        const lines = code.split("\n");
        const lineCount = Math.max(1, lines.length);

        const fragment = document.createDocumentFragment();
        for (let i = 1; i <= lineCount; i++) {
            const lineDiv = document.createElement("div");
            lineDiv.className = "gutter-line";
            lineDiv.setAttribute("data-line", String(i));
            if (currentActiveLineNo === i) {
                lineDiv.classList.add("gutter-active");
            }

            const marker = document.createElement("span");
            marker.className = "gutter-marker";
            marker.textContent = "▶";

            const num = document.createElement("span");
            num.className = "gutter-number";
            num.textContent = String(i);

            lineDiv.appendChild(marker);
            lineDiv.appendChild(num);
            fragment.appendChild(lineDiv);
        }

        editorGutter.replaceChildren(fragment);
        editorGutter.scrollTop = codeInput.scrollTop;
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
        if (!codeInput) return;
        const code = codeInput.value;
        const lines = code.split("\n");

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

        // CRITICAL: Synchronize gutter and active line position AFTER codeInput.scrollTop is updated
        syncEditorScroll();
    }

    // 4. Algorithm Presets Loader
    function initPresets() {
        if (!presetSelect || !codeInput) return;
        presetSelect.addEventListener("change", function () {
            const key = presetSelect.value;
            // Default option ("Load Algorithm Preset..."): do NOT overwrite editor
            if (!key) return;

            const presets = window.ALGORITHM_PRESETS || {};
            if (Object.prototype.hasOwnProperty.call(presets, key)) {
                pause();
                resetTraceVisuals();
                codeInput.value = presets[key];
                codeInput.scrollTop = 0;
                updateEditorGutter();
                highlightEditorLine(null);
                updateStatus(`PRESET LOADED // ${key.toUpperCase()}`);
            }
        });
    }

    // 5. Run & Trace API Client (Preset Only)
    async function runTrace() {
        if (isTracing) return;
        const presetId = presetSelect ? presetSelect.value : "";
        const rawCode = codeInput ? codeInput.value : "";

        if (!presetId || !rawCode.trim()) {
            updateStatus("SELECT PRESET // CHOOSE ALGORITHM", "status-error");
            if (consoleOutput) {
                consoleOutput.textContent = "Please select an algorithm preset from the dropdown menu above to trace.\n";
                consoleOutput.classList.remove("console-empty");
            }
            return;
        }

        pause();
        isTracing = true;
        hasTriggeredDiwaliThisRun = false;
        if (window.stopDiwaliSpark) window.stopDiwaliSpark();
        updateStatus("TRACING // RUNNING...", "status-running");

        if (btnRun) btnRun.disabled = true;
        if (btnClear) btnClear.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/api/trace`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ preset_id: presetId })
            });

            const data = await response.json();

            // Handle errors or HTTP non-200 responses
            if (!response.ok || data.status === "syntax_error") {
                resetTraceVisuals();
                const errMsg = typeof data.error === "string" ? data.error : (data.error && data.error.message ? data.error.message : "Execution failed");
                if (consoleOutput) {
                    consoleOutput.textContent = `Error: ${errMsg}\n`;
                    consoleOutput.classList.remove("console-empty");
                }
                updateStatus("EXECUTION ERROR // CHECK CONSOLE", "status-error");
                return;
            }

            // Verify trace payload has recorded steps
            if (!data.steps || !Array.isArray(data.steps) || data.steps.length === 0) {
                resetTraceVisuals();
                updateStatus("TRACE EMPTY // 0 STEPS", "status-error");
                return;
            }

            // Store trace payload and configure timeline
            traceData = data;
            currentStepIndex = 0;

            // Reflect status based on tracer termination cause
            if (data.status === "completed") {
                updateStatus(`READY // ${data.total_steps} STEPS`, "status-completed");
            } else if (data.status === "step_limit_exceeded") {
                updateStatus(`LIMIT EXCEEDED // ${data.total_steps} STEPS`, "status-running");
            } else if (data.status === "timeout") {
                updateStatus("TIMEOUT // 2.0S LIMIT", "status-error");
            } else if (data.status === "exception") {
                const exc = data.error || {};
                updateStatus(`EXCEPTION // ${exc.type || "RUNTIME ERROR"}`, "status-error");
            } else {
                updateStatus(`READY // ${data.total_steps} STEPS`, "status-completed");
            }

            // Enable transport controls
            if (timelineScrubber) {
                timelineScrubber.disabled = false;
                timelineScrubber.min = "0";
                timelineScrubber.max = String(data.total_steps - 1);
                timelineScrubber.value = "0";
            }
            if (btnPlay) btnPlay.disabled = false;

            renderStep(0);

            // Automatically start playback if there are multiple steps
            if (data.total_steps > 1) {
                play();
            } else {
                pause();
            }

        } catch (fetchErr) {
            resetTraceVisuals();
            updateStatus("NETWORK ERROR // REQUEST FAILED", "status-error");
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
        currentStepIndex = stepIndex;

        const step = traceData.steps[stepIndex];
        const prevStep = (stepIndex > 0) ? traceData.steps[stepIndex - 1] : null;

        // 6A. Update Transport Navigation Controls
        if (timelineScrubber) timelineScrubber.value = String(stepIndex);
        if (stepCounter) stepCounter.textContent = `STEP ${stepIndex + 1} / ${traceData.total_steps}`;

        if (btnFirst) btnFirst.disabled = (stepIndex === 0);
        if (btnPrev) btnPrev.disabled = (stepIndex === 0);
        if (btnNext) btnNext.disabled = (stepIndex === traceData.total_steps - 1);
        if (btnLast) btnLast.disabled = (stepIndex === traceData.total_steps - 1);

        // 6B. Highlight Editor Source Line
        highlightEditorLine(step.line_no);

        // 6C. Render Memory Map Table
        renderMemoryTable(step, prevStep);

        // 6D. Render Sequence & Pointer Stage
        renderSequenceStage(step);

        // 6E. Synchronize Console Output
        renderConsole(step);

        // 6F. Trigger Diwali Celebration Spark if final step reached on completed execution
        if (stepIndex === traceData.total_steps - 1 && traceData.status === "completed") {
            if (window.triggerDiwaliSpark && !hasTriggeredDiwaliThisRun) {
                hasTriggeredDiwaliThisRun = true;
                window.triggerDiwaliSpark();
            }
        } else {
            hasTriggeredDiwaliThisRun = false;
        }
    }

    // 6C. Sub-renderer: Memory Map Table
    function renderMemoryTable(step, prevStep) {
        if (!memoryTableBody) return;
        memoryTableBody.replaceChildren();

        const locals = step.locals_snapshot || {};
        const varNames = Object.keys(locals).sort();

        if (varNames.length === 0) {
            const emptyRow = document.createElement("tr");
            const emptyCell = document.createElement("td");
            emptyCell.colSpan = 5;
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

            // Col 1: Variable Name
            const tdVar = document.createElement("td");
            tdVar.className = "col-var";
            tdVar.textContent = varName;
            if (isNew) {
                tdVar.classList.add("val-new");
            }

            // Col 2: Type
            const tdType = document.createElement("td");
            tdType.className = "col-type";
            tdType.textContent = (step.types && step.types[varName]) ? step.types[varName] : typeof currVal;

            // Col 3: Current Value
            const tdVal = document.createElement("td");
            tdVal.className = "col-val";
            tdVal.textContent = formatValue(currVal);

            // Col 4: Previous Value & Col 5: Status
            const tdPrev = document.createElement("td");
            tdPrev.className = "col-prev";

            const tdStatus = document.createElement("td");
            tdStatus.className = "col-status";

            if (isNew) {
                tdPrev.textContent = "-";
                const badgeNew = document.createElement("span");
                badgeNew.className = "status-badge-inline new";
                badgeNew.textContent = "NEW";
                badgeNew.title = `Variable '${varName}' initialized in local scope`;
                tdStatus.appendChild(badgeNew);
            } else {
                const prevVal = prevLocals[varName];
                const prevFmt = formatValue(prevVal);
                const currFmt = formatValue(currVal);

                tdPrev.textContent = prevFmt;

                // Value comparison to avoid false mutations
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
                    badgeMutated.title = `Mutated from ${prevFmt} to ${currFmt}`;

                    // Concise transition indicator if values are compact
                    if (prevFmt.length <= 10 && currFmt.length <= 10) {
                        badgeMutated.textContent = `${prevFmt} → ${currFmt}`;
                    } else {
                        badgeMutated.textContent = "MUTATED";
                    }
                    tdStatus.appendChild(badgeMutated);
                } else {
                    // Unchanged: visually quiet without heavy badges
                    const quiet = document.createElement("span");
                    quiet.className = "col-status-quiet";
                    quiet.textContent = "-";
                    tdStatus.appendChild(quiet);
                }
            }

            row.appendChild(tdVar);
            row.appendChild(tdType);
            row.appendChild(tdVal);
            row.appendChild(tdPrev);
            row.appendChild(tdStatus);

            memoryTableBody.appendChild(row);
        }
    }

    // 6D. Sub-renderer: Sequence & Pointer Stage
    function renderSequenceStage(step) {
        if (!sequencesContainer || !stageEmpty) return;

        const sequences = step.sequences || {};
        const seqNames = Object.keys(sequences).sort();

        if (seqNames.length === 0) {
            stageEmpty.style.display = "block";
            sequencesContainer.replaceChildren();
            return;
        }

        stageEmpty.style.display = "none";
        sequencesContainer.replaceChildren();

        const allPointers = Array.isArray(step.pointers) ? step.pointers : [];
        const mutations = Array.isArray(step.mutations) ? step.mutations : [];

        for (const seqName of seqNames) {
            const seq = sequences[seqName];
            const seqPointers = allPointers.filter(p => p.target === seqName);
            const isSeqMutated = mutations.includes(seqName);

            // Container for this individual sequence
            const seqBox = document.createElement("div");
            seqBox.className = "sequence-container";

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
                // Find pointers currently pointing to this index
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
                blockCell.textContent = formatCellValue(elements[idx]);

                if (isSeqMutated) {
                    blockCell.classList.add("cell-mutated");
                }

                if (matchedPtrs.length > 0) {
                    // Check if pointer A or B
                    const hasPtrA = matchedPtrs.some(p => p.name === "left" || p.name === "i" || p.name === "start" || p.name === "slow");
                    if (hasPtrA) {
                        blockCell.classList.add("cell-pointer-a");
                    } else {
                        blockCell.classList.add("cell-pointer-b");
                    }
                }
                blocksRow.appendChild(blockCell);

                // Pointer Slot
                const ptrSlot = document.createElement("div");
                ptrSlot.className = "pointer-slot";

                for (let pi = 0; pi < matchedPtrs.length; pi++) {
                    const ptr = matchedPtrs[pi];
                    const ptrIndicator = document.createElement("span");
                    // Alternate between green (ptr-a) and blue (ptr-b) based on convention
                    const isA = (ptr.name === "left" || ptr.name === "i" || ptr.name === "start" || ptr.name === "slow" || pi === 0);
                    ptrIndicator.className = `pointer-indicator ${isA ? "ptr-a" : "ptr-b"}`;
                    ptrIndicator.textContent = ptr.name;
                    ptrSlot.appendChild(ptrIndicator);
                }
                pointersRow.appendChild(ptrSlot);
            }

            trackInner.appendChild(indicesRow);
            trackInner.appendChild(blocksRow);
            trackInner.appendChild(pointersRow);
            track.appendChild(trackInner);
            seqBox.appendChild(track);

            sequencesContainer.appendChild(seqBox);
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
        updatePlayButtonIcon();
        scheduleNextTick();
    }

    function pause() {
        isPlaying = false;
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
        const delay = Math.round(700 / speed);

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

    function goToStep(index) {
        if (!traceData || !traceData.steps || traceData.steps.length === 0) return;
        renderStep(index);
    }

    // 8. Clear and Error Recovery
    function resetTraceVisuals() {
        pause();
        traceData = null;
        currentStepIndex = 0;
        highlightEditorLine(null);
        hasTriggeredDiwaliThisRun = false;
        if (window.stopDiwaliSpark) window.stopDiwaliSpark();

        // Reset transport controls
        if (btnFirst) btnFirst.disabled = true;
        if (btnPrev) btnPrev.disabled = true;
        if (btnPlay) btnPlay.disabled = true;
        if (btnNext) btnNext.disabled = true;
        if (btnLast) btnLast.disabled = true;

        if (timelineScrubber) {
            timelineScrubber.disabled = true;
            timelineScrubber.min = "0";
            timelineScrubber.max = "0";
            timelineScrubber.value = "0";
        }

        if (stepCounter) {
            stepCounter.textContent = "STEP 0 / 0";
        }

        // Reset memory table to default empty state
        if (memoryTableBody) {
            memoryTableBody.replaceChildren();
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 5;
            td.className = "table-empty-message";
            td.textContent = "No active execution frame. Execute a trace to inspect variable snapshots and mutations.";
            tr.appendChild(td);
            memoryTableBody.appendChild(tr);
        }

        // Reset sequence stage to default empty state
        if (stageEmpty) stageEmpty.style.display = "block";
        if (sequencesContainer) sequencesContainer.replaceChildren();

        // Reset console to default empty state
        if (consoleOutput) {
            consoleOutput.textContent = "No standard output recorded. Run a trace to view print() outputs.";
            consoleOutput.classList.add("console-empty");
        }
    }

    function handleClear() {
        pause();
        traceData = null;
        currentStepIndex = 0;
        hasTriggeredDiwaliThisRun = false;
        if (window.stopDiwaliSpark) window.stopDiwaliSpark();

        // Clear editor completely
        if (codeInput) {
            codeInput.value = "";
            codeInput.focus();
        }

        // Reset dropdown to default option
        if (presetSelect) {
            presetSelect.value = "";
        }

        updateEditorGutter();
        highlightEditorLine(null);
        resetTraceVisuals();
        updateStatus("IDLE // AWAITING INPUT");
    }

    // 9. Event Listeners Wiring
    function initEvents() {
        // Code input editor interactions (scrolling, typing, indentation)
        if (codeInput) {
            codeInput.addEventListener("scroll", syncEditorScroll);
            codeInput.addEventListener("input", function () {
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

        // Run button
        if (btnRun) {
            btnRun.addEventListener("click", runTrace);
        }

        // Clear button (empties editor, resets dropdown and visual state)
        if (btnClear) {
            btnClear.addEventListener("click", handleClear);
        }

        // Transport Controls
        if (btnFirst) {
            btnFirst.addEventListener("click", function () {
                pause();
                if (window.stopDiwaliSpark) window.stopDiwaliSpark();
                goToStep(0);
            });
        }

        if (btnPrev) {
            btnPrev.addEventListener("click", function () {
                pause();
                if (window.stopDiwaliSpark) window.stopDiwaliSpark();
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
                goToStep(currentStepIndex + 1);
            });
        }

        if (btnLast) {
            btnLast.addEventListener("click", function () {
                pause();
                if (traceData) goToStep(traceData.total_steps - 1);
            });
        }

        // Timeline range scrubber
        if (timelineScrubber) {
            timelineScrubber.addEventListener("input", function () {
                pause();
                if (window.stopDiwaliSpark) window.stopDiwaliSpark();
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

        // Keyboard Shortcuts (Space, Left, Right, Home, End)
        window.addEventListener("keydown", function (e) {
            // Do not intercept keystrokes while user is editing code
            if (document.activeElement === codeInput) {
                // Allow Ctrl+Enter or Cmd+Enter to trigger Run & Trace
                if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                    e.preventDefault();
                    runTrace();
                }
                return;
            }

            if (!traceData || traceData.total_steps === 0) return;

            if (e.code === "Space") {
                e.preventDefault();
                togglePlay();
            } else if (e.code === "ArrowLeft") {
                e.preventDefault();
                pause();
                goToStep(currentStepIndex - 1);
            } else if (e.code === "ArrowRight") {
                e.preventDefault();
                pause();
                goToStep(currentStepIndex + 1);
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

    // 10. Initialization with robust readyState check
    function init() {
        if (codeInput) {
            codeInput.readOnly = true;
        }
        initPresets();
        initEvents();
        updateEditorGutter();
        syncEditorScroll();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

})();
