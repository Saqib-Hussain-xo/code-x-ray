/**
 * X-Ray Execution Agent: Adaptive 2D Matrix Stage Controller
 * File: static/js/matrix-stage.js
 *
 * Renders two-dimensional rectangular grids with row/column index headers,
 * cell coordinate badges, active cell access highlights, and scroll containers.
 *
 * Strict security & anti-vibe-coding rules:
 * - Zero eval() or unsafe innerHTML insertion
 * - Zero em dashes, zero emojis, zero gradients
 * - Respects prefers-reduced-motion
 */

(function () {
    "use strict";

    function formatCellValue(val) {
        if (val === null) return "None";
        if (val === undefined) return "-";
        if (typeof val === "boolean") return val ? "T" : "F";
        if (typeof val === "string") return val;
        if (typeof val === "number") return String(val);
        if (Array.isArray(val)) {
            try {
                const s = JSON.stringify(val);
                return s.length > 8 ? s.slice(0, 7) + "…" : s;
            } catch (_) {
                return "[...]";
            }
        }
        return String(val);
    }

    const XRayMatrixStage = {
        render: function (containerEl, step, currentStepIndex, executionSteps) {
            if (!containerEl) return false;

            const sequences = (step && step.sequences) ? step.sequences : {};
            let activeMatrixName = null;
            let activeMatrixInfo = null;

            for (const name of Object.keys(sequences)) {
                if (sequences[name].is_2d_matrix && sequences[name].matrix_elements) {
                    activeMatrixName = name;
                    activeMatrixInfo = sequences[name];
                    break;
                }
            }

            if (!activeMatrixName || !activeMatrixInfo) {
                containerEl.style.display = "none";
                containerEl.replaceChildren();
                return false;
            }

            containerEl.style.display = "block";

            // Universal Reversible Semantic State Resolution for 2D Matrix
            const currIdx = (typeof currentStepIndex === "number") ? currentStepIndex : 0;
            const stepsList = Array.isArray(executionSteps) ? executionSteps : [step];

            const activeCoords = new Set();
            const modifiedCoords = new Set();
            const foundCoords = new Set();
            const visitedCoords = new Set();

            // 1. Scan historical steps up to current step for found and visited cells
            const maxStep = Math.min(currIdx, stepsList.length - 1);
            for (let s = 0; s <= maxStep; s++) {
                const st = stepsList[s];
                if (!st || !Array.isArray(st.events)) continue;

                for (let eIdx = 0; eIdx < st.events.length; eIdx++) {
                    const ev = st.events[eIdx];
                    if (ev.target !== activeMatrixName) continue;

                    const r = (ev.row !== undefined) ? ev.row : (Array.isArray(ev.indices) ? ev.indices[0] : null);
                    const c = (ev.col !== undefined) ? ev.col : (Array.isArray(ev.indices) ? ev.indices[1] : null);
                    if (r === null || c === null || r === undefined || c === undefined) continue;
                    const coordKey = `${r}:${c}`;

                    if (ev.semantic_state === "found" || ev.type === "found" || ev.type === "search_found") {
                        foundCoords.add(coordKey);
                    } else if (s < currIdx) {
                        visitedCoords.add(coordKey);
                    } else if (s === currIdx) {
                        if (ev.semantic_state === "modified" || ev.type === "mutation" || ev.type === "swap") {
                            modifiedCoords.add(coordKey);
                        } else {
                            activeCoords.add(coordKey);
                        }
                    }
                }
            }

            // Also check current step events directly
            const currEvents = Array.isArray(step.events) ? step.events : [];
            for (let i = 0; i < currEvents.length; i++) {
                const ev = currEvents[i];
                if (ev.target !== activeMatrixName) continue;
                const r = (ev.row !== undefined) ? ev.row : (Array.isArray(ev.indices) ? ev.indices[0] : null);
                const c = (ev.col !== undefined) ? ev.col : (Array.isArray(ev.indices) ? ev.indices[1] : null);
                if (r === null || c === null || r === undefined || c === undefined) continue;
                const coordKey = `${r}:${c}`;

                if (ev.semantic_state === "found" || ev.type === "found" || ev.type === "search_found") {
                    foundCoords.add(coordKey);
                } else if (ev.semantic_state === "modified" || ev.type === "mutation" || ev.type === "swap") {
                    modifiedCoords.add(coordKey);
                } else {
                    activeCoords.add(coordKey);
                }
            }

            const rows = activeMatrixInfo.rows;
            const cols = activeMatrixInfo.cols;
            const matrixData = activeMatrixInfo.matrix_elements;

            // Reuse existing container if dimensions match
            let gridWrapper = containerEl.querySelector(".matrix-grid-wrapper");
            const expectedDim = `${rows}x${cols}`;

            if (!gridWrapper || gridWrapper.getAttribute("data-dimensions") !== expectedDim || gridWrapper.getAttribute("data-matrix-name") !== activeMatrixName) {
                containerEl.replaceChildren();

                // Matrix Header Label
                const headerRow = document.createElement("div");
                headerRow.className = "matrix-label-row";

                const nameSpan = document.createElement("span");
                nameSpan.className = "matrix-label-name";
                nameSpan.textContent = activeMatrixName;

                const dimBadge = document.createElement("span");
                dimBadge.className = "matrix-label-dim";
                dimBadge.textContent = `2D MATRIX [${rows} × ${cols}]`;

                headerRow.appendChild(nameSpan);
                headerRow.appendChild(dimBadge);
                containerEl.appendChild(headerRow);

                // Scroll Container for large grids
                const scrollContainer = document.createElement("div");
                scrollContainer.className = "matrix-scroll-container";

                gridWrapper = document.createElement("div");
                gridWrapper.className = "matrix-grid-wrapper";
                gridWrapper.setAttribute("data-dimensions", expectedDim);
                gridWrapper.setAttribute("data-matrix-name", activeMatrixName);

                // CSS Grid Template Columns: 1 header col (row index) + N data cols
                gridWrapper.style.gridTemplateColumns = `36px repeat(${cols}, minmax(46px, 1fr))`;

                // Top-left blank corner
                const corner = document.createElement("div");
                corner.className = "matrix-header-cell matrix-corner-cell";
                corner.textContent = "r\\c";
                gridWrapper.appendChild(corner);

                // Top column index headers
                for (let c = 0; c < cols; c++) {
                    const colHeader = document.createElement("div");
                    colHeader.className = "matrix-header-cell matrix-col-header";
                    colHeader.textContent = String(c);
                    gridWrapper.appendChild(colHeader);
                }

                // Grid rows: row index header + M cell data elements
                for (let r = 0; r < rows; r++) {
                    const rowHeader = document.createElement("div");
                    rowHeader.className = "matrix-header-cell matrix-row-header";
                    rowHeader.textContent = String(r);
                    gridWrapper.appendChild(rowHeader);

                    for (let c = 0; c < cols; c++) {
                        const cell = document.createElement("div");
                        cell.className = "matrix-cell";
                        cell.setAttribute("data-row", String(r));
                        cell.setAttribute("data-col", String(c));

                        const coordBadge = document.createElement("span");
                        coordBadge.className = "matrix-cell-coord";
                        coordBadge.textContent = `${r},${c}`;

                        const valSpan = document.createElement("span");
                        valSpan.className = "matrix-cell-val";
                        const val = (matrixData[r] && matrixData[r][c] !== undefined) ? matrixData[r][c] : "-";
                        valSpan.textContent = formatCellValue(val);

                        cell.appendChild(coordBadge);
                        cell.appendChild(valSpan);
                        gridWrapper.appendChild(cell);
                    }
                }

                scrollContainer.appendChild(gridWrapper);
                containerEl.appendChild(scrollContainer);
            } else {
                // In-place update to preserve DOM stability
                const cells = gridWrapper.querySelectorAll(".matrix-cell");
                for (let i = 0; i < cells.length; i++) {
                    const cell = cells[i];
                    const r = parseInt(cell.getAttribute("data-row"), 10);
                    const c = parseInt(cell.getAttribute("data-col"), 10);
                    const valSpan = cell.querySelector(".matrix-cell-val");
                    const val = (matrixData[r] && matrixData[r][c] !== undefined) ? matrixData[r][c] : "-";
                    const formatted = formatCellValue(val);
                    if (valSpan && valSpan.textContent !== formatted) {
                        valSpan.textContent = formatted;
                    }
                }
            }

            // Update semantic states and coordinates
            const cells = gridWrapper.querySelectorAll(".matrix-cell");
            for (let i = 0; i < cells.length; i++) {
                const cell = cells[i];
                const r = cell.getAttribute("data-row");
                const c = cell.getAttribute("data-col");
                const key = `${r}:${c}`;

                cell.classList.remove(
                    "matrix-cell-active",
                    "semantic-active",
                    "semantic-visited",
                    "semantic-modified",
                    "semantic-found",
                    "semantic-neutral"
                );

                if (foundCoords.has(key)) {
                    cell.classList.add("semantic-found");
                } else if (activeCoords.has(key)) {
                    cell.classList.add("matrix-cell-active", "semantic-active");
                } else if (modifiedCoords.has(key)) {
                    cell.classList.add("semantic-modified");
                } else if (visitedCoords.has(key)) {
                    cell.classList.add("semantic-visited");
                } else {
                    cell.classList.add("semantic-neutral");
                }
            }

            return true;
        }
    };

    window.XRayMatrixStage = XRayMatrixStage;

})();
