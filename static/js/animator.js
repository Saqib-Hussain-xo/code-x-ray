/**
 * X-Ray Execution Agent: Unified Animation Controller
 * File: static/js/animator.js
 *
 * Implements FLIP pointer gliding, memory cell mutation pulses,
 * variable state transitions, and speed-adaptive timing.
 *
 * Strict security & anti-vibe-coding rules:
 * - Zero eval() or unsafe innerHTML insertion
 * - Zero em dashes, zero emojis, zero gradients
 * - Zero mutation of execution trace data
 * - Respects prefers-reduced-motion
 */

(function () {
    "use strict";

    // 1. State & Cache
    let previousPointerRects = new Map();
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

    // 2. Speed Adjustment Helper
    function getSpeedDuration() {
        if (prefersReducedMotion) return 1; // 1ms for reduced motion

        const speedSelect = document.getElementById("speed-select");
        const speed = parseFloat(speedSelect ? speedSelect.value : "1.0") || 1.0;

        if (speed >= 4.0) return 60;
        if (speed >= 2.0) return 120;
        if (speed <= 0.5) return 360;
        return 220; // 1.0x baseline duration in ms
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
            const seqName = seqBox ? (seqBox.querySelector(".seq-label-name")?.textContent.trim() || "") : "";
            const key = `${seqName}:${name}`;
            previousPointerRects.set(key, el.getBoundingClientRect());
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
            const seqName = seqBox ? (seqBox.querySelector(".seq-label-name")?.textContent.trim() || "") : "";
            const key = `${seqName}:${name}`;

            if (previousPointerRects.has(key)) {
                const oldRect = previousPointerRects.get(key);
                const newRect = el.getBoundingClientRect();
                const deltaX = oldRect.left - newRect.left;

                // Animate horizontal shift if within reasonable boundary
                if (Math.abs(deltaX) > 1 && Math.abs(deltaX) < 800) {
                    el.style.transform = `translateX(${deltaX}px)`;
                    el.style.transition = "none";

                    requestAnimationFrame(function () {
                        el.style.transition = `transform ${duration}ms cubic-bezier(0.2, 0, 0, 1)`;
                        el.style.transform = "translateX(0)";
                    });
                }
            } else {
                // New pointer appearance
                el.classList.add("pointer-enter");
            }
        }
    }

    // 4. Memory Block & Table Transition Enhancements
    function animateMemoryBlocks(step, prevStep) {
        if (isRapidNavigation || prefersReducedMotion) return;

        const stage = document.getElementById("sequences-container");
        if (!stage) return;

        // Apply mutation pulse to changed memory block cells
        const mutatedBlocks = stage.querySelectorAll(".memory-block-cell.cell-mutated");
        for (let i = 0; i < mutatedBlocks.length; i++) {
            mutatedBlocks[i].classList.add("anim-pulse-mutation");
        }
    }

    function animateMemoryTable(step, prevStep) {
        if (isRapidNavigation || prefersReducedMotion) return;

        const tableBody = document.getElementById("memory-table-body");
        if (!tableBody) return;

        // Animate new rows smoothly
        const newBadges = tableBody.querySelectorAll(".status-badge-inline.new");
        for (let i = 0; i < newBadges.length; i++) {
            const row = newBadges[i].closest("tr");
            if (row) {
                row.classList.add("row-enter");
            }
        }
    }

    // 5. Public API Export
    const XRayAnimator = {
        init: function () {
            updateAnimationSpeed();
            const speedSelect = document.getElementById("speed-select");
            if (speedSelect) {
                speedSelect.addEventListener("change", updateAnimationSpeed);
            }
        },

        beforeStepRender: function () {
            capturePointerPositions();
        },

        afterStepRender: function (step, prevStep, isSteppingBackward) {
            animatePointers();
            animateMemoryBlocks(step, prevStep);
            animateMemoryTable(step, prevStep);
        },

        cancelAnimations: function () {
            // Called during rapid scrubbing to prevent animation queues
            isRapidNavigation = true;
            previousPointerRects.clear();
            if (rapidNavTimeout) clearTimeout(rapidNavTimeout);
            rapidNavTimeout = setTimeout(function () {
                isRapidNavigation = false;
            }, 150);
        },

        getDuration: function () {
            return getSpeedDuration();
        }
    };

    window.XRayAnimator = XRayAnimator;

})();
