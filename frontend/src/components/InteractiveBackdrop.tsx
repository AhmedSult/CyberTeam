import { useEffect, useRef } from "react";

function CanvasBackdrop() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const cnv = canvas;
    const c2d = ctx;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    type Particle = { x: number; y: number; vx: number; vy: number; r: number };
    const particles: Particle[] = [];
    const count = 64;
    let w = 0;
    let h = 0;
    let raf = 0;

    function resize() {
      w = window.innerWidth;
      h = window.innerHeight;
      cnv.width = w * dpr;
      cnv.height = h * dpr;
      cnv.style.width = `${w}px`;
      cnv.style.height = `${h}px`;
      c2d.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function seedParticles() {
      particles.length = 0;
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          r: 1 + Math.random() * 2.2,
        });
      }
    }

    const onMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.active = true;
    };
    const onLeave = () => {
      mouseRef.current.active = false;
    };

    function tick() {
      c2d.clearRect(0, 0, w, h);
      const grad = c2d.createRadialGradient(w * 0.3, h * 0.2, 0, w * 0.5, h * 0.5, Math.max(w, h) * 0.9);
      grad.addColorStop(0, "rgba(0, 120, 85, 0.06)");
      grad.addColorStop(0.45, "rgba(12, 100, 95, 0.03)");
      grad.addColorStop(1, "rgba(232, 240, 235, 0.01)");
      c2d.fillStyle = grad;
      c2d.fillRect(0, 0, w, h);

      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;
      const pullRadius = 220;

      for (const p of particles) {
        if (mouseRef.current.active) {
          const dx = mx - p.x;
          const dy = my - p.y;
          const dist = Math.hypot(dx, dy) + 1;
          if (dist < pullRadius) {
            const f = ((pullRadius - dist) / pullRadius) * 0.045;
            p.vx += (dx / dist) * f;
            p.vy += (dy / dist) * f;
          }
        }
        p.vx += (Math.random() - 0.5) * 0.018;
        p.vy += (Math.random() - 0.5) * 0.018;
        p.vx *= 0.988;
        p.vy *= 0.988;
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -0.55;
        if (p.y < 0 || p.y > h) p.vy *= -0.55;
        p.x = Math.max(0, Math.min(w, p.x));
        p.y = Math.max(0, Math.min(h, p.y));
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 95) {
            const alpha = 0.14 * (1 - dist / 95);
            c2d.strokeStyle = `rgba(10, 140, 120, ${alpha})`;
            c2d.lineWidth = 0.55;
            c2d.beginPath();
            c2d.moveTo(a.x, a.y);
            c2d.lineTo(b.x, b.y);
            c2d.stroke();
          }
        }
      }

      for (const p of particles) {
        c2d.beginPath();
        c2d.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        c2d.fillStyle = "rgba(0, 107, 63, 0.28)";
        c2d.fill();
        c2d.beginPath();
        c2d.arc(p.x, p.y, p.r * 0.45, 0, Math.PI * 2);
        c2d.fillStyle = "rgba(180, 255, 220, 0.15)";
        c2d.fill();
      }

      raf = requestAnimationFrame(tick);
    }

    function onResize() {
      resize();
      seedParticles();
    }

    resize();
    seedParticles();
    window.addEventListener("resize", onResize);
    window.addEventListener("mousemove", onMove, { passive: true });
    document.body.addEventListener("mouseleave", onLeave);
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMove);
      document.body.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="interactive-backdrop" aria-hidden />;
}

export function InteractiveBackdrop() {
  const reduced =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) {
    return <div className="interactive-backdrop interactive-backdrop--static" aria-hidden />;
  }
  return <CanvasBackdrop />;
}
