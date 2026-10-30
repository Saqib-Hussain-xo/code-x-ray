/**
 * X-Ray Execution Agent: Unified Animation Controller
 * File: static/js/animator.js
 *
 * Implements physics-inspired projectile swap animations, FLIP pointer gliding,
 * operation-aware comparison elevation, mutation pulses, and speed-adaptive timing.
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

        if (speed >= 4.0) return 140;
        if (speed >= 2.0) return 240;
        if (speed <= 0.5) return 750;
        return 460; // 1.0x baseline swap duration in ms (within 400-550ms range)
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

    // 4. Projectile-Style Curved Swap Animation via Web Animations API
    function animateSwap(seqName, idxA, idxB) {
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

        const rectA = cellA.getBoundingClientRect();
        const rectB = cellB.getBoundingClientRect();
        const dx = rectB.left - rectA.left;

        if (Math.abs(dx) < 2) return;

        // Calculate adaptive arc height based on travel distance
        const H = Math.min(65, Math.max(24, 18 + Math.abs(dx) * 0.14));
        const HA = H;          // Cell A takes higher arc in front
        const HB = H * 0.65;   // Cell B takes lower arc behind to avoid mid-air collision

        const duration = getSwapDuration();

        // Keyframes for cellA (currently showing value from idxB, travels from +dx to 0)
        const keyframesA = [
            {
                transform: `translate(${dx}px, 0px) scale(1)`,
                zIndex: 12,
                offset: 0
            },
            {
                transform: `translate(${dx * 0.75}px, ${-HA * 0.75}px) scale(1.05)`,
                zIndex: 12,
                offset: 0.25
            },
            {
                transform: `translate(${dx * 0.5}px, ${-HA}px) scale(1.08)`,
                zIndex: 12,
                offset: 0.5
            },
            {
                transform: `translate(${dx * 0.25}px, ${-HA * 0.75}px) scale(1.05)`,
                zIndex: 12,
                offset: 0.75
            },
            {
                transform: `translate(0px, 2px) scale(1.02)`,
                zIndex: 12,
                offset: 0.92
            },
            {
                transform: `translate(0px, 0px) scale(1)`,
                zIndex: 1,
                offset: 1
            }
        ];

        // Keyframes for cellB (currently showing value from idxA, travels from -dx to 0)
        const keyframesB = [
            {
                transform: `translate(${-dx}px, 0px) scale(1)`,
                zIndex: 10,
                offset: 0
            },
            {
                transform: `translate(${-dx * 0.75}px, ${-HB * 0.75}px) scale(0.96)`,
                zIndex: 10,
                offset: 0.25
            },
            {
                transform: `translate(${-dx * 0.5}px, ${-HB}px) scale(0.93)`,
                zIndex: 10,
                offset: 0.5
            },
            {
                transform: `translate(${-dx * 0.25}px, ${-HB * 0.75}px) scale(0.96)`,
                zIndex: 10,
                offset: 0.75
            },
            {
                transform: `translate(0px, 2px) scale(0.98)`,
                zIndex: 10,
                offset: 0.92
            },
            {
                transform: `translate(0px, 0px) scale(1)`,
                zIndex: 1,
                offset: 1
            }
        ];

        const animOptions = {
            duration: duration,
            easing: "cubic-bezier(0.25, 1, 0.5, 1)",
            fill: "none"
        };

        cellA.classList.add("cell-swap-active");
        cellB.classList.add("cell-swap-active");

        try {
            const animA = cellA.animate(keyframesA, animOptions);
            const animB = cellB.animate(keyframesB, animOptions);

            activeAnimations.push(animA, animB);

            const settleHandler = function () {
                cellA.classList.remove("cell-swap-active");
                cellB.classList.remove("cell-swap-active");
                cellA.classList.add("cell-settling");
                cellB.classList.add("cell-settling");
                setTimeout(function () {
                    cellA.classList.remove("cell-settling");
                    cellB.classList.remove("cell-settling");
                }, 200);
            };

            animA.onfinish = settleHandler;
        } catch (_) {
            cellA.classList.remove("cell-swap-active");
            cellB.classList.remove("cell-swap-active");
        }
    }

    // 5. Operation-Aware Routing
    function applyOperationAnimations(step) {
        if (!step || !Array.isArray(step.operations) || isRapidNavigation || prefersReducedMotion) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        for (const op of step.operations) {
            if (op.type === "swap") {
                const seq = op.sequence;
                const indices = op.indices || [];
                if (indices.length === 2) {
                    animateSwap(seq, indices[0], indices[1]);
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
            applyOperationAnimations(step);
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
