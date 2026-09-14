import React, { useEffect, useRef } from 'react';

interface ShaderBackgroundProps {
  className?: string;
  opacity?: number;
}

export const ShaderBackground: React.FC<ShaderBackgroundProps> = ({
  className = 'absolute inset-0 w-full h-full pointer-events-none',
  opacity = 0.35,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')) as WebGLRenderingContext | null;
    if (!gl) return;

    let animFrameId: number;

    const vs = `
      attribute vec2 a_position;
      varying vec2 v_texCoord;
      void main() {
        v_texCoord = a_position * 0.5 + 0.5;
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    const fs = `
      precision highp float;
      varying vec2 v_texCoord;
      uniform float u_time;
      uniform vec2 u_resolution;

      void main() {
        vec2 uv = v_texCoord;
        float noise = sin(uv.x * 3.0 + u_time * 0.5) * 0.5 + 0.5;
        noise *= cos(uv.y * 2.0 - u_time * 0.3) * 0.5 + 0.5;

        vec3 white = vec3(1.0, 1.0, 1.0);
        vec3 spiderRed = vec3(0.843, 0.098, 0.125); // #D71920
        vec3 deepBlue = vec3(0.043, 0.122, 0.302);  // #0B1F4D

        float redMask = smoothstep(0.7, 1.1, uv.x + uv.y * 0.5);
        float blueMask = smoothstep(0.4, 0.9, uv.x + uv.y * 0.3) * (1.0 - redMask);

        vec3 color = white;
        color = mix(color, deepBlue, blueMask * 0.18);
        color = mix(color, spiderRed, redMask * 0.15);
        color += noise * 0.02;

        gl_FragColor = vec4(color, 1.0);
      }
    `;

    function createShader(glCtx: WebGLRenderingContext, type: number, src: string) {
      const shader = glCtx.createShader(type);
      if (!shader) return null;
      glCtx.shaderSource(shader, src);
      glCtx.compileShader(shader);
      return shader;
    }

    const vShader = createShader(gl, gl.VERTEX_SHADER, vs);
    const fShader = createShader(gl, gl.FRAGMENT_SHADER, fs);
    if (!vShader || !fShader) return;

    const prog = gl.createProgram();
    if (!prog) return;
    gl.attachShader(prog, vShader);
    gl.attachShader(prog, fShader);
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
      gl.STATIC_DRAW
    );

    const pos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, 'u_time');
    const uRes = gl.getUniformLocation(prog, 'u_resolution');

    const syncSize = () => {
      if (!canvas) return;
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 400;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    syncSize();

    const render = (t: number) => {
      syncSize();
      if (uTime) gl.uniform1f(uTime, t * 0.0008);
      if (uRes) gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animFrameId = requestAnimationFrame(render);
    };

    animFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animFrameId);
    };
  }, []);

  return (
    <div className={className} style={{ opacity, mixBlendMode: 'multiply' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
    </div>
  );
};
