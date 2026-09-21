import React, { useEffect, useRef } from 'react';

interface BioNeuralBackgroundProps {
  className?: string;
  nodeCount?: number;
  interactive?: boolean;
  opacity?: number;
}

export const BioNeuralBackground: React.FC<BioNeuralBackgroundProps> = ({
  className = '',
  nodeCount = 75,
  interactive = true,
  opacity = 0.45
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const mouse = { x: width / 2, y: height / 2, active: false, radius: 200 };

    const handlePointerMove = (e: PointerEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      mouse.active = true;
    };

    const handlePointerLeave = () => {
      mouse.active = false;
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerleave', handlePointerLeave);
    window.addEventListener('resize', handleResize);

    const count = Math.min(Math.floor((width * height) / 16000), nodeCount);
    const palette = ['#0d9488', '#06b6d4', '#6366f1', '#38bdf8', '#10b981', '#a855f7'];

    const nodes = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.55,
      vy: (Math.random() - 0.5) * 0.55,
      radius: Math.random() * 2.5 + 1.2,
      baseRadius: Math.random() * 2.5 + 1.2,
      pulseSpeed: Math.random() * 0.03 + 0.015,
      color: palette[Math.floor(Math.random() * palette.length)],
      phase: Math.random() * Math.PI * 2
    }));

    let animationFrameId: number;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Subtle ambient radial background glow
      const bgGrad = ctx.createRadialGradient(width * 0.5, height * 0.4, 80, width * 0.5, height * 0.5, width * 0.8);
      bgGrad.addColorStop(0, 'rgba(13, 148, 136, 0.07)');
      bgGrad.addColorStop(0.5, 'rgba(2, 132, 199, 0.04)');
      bgGrad.addColorStop(1, 'rgba(240, 253, 250, 0.0)');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // Draw & Connect Nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.phase += n.pulseSpeed;
        n.radius = n.baseRadius + Math.sin(n.phase) * 0.8;
        n.x += n.vx;
        n.y += n.vy;

        if (n.x < 0 || n.x > width) n.vx *= -1;
        if (n.y < 0 || n.y > height) n.vy *= -1;

        if (interactive && mouse.active) {
          const dx = mouse.x - n.x;
          const dy = mouse.y - n.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const force = (1 - dist / mouse.radius) * 0.8;
            n.x -= (dx / dist) * force * 2.2;
            n.y -= (dy / dist) * force * 2.2;
            n.radius = n.baseRadius + force * 2.5;
          }
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;

        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const dx = n.x - n2.x;
          const dy = n.y - n2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 150) {
            const alpha = (1 - dist / 150) * 0.3;
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = `rgba(13, 148, 136, ${alpha})`;
            ctx.lineWidth = 0.9;
            ctx.stroke();
          }
        }

        if (interactive && mouse.active) {
          const dx = n.x - mouse.x;
          const dy = n.y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 170) {
            const alpha = (1 - dist / 170) * 0.55;
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.strokeStyle = `rgba(6, 182, 212, ${alpha})`;
            ctx.lineWidth = 1.2;
            ctx.stroke();
          }
        }
      }

      if (interactive && mouse.active) {
        const curGrad = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 75);
        curGrad.addColorStop(0, 'rgba(6, 182, 212, 0.22)');
        curGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
        ctx.fillStyle = curGrad;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 75, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerleave', handlePointerLeave);
      window.removeEventListener('resize', handleResize);
    };
  }, [nodeCount, interactive]);

  return (
    <div
      className={`fixed inset-0 pointer-events-none z-0 overflow-hidden ${className}`}
      style={{ opacity }}
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
};

export default BioNeuralBackground;
