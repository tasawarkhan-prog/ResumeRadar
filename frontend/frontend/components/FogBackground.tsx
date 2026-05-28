"use client";
import { useEffect, useRef } from "react";

// Each color set is 4 blobs — richer, more layered than before
// Format: { x%, y%, radius, color-rgb, drift-speed-x, drift-speed-y }
const FOG_SETS = [
  // Indigo + Cyan — primary brand feel
  [
    { x: 18, y: 12, r: 420, color: "99,102,241",  vx:  0.012, vy:  0.008 },
    { x: 78, y: 65, r: 370, color: "6,182,212",   vx: -0.010, vy:  0.006 },
    { x: 50, y: 88, r: 290, color: "167,139,250", vx:  0.007, vy: -0.012 },
    { x: 30, y: 50, r: 240, color: "56,189,248",  vx: -0.006, vy:  0.010 },
  ],
  // Violet + Rose — warm purple night
  [
    { x: 82, y: 18, r: 400, color: "139,92,246",  vx: -0.011, vy:  0.009 },
    { x: 20, y: 70, r: 350, color: "236,72,153",  vx:  0.008, vy: -0.007 },
    { x: 60, y: 35, r: 280, color: "168,85,247",  vx: -0.007, vy:  0.011 },
    { x: 42, y: 90, r: 230, color: "244,114,182", vx:  0.010, vy: -0.008 },
  ],
  // Teal + Emerald — cool ocean depth
  [
    { x: 25, y: 25, r: 410, color: "20,184,166",  vx:  0.009, vy:  0.007 },
    { x: 72, y: 72, r: 360, color: "16,185,129",  vx: -0.008, vy: -0.010 },
    { x: 12, y: 80, r: 270, color: "6,182,212",   vx:  0.011, vy:  0.006 },
    { x: 85, y: 30, r: 220, color: "52,211,153",  vx: -0.007, vy:  0.012 },
  ],
  // Indigo + Amber — electric contrast
  [
    { x: 60, y: 20, r: 390, color: "99,102,241",  vx:  0.007, vy:  0.010 },
    { x: 15, y: 60, r: 340, color: "245,158,11",  vx: -0.009, vy: -0.006 },
    { x: 80, y: 80, r: 260, color: "251,191,36",  vx:  0.006, vy:  0.009 },
    { x: 40, y: 42, r: 200, color: "167,139,250", vx: -0.011, vy: -0.008 },
  ],
  // Rose + Sky — dawn gradient
  [
    { x: 35, y: 15, r: 430, color: "244,63,94",   vx:  0.010, vy:  0.007 },
    { x: 75, y: 55, r: 360, color: "56,189,248",  vx: -0.007, vy:  0.010 },
    { x: 55, y: 82, r: 280, color: "251,113,133", vx:  0.008, vy: -0.009 },
    { x: 10, y: 38, r: 220, color: "125,211,252", vx: -0.010, vy:  0.006 },
  ],
  // Purple + Lime — neon night
  [
    { x: 70, y: 10, r: 400, color: "168,85,247",  vx: -0.008, vy:  0.011 },
    { x: 22, y: 68, r: 350, color: "163,230,53",  vx:  0.011, vy: -0.007 },
    { x: 88, y: 75, r: 260, color: "192,132,252", vx: -0.007, vy:  0.008 },
    { x: 48, y: 30, r: 210, color: "132,204,22",  vx:  0.009, vy: -0.011 },
  ],
  // Cyan + Fuchsia — vibrant digital
  [
    { x: 28, y: 22, r: 410, color: "34,211,238",  vx:  0.010, vy:  0.008 },
    { x: 68, y: 78, r: 360, color: "232,121,249", vx: -0.009, vy: -0.010 },
    { x: 90, y: 20, r: 250, color: "6,182,212",   vx:  0.007, vy:  0.012 },
    { x: 15, y: 90, r: 200, color: "240,171,252", vx: -0.011, vy: -0.007 },
  ],
];

type Blob = { x: number; y: number; r: number; color: string; vx: number; vy: number };

export default function FogBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cvs = canvas;
    const c   = ctx;

    // Live blob positions (copies of FOG_SETS with mutable x/y)
    const liveBlobs: Blob[][] = FOG_SETS.map((set) =>
      set.map((b) => ({ ...b }))
    );

    let raf: number;
    let currentSet = 0;
    let nextSet    = 1;
    let progress   = 0;
    const HOLD = 3.2;  // seconds per palette
    const FADE = 1.4;  // cross-fade seconds
    let holdTimer  = 0;
    let lastTime   = performance.now();
    let phase: "hold" | "fade" = "hold";

    function resize() {
      cvs.width  = window.innerWidth;
      cvs.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    function driftBlobs(dt: number) {
      for (const set of liveBlobs) {
        for (const b of set) {
          b.x += b.vx * dt * 60; // 60 = normalize to 60 fps
          b.y += b.vy * dt * 60;
          // Soft bounce at boundaries
          if (b.x < -10 || b.x > 110) b.vx *= -1;
          if (b.y < -10 || b.y > 110) b.vy *= -1;
        }
      }
    }

    function drawSet(setIdx: number, alpha: number) {
      const blobs = liveBlobs[setIdx];
      blobs.forEach((b) => {
        const cx = (b.x / 100) * cvs.width;
        const cy = (b.y / 100) * cvs.height;
        const grad = c.createRadialGradient(cx, cy, 0, cx, cy, b.r);
        // Slightly richer opacity than before (0.17 / 0.09)
        grad.addColorStop(0,    `rgba(${b.color},${(0.17 * alpha).toFixed(3)})`);
        grad.addColorStop(0.35, `rgba(${b.color},${(0.09 * alpha).toFixed(3)})`);
        grad.addColorStop(0.65, `rgba(${b.color},${(0.03 * alpha).toFixed(3)})`);
        grad.addColorStop(1,    `rgba(${b.color},0)`);
        c.fillStyle = grad;
        c.fillRect(0, 0, cvs.width, cvs.height);
      });
    }

    function easeInOut(t: number) {
      return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    }

    function tick(now: number) {
      const dt = Math.min((now - lastTime) / 1000, 0.05); // cap at 50ms to avoid jumps
      lastTime = now;

      driftBlobs(dt);
      c.clearRect(0, 0, cvs.width, cvs.height);

      if (phase === "hold") {
        holdTimer += dt;
        drawSet(currentSet, 1.0);
        if (holdTimer >= HOLD) {
          holdTimer = 0;
          progress  = 0;
          phase     = "fade";
          nextSet   = (currentSet + 1) % liveBlobs.length;
        }
      } else {
        progress += dt / FADE;
        if (progress >= 1) {
          progress   = 1;
          currentSet = nextSet;
          phase      = "hold";
        }
        const t = easeInOut(progress);
        drawSet(currentSet, 1 - t);
        drawSet(nextSet,    t);
      }

      raf = requestAnimationFrame(tick);
    }

    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0 }}
      aria-hidden
    />
  );
}
