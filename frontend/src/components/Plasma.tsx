import React, { useEffect, useRef } from 'react';
import { Renderer, Program, Mesh, Triangle } from 'ogl';
import './Plasma.css';

interface PlasmaProps {
  color?: string;
  speed?: number;
  direction?: 'forward' | 'reverse' | 'pingpong';
  scale?: number;
  opacity?: number;
  mouseInteractive?: boolean;
  renderScale?: number;
  maxDpr?: number;
  targetFps?: number;
  iterations?: number;
  className?: string;
}

const hexToRgb = (hex: string): [number, number, number] => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [0.05, 0.58, 0.53];
  return [
    parseInt(result[1], 16) / 255,
    parseInt(result[2], 16) / 255,
    parseInt(result[3], 16) / 255
  ];
};

const vertexShader = `#version 300 es
in vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragmentShader = `#version 300 es
precision highp float;
uniform vec2 iResolution;
uniform float iTime;
uniform vec3 uColor;
uniform float uScale;
uniform float uOpacity;
uniform vec2 uMouse;
uniform int uIterations;
out vec4 fragColor;

void main() {
  vec2 uv = (gl_FragCoord.xy * 2.0 - iResolution.xy) / min(iResolution.x, iResolution.y);
  uv *= uScale;

  vec2 m = (uMouse * 2.0 - iResolution.xy) / min(iResolution.x, iResolution.y);
  float distToMouse = length(uv - m);
  float mouseWarp = exp(-distToMouse * 2.5) * 0.4;
  uv += normalize(uv - m + 0.0001) * mouseWarp;

  float t = iTime * 0.5;
  vec3 col = vec3(0.0);

  for (int i = 0; i < 40; i++) {
    if (i >= uIterations) break;
    float fi = float(i);
    vec2 p = uv + vec2(
      sin(t * 0.3 + fi * 0.2 + uv.y * 1.2),
      cos(t * 0.4 + fi * 0.3 + uv.x * 1.1)
    ) * 0.6;
    
    float len = length(p);
    float glow = 0.015 / (len + 0.04);
    
    vec3 tone = vec3(
      sin(fi * 0.4 + t * 0.6) * 0.5 + 0.5,
      sin(fi * 0.4 + t * 0.6 + 2.094) * 0.5 + 0.5,
      sin(fi * 0.4 + t * 0.6 + 4.188) * 0.5 + 0.5
    );

    col += mix(tone, uColor, 0.6) * glow;
  }

  col *= uOpacity;
  fragColor = vec4(col, 1.0);
}
`;

export const Plasma: React.FC<PlasmaProps> = ({
  color = '#0d9488',
  speed = 0.6,
  direction = 'forward',
  scale = 1.1,
  opacity = 0.35,
  mouseInteractive = true,
  renderScale = 0.55,
  maxDpr = 1.5,
  targetFps = 60,
  iterations = 60,
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const renderer = new Renderer({
      alpha: true,
      antialias: false,
      dpr: Math.min(window.devicePixelRatio || 1, maxDpr) * renderScale
    });

    const gl = renderer.gl;
    gl.clearColor(0, 0, 0, 0);

    const canvas = gl.canvas as HTMLCanvasElement;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.display = 'block';
    container.appendChild(canvas);

    const geometry = new Triangle(gl);
    const rgb = hexToRgb(color);

    const program = new Program(gl, {
      vertex: vertexShader,
      fragment: fragmentShader,
      uniforms: {
        iResolution: { value: [container.clientWidth, container.clientHeight] },
        iTime: { value: 0 },
        uColor: { value: rgb },
        uScale: { value: scale },
        uOpacity: { value: opacity },
        uMouse: { value: [container.clientWidth / 2, container.clientHeight / 2] },
        uIterations: { value: Math.min(iterations, 40) }
      },
      transparent: true
    });

    const mesh = new Mesh(gl, { geometry, program });

    let targetMouse = [container.clientWidth / 2, container.clientHeight / 2];
    let currentMouse = [container.clientWidth / 2, container.clientHeight / 2];

    const onPointerMove = (e: PointerEvent) => {
      if (!mouseInteractive) return;
      const rect = container.getBoundingClientRect();
      targetMouse = [e.clientX - rect.left, rect.height - (e.clientY - rect.top)];
    };

    window.addEventListener('pointermove', onPointerMove);

    const handleResize = () => {
      if (!container) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      renderer.setSize(width, height);
      program.uniforms.iResolution.value = [width, height];
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    let animationFrameId: number;
    let lastTime = performance.now();
    let accumulatedTime = 0;
    const frameInterval = 1000 / targetFps;

    const render = (time: number) => {
      animationFrameId = requestAnimationFrame(render);

      const delta = time - lastTime;
      if (delta < frameInterval) return;
      lastTime = time - (delta % frameInterval);

      let dirMultiplier = 1;
      if (direction === 'reverse') dirMultiplier = -1;
      else if (direction === 'pingpong') dirMultiplier = Math.sin(time * 0.001) > 0 ? 1 : -1;

      accumulatedTime += (delta * 0.001) * speed * dirMultiplier;
      program.uniforms.iTime.value = accumulatedTime;

      // Smooth mouse interpolation
      if (mouseInteractive) {
        currentMouse[0] += (targetMouse[0] - currentMouse[0]) * 0.08;
        currentMouse[1] += (targetMouse[1] - currentMouse[1]) * 0.08;
        program.uniforms.uMouse.value = currentMouse;
      }

      program.uniforms.uOpacity.value = opacity;
      program.uniforms.uScale.value = scale;
      program.uniforms.uColor.value = hexToRgb(color);

      renderer.render({ scene: mesh });
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('resize', handleResize);
      if (canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
    };
  }, [color, speed, direction, scale, opacity, mouseInteractive, renderScale, maxDpr, targetFps, iterations]);

  return (
    <div
      ref={containerRef}
      className={`plasma-container ${className}`.trim()}
    />
  );
};

export default Plasma;
