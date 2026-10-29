/**
 * X-Ray Execution Agent: Diwali Celebration Completion Spark Canvas
 * File: static/js/spark.js
 *
 * Implements a high-performance, non-intrusive geometric spark animation
 * celebrating successful algorithm execution completion (Diwali theme).
 *
 * Design constraints:
 * - Zero external dependencies (Vanilla Canvas 2D)
 * - Zero pointer interception (pointer-events: none)
 * - Festive palette: Warm Gold, Saffron Orange, Festive Green, Diamond White
 * - Auto-terminating animation loop (clears after ~2.5s, no CPU leaks)
 */

(function () {
    "use strict";

    let canvas = null;
    let ctx = null;
    let animId = null;
    let particles = [];
    let isRunning = false;
    let bannerEl = null;

    const FESTIVE_COLORS = [
        "#f59e0b", // Warm Gold
        "#fbbf24", // Luminous Gold
        "#d29922", // Active Amber
        "#ea580c", // Saffron
        "#f97316", // Festive Orange
        "#10b981", // Emerald
        "#3fb950", // Mutation Green
        "#ffffff", // Diamond Spark
        "#fef08a"  // Warm White
    ];

    function initCanvas() {
        canvas = document.getElementById("diwali-canvas");
        if (!canvas) {
            canvas = document.createElement("canvas");
            canvas.id = "diwali-canvas";
            canvas.className = "diwali-canvas";
            document.body.appendChild(canvas);
        }
        ctx = canvas.getContext("2d");
        resizeCanvas();
        window.addEventListener("resize", resizeCanvas);
    }

    function resizeCanvas() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createBurst(originX, originY, count, speedMultiplier) {
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = (Math.random() * 4 + 1.5) * (speedMultiplier || 1);
            const color = FESTIVE_COLORS[Math.floor(Math.random() * FESTIVE_COLORS.length)];
            const size = Math.random() * 2.5 + 1.5;
            const life = Math.random() * 40 + 70; // 70-110 frames (~1.5 to 2.2s)

            particles.push({
                x: originX,
                y: originY,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                color: color,
                size: size,
                alpha: 1.0,
                maxLife: life,
                life: life,
                twinkle: Math.random() * 10,
                decay: 1.0 / life
            });
        }
    }

    function triggerDiwaliSpark() {
        // Respect prefers-reduced-motion
        if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            return;
        }

        if (!canvas || !ctx) {
            initCanvas();
        }
        if (!canvas || !ctx) return;

        stopDiwaliSpark();
        resizeCanvas();

        const w = canvas.width;
        const h = canvas.height;

        particles = [];

        // Launch 3 festive burst centers (left-fountain, center-firework, right-fountain)
        createBurst(w * 0.25, h * 0.45, 45, 1.2);
        createBurst(w * 0.50, h * 0.35, 60, 1.4);
        createBurst(w * 0.75, h * 0.45, 45, 1.2);

        // Show subtle celebration banner
        showCelebrationBanner();

        isRunning = true;
        render();
    }

    function showCelebrationBanner() {
        if (!bannerEl) {
            bannerEl = document.getElementById("diwali-banner");
            if (!bannerEl) {
                bannerEl = document.createElement("div");
                bannerEl.id = "diwali-banner";
                bannerEl.className = "diwali-banner";
                bannerEl.setAttribute("aria-live", "polite");
                document.body.appendChild(bannerEl);
            }
        }
        bannerEl.textContent = "EXECUTION COMPLETE // DIWALI FESTIVAL OF LIGHTS";
        bannerEl.classList.add("diwali-banner-visible");

        setTimeout(function () {
            if (bannerEl) {
                bannerEl.classList.remove("diwali-banner-visible");
            }
        }, 2600);
    }

    function render() {
        if (!isRunning || !ctx || !canvas) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const aliveParticles = [];

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.life--;
            p.alpha -= p.decay;

            if (p.life > 0 && p.alpha > 0.01) {
                // Physics
                p.vx *= 0.982; // Air resistance
                p.vy *= 0.982;
                p.vy += 0.075; // Subtle gravity
                p.x += p.vx;
                p.y += p.vy;

                // Sparkle luminance
                const twinkleAlpha = Math.max(0, Math.min(1, p.alpha * (0.6 + 0.4 * Math.sin(p.life * 0.4 + p.twinkle))));

                ctx.save();
                ctx.globalAlpha = twinkleAlpha;
                ctx.fillStyle = p.color;

                // Geometric spark star or diamond cell
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();

                // Spark cross glint
                if (p.size > 2.2 && p.alpha > 0.4) {
                    ctx.strokeStyle = p.color;
                    ctx.lineWidth = 0.75;
                    ctx.beginPath();
                    ctx.moveTo(p.x - p.size * 1.8, p.y);
                    ctx.lineTo(p.x + p.size * 1.8, p.y);
                    ctx.moveTo(p.x, p.y - p.size * 1.8);
                    ctx.lineTo(p.x, p.y + p.size * 1.8);
                    ctx.stroke();
                }

                ctx.restore();
                aliveParticles.push(p);
            }
        }

        particles = aliveParticles;

        if (particles.length > 0) {
            animId = requestAnimationFrame(render);
        } else {
            stopDiwaliSpark();
        }
    }

    function stopDiwaliSpark() {
        isRunning = false;
        if (animId) {
            cancelAnimationFrame(animId);
            animId = null;
        }
        if (ctx && canvas) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        if (bannerEl) {
            bannerEl.classList.remove("diwali-banner-visible");
        }
        particles = [];
    }

    // Expose global controller
    window.triggerDiwaliSpark = triggerDiwaliSpark;
    window.stopDiwaliSpark = stopDiwaliSpark;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initCanvas);
    } else {
        initCanvas();
    }
})();
