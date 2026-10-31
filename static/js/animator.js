/**
 * X-Ray Execution Agent: Unified Animation Controller
 * File: static/js/animator.js
 *
 * Implements physics-inspired projectile swap animations via dedicated ghost overlay,
 * FLIP pointer gliding, operation-aware comparison elevation, and speed-adaptive timing.
 *
 * Strict security & anti-vibe-coding rules:
 * - Zero eval() or unsafe innerHTML insertion
 * - Zero em dashes, zero emojis, zero gradients
 * - Zero mutation of execution trace data
 * - Respects prefers-reduced-motion
 */

(function () {
    "use strict";

    // 1. State, Cache & Active Animation Handles
    let previousPointerRects = new Map();
    let previousCellRects = new Map();
    let activeAnimations = [];
    let isRapidNavigation = false;
    let rapidNavTimeout = null;
    let prefersReducedMotion = false;

    // Check prefers-reduced-motion media query
    if (window.matchMedia) {
        const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
        prefersReducedMotion = motionQuery.matches;
        motionQuery.addEventListener("change", function (e) {
            prefersReducedMotion = e.matches;
            updateAnimationSpeed();
        });
    }

    // 2. Speed Adjustment Helpers
    function getSpeedDuration() {
        if (prefersReducedMotion) return 1;

        const speedSelect = document.getElementById("speed-select");
        const speed = parseFloat(speedSelect ? speedSelect.value : "1.0") || 1.0;

        if (speed >= 4.0) return 70;
        if (speed >= 2.0) return 130;
        if (speed <= 0.5) return 380;
        return 220; // 1.0x baseline duration in ms
    }

    function getSwapDuration() {
        if (prefersReducedMotion) return 1;

        const speedSelect = document.getElementById("speed-select");
        const speed = parseFloat(speedSelect ? speedSelect.value : "1.0") || 1.0;

        if (speed >= 4.0) return 180;
        if (speed >= 2.0) return 320;
        if (speed <= 0.5) return 850;
        return 580; // 1.0x baseline swap duration in ms (within 500-650ms range)
    }

    function updateAnimationSpeed() {
        const duration = getSpeedDuration();
        document.documentElement.style.setProperty("--anim-duration", `${duration}ms`);
    }

    // 3. FLIP Pointer Transition Implementation
    function capturePointerPositions() {
        previousPointerRects.clear();
        if (isRapidNavigation || prefersReducedMotion) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        const indicators = stage.querySelectorAll(".pointer-indicator");
        for (let i = 0; i < indicators.length; i++) {
            const el = indicators[i];
            const name = el.textContent.trim().toLowerCase();
            const seqBox = el.closest(".sequence-container");
            const seqName = seqBox ? (seqBox.getAttribute("data-seq-name") || "") : "";
            const key = `${seqName}:${name}`;
            previousPointerRects.set(key, el.getBoundingClientRect());
        }
    }

    function captureCellPositions() {
        previousCellRects.clear();
        if (isRapidNavigation || prefersReducedMotion) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        const cells = stage.querySelectorAll(".memory-block-cell");
        for (let i = 0; i < cells.length; i++) {
            const el = cells[i];
            const idx = el.getAttribute("data-index");
            const seqBox = el.closest(".sequence-container");
            const seqName = seqBox ? (seqBox.getAttribute("data-seq-name") || "") : "";
            if (seqName && idx !== null) {
                const key = `${seqName}:${idx}`;
                previousCellRects.set(key, el.getBoundingClientRect());
            }
        }
    }

    function animatePointers() {
        if (isRapidNavigation || prefersReducedMotion) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        const duration = getSpeedDuration();
        const indicators = stage.querySelectorAll(".pointer-indicator");

        for (let i = 0; i < indicators.length; i++) {
            const el = indicators[i];
            const name = el.textContent.trim().toLowerCase();
            const seqBox = el.closest(".sequence-container");
            const seqName = seqBox ? (seqBox.getAttribute("data-seq-name") || "") : "";
            const key = `${seqName}:${name}`;

            if (previousPointerRects.has(key)) {
                const oldRect = previousPointerRects.get(key);
                const newRect = el.getBoundingClientRect();
                const deltaX = oldRect.left - newRect.left;

                if (Math.abs(deltaX) > 1 && Math.abs(deltaX) < 1200) {
                    el.style.transform = `translateX(${deltaX}px)`;
                    el.style.transition = "none";

                    requestAnimationFrame(function () {
                        el.style.transition = `transform ${duration}ms cubic-bezier(0.2, 0, 0, 1)`;
                        el.style.transform = "translateX(0)";
                    });
                }
            } else {
                el.classList.add("pointer-enter");
            }
        }
    }

    // 4. Projectile-Style Curved Swap Animation via Dedicated Ghost Overlay & Web Animations API
    function animateSwap(seqName, idxA, idxB, fromValues) {
        if (isRapidNavigation || prefersReducedMotion) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        const seqBox = stage.querySelector(`.sequence-container[data-seq-name="${seqName}"]`);
        if (!seqBox) return;

        const blocksRow = seqBox.querySelector(".sequence-blocks-row");
        if (!blocksRow) return;

        const i = Math.min(idxA, idxB);
        const j = Math.max(idxA, idxB);

        const cellA = blocksRow.children[i];
        const cellB = blocksRow.children[j];
        if (!cellA || !cellB) return;

        // Ensure animation overlay container exists (fixed viewport overlay)
        let overlay = document.getElementById("sequence-animation-overlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = "sequence-animation-overlay";
            overlay.className = "sequence-animation-overlay";
            overlay.setAttribute("aria-hidden", "true");
            document.body.appendChild(overlay);
        }

        const rectA = cellA.getBoundingClientRect();
        const rectB = cellB.getBoundingClientRect();

        const dx = rectB.left - rectA.left;
        if (Math.abs(dx) < 2) return;

        const dist = Math.abs(dx);

        // Substantial physical arc height: minimum 88px for adjacent elements up to 130px for distant elements
        const H = Math.min(130, Math.max(88, 82 + dist * 0.18));
        const HA = H;                       // Ghost A takes higher arc in front (88px to 130px)
        const HB = Math.round(H * 0.65);    // Ghost B takes lower arc behind (57px to 84px)

        const duration = getSwapDuration();

        // Retrieve values for both cells
        const valA = (fromValues && fromValues.length >= 2) ? String(fromValues[0]) : cellB.textContent;
        const valB = (fromValues && fromValues.length >= 2) ? String(fromValues[1]) : cellA.textContent;

        // Create Ghost A (starts at slot A, carries valA to slot B)
        const ghostA = document.createElement("div");
        ghostA.className = "memory-block-cell ghost-projectile-cell";
        ghostA.textContent = valA;
        ghostA.style.position = "fixed";
        ghostA.style.left = `${rectA.left}px`;
        ghostA.style.top = `${rectA.top}px`;
        ghostA.style.width = `${rectA.width}px`;
        ghostA.style.height = `${rectA.height}px`;
        ghostA.style.zIndex = "10005";

        // Create Ghost B (starts at slot B, carries valB to slot A)
        const ghostB = document.createElement("div");
        ghostB.className = "memory-block-cell ghost-projectile-cell";
        ghostB.textContent = valB;
        ghostB.style.position = "fixed";
        ghostB.style.left = `${rectB.left}px`;
        ghostB.style.top = `${rectB.top}px`;
        ghostB.style.width = `${rectB.width}px`;
        ghostB.style.height = `${rectB.height}px`;
        ghostB.style.zIndex = "10003";

        // Hide underlying cells during flight
        cellA.style.visibility = "hidden";
        cellB.style.visibility = "hidden";

        overlay.appendChild(ghostA);
        overlay.appendChild(ghostB);

        // Trajectory Keyframes for Ghost A (travels +dx)
        const keyframesA = [
            {
                transform: "translate(0px, 0px) scale(1)",
                boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
                zIndex: 10005,
                offset: 0
            },
            {
                transform: `translate(${dx * 0.15}px, ${-HA * 0.55}px) scale(1.08)`,
                boxShadow: "0 10px 18px rgba(0, 0, 0, 0.4), 0 0 10px rgba(88, 166, 255, 0.4)",
                zIndex: 10005,
                offset: 0.16
            },
            {
                transform: `translate(${dx * 0.35}px, ${-HA * 0.90}px) scale(1.14)`,
                boxShadow: "0 18px 28px rgba(0, 0, 0, 0.5), 0 0 16px rgba(88, 166, 255, 0.55)",
                zIndex: 10005,
                offset: 0.36
            },
            {
                transform: `translate(${dx * 0.50}px, ${-HA}px) scale(1.18)`,
                boxShadow: "0 24px 36px rgba(0, 0, 0, 0.6), 0 0 20px rgba(88, 166, 255, 0.7)",
                zIndex: 10005,
                offset: 0.50
            },
            {
                transform: `translate(${dx * 0.65}px, ${-HA * 0.90}px) scale(1.14)`,
                boxShadow: "0 18px 28px rgba(0, 0, 0, 0.5), 0 0 16px rgba(88, 166, 255, 0.55)",
                zIndex: 10005,
                offset: 0.64
            },
            {
                transform: `translate(${dx * 0.85}px, ${-HA * 0.55}px) scale(1.08)`,
                boxShadow: "0 10px 18px rgba(0, 0, 0, 0.4), 0 0 10px rgba(88, 166, 255, 0.4)",
                zIndex: 10005,
                offset: 0.84
            },
            {
                transform: `translate(${dx}px, 3px) scale(0.97)`,
                boxShadow: "0 4px 8px rgba(0, 0, 0, 0.3)",
                zIndex: 10005,
                offset: 0.94
            },
            {
                transform: `translate(${dx}px, 0px) scale(1)`,
                boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
                zIndex: 10005,
                offset: 1
            }
        ];

        // Trajectory Keyframes for Ghost B (travels -dx)
        const keyframesB = [
            {
                transform: "translate(0px, 0px) scale(1)",
                boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
                zIndex: 10003,
                offset: 0
            },
            {
                transform: `translate(${-dx * 0.15}px, ${-HB * 0.55}px) scale(0.96)`,
                boxShadow: "0 6px 12px rgba(0, 0, 0, 0.35)",
                zIndex: 10003,
                offset: 0.16
            },
            {
                transform: `translate(${-dx * 0.35}px, ${-HB * 0.90}px) scale(0.93)`,
                boxShadow: "0 12px 18px rgba(0, 0, 0, 0.4)",
                zIndex: 10003,
                offset: 0.36
            },
            {
                transform: `translate(${-dx * 0.50}px, ${-HB}px) scale(0.91)`,
                boxShadow: "0 14px 22px rgba(0, 0, 0, 0.45)",
                zIndex: 10003,
                offset: 0.50
            },
            {
                transform: `translate(${-dx * 0.65}px, ${-HB * 0.90}px) scale(0.93)`,
                boxShadow: "0 12px 18px rgba(0, 0, 0, 0.4)",
                zIndex: 10003,
                offset: 0.64
            },
            {
                transform: `translate(${-dx * 0.85}px, ${-HB * 0.55}px) scale(0.96)`,
                boxShadow: "0 6px 12px rgba(0, 0, 0, 0.35)",
                zIndex: 10003,
                offset: 0.84
            },
            {
                transform: `translate(${-dx}px, 3px) scale(0.97)`,
                boxShadow: "0 3px 6px rgba(0, 0, 0, 0.3)",
                zIndex: 10003,
                offset: 0.94
            },
            {
                transform: `translate(${-dx}px, 0px) scale(1)`,
                boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
                zIndex: 10003,
                offset: 1
            }
        ];

        const animOptions = {
            duration: duration,
            easing: "cubic-bezier(0.4, 0.0, 0.2, 1.0)",
            fill: "forwards"
        };

        try {
            const animA = ghostA.animate(keyframesA, animOptions);
            const animB = ghostB.animate(keyframesB, animOptions);

            if (document.timeline && typeof document.timeline.currentTime === "number") {
                animA.startTime = document.timeline.currentTime;
                animB.startTime = document.timeline.currentTime;
            }

            activeAnimations.push(animA, animB);

            let finished = false;
            const cleanup = function () {
                if (finished) return;
                finished = true;

                try {
                    if (ghostA.parentNode) ghostA.remove();
                    if (ghostB.parentNode) ghostB.remove();
                } catch (_) {}

                cellA.style.visibility = "";
                cellB.style.visibility = "";
                cellA.classList.add("cell-settling");
                cellB.classList.add("cell-settling");

                setTimeout(function () {
                    cellA.classList.remove("cell-settling");
                    cellB.classList.remove("cell-settling");
                }, 180);
            };

            if (animA.finished && typeof animA.finished.then === "function") {
                animA.finished.then(cleanup).catch(cleanup);
            }
            animA.onfinish = cleanup;
            setTimeout(cleanup, duration + 30);
        } catch (_) {
            if (ghostA.parentNode) ghostA.remove();
            if (ghostB.parentNode) ghostB.remove();
            cellA.style.visibility = "";
            cellB.style.visibility = "";
        }
    }

    // 5. Operation-Aware Routing
    function applyOperationAnimations(step, isSteppingBackward) {
        if (!step || !Array.isArray(step.operations) || isRapidNavigation || prefersReducedMotion || isSteppingBackward) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        for (const op of step.operations) {
            if (op.type === "swap") {
                const seq = op.sequence;
                const indices = op.indices || [];
                const fromVals = op.from_values;
                if (indices.length === 2) {
                    animateSwap(seq, indices[0], indices[1], fromVals);
                }
            } else if (op.type === "comparison") {
                const seq = op.sequence;
                const indices = op.indices || [];
                const seqBox = stage.querySelector(`.sequence-container[data-seq-name="${seq}"]`);
                if (seqBox) {
                    const blocksRow = seqBox.querySelector(".sequence-blocks-row");
                    if (blocksRow) {
                        for (const idx of indices) {
                            const cell = blocksRow.children[idx];
                            if (cell) {
                                cell.classList.add("cell-comparing");
                            }
                        }
                    }
                }
            } else if (op.type === "mutation") {
                const seq = op.sequence;
                const idx = op.index !== undefined ? op.index : (op.indices ? op.indices[0] : null);
                if (idx !== null) {
                    const seqBox = stage.querySelector(`.sequence-container[data-seq-name="${seq}"]`);
                    if (seqBox) {
                        const blocksRow = seqBox.querySelector(".sequence-blocks-row");
                        if (blocksRow && blocksRow.children[idx]) {
                            blocksRow.children[idx].classList.add("anim-pulse-mutation");
                        }
                    }
                }
            } else if (op.type === "shift") {
                const seq = op.sequence;
                const indices = op.indices || [];
                const seqBox = stage.querySelector(`.sequence-container[data-seq-name="${seq}"]`);
                if (seqBox) {
                    const blocksRow = seqBox.querySelector(".sequence-blocks-row");
                    if (blocksRow) {
                        const duration = getSpeedDuration();
                        for (const idx of indices) {
                            const cell = blocksRow.children[idx];
                            if (cell) {
                                try {
                                    const anim = cell.animate([
                                        { transform: "translateX(-30px)" },
                                        { transform: "translateX(0)" }
                                    ], {
                                        duration: duration,
                                        easing: "cubic-bezier(0.2, 0, 0, 1)"
                                    });
                                    activeAnimations.push(anim);
                                } catch (_) {}
                            }
                        }
                    }
                }
            }
        }
    }

    // 6. Memory Table Transitions
    function animateMemoryTable(step, prevStep) {
        if (isRapidNavigation || prefersReducedMotion) return;

        const tableBody = document.getElementById("memory-table-body");
        if (!tableBody) return;

        const newBadges = tableBody.querySelectorAll(".status-badge-inline.new");
        for (let i = 0; i < newBadges.length; i++) {
            const row = newBadges[i].closest("tr");
            if (row) {
                row.classList.add("row-enter");
            }
        }
    }

    // 7. Public API Export
    const XRayAnimator = {
        init: function () {
            updateAnimationSpeed();
            const speedSelect = document.getElementById("speed-select");
            if (speedSelect) {
                speedSelect.addEventListener("change", updateAnimationSpeed);
            }
        },

        beforeStepRender: function (step, prevStep) {
            capturePointerPositions();
            captureCellPositions();
        },

        afterStepRender: function (step, prevStep, isSteppingBackward) {
            animatePointers();
            applyOperationAnimations(step, isSteppingBackward);
            animateMemoryTable(step, prevStep);
        },

        cancelAnimations: function () {
            isRapidNavigation = true;
            previousPointerRects.clear();
            previousCellRects.clear();

            for (let i = 0; i < activeAnimations.length; i++) {
                try {
                    activeAnimations[i].cancel();
                } catch (_) {}
            }
            activeAnimations = [];

            const overlay = document.getElementById("sequence-animation-overlay");
            if (overlay) {
                overlay.replaceChildren();
            }

            const hiddenCells = document.querySelectorAll(".memory-block-cell");
            for (let i = 0; i < hiddenCells.length; i++) {
                if (hiddenCells[i].style.visibility === "hidden") {
                    hiddenCells[i].style.visibility = "";
                }
            }

            if (rapidNavTimeout) clearTimeout(rapidNavTimeout);
            rapidNavTimeout = setTimeout(function () {
                isRapidNavigation = false;
            }, 120);
        },

        getDuration: function () {
            return getSpeedDuration();
        },

        getSwapDuration: function () {
            return getSwapDuration();
        },

        animateSwap: animateSwap
    };

    window.XRayAnimator = XRayAnimator;

})();
