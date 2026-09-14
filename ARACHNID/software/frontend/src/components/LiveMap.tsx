import React, { useRef, useEffect, useState } from 'react';
import { useRover } from '../hooks/useRover';

/**
 * LiveMap — Clean white canvas, gray grid, blue rover, red path.
 * The visual centerpiece of the interface.
 */
export const LiveMap: React.FC = () => {
  const { status, mapData, navigationData, explorationData } = useRover();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [zoom, setZoom] = useState(16);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef({ x: 0, y: 0 });

  const [size, setSize] = useState({ w: 800, h: 520 });

  const [hasAutoFit, setHasAutoFit] = useState(false);

  // Responsive container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      const w = entries[0].contentRect.width;
      setSize({ w, h: Math.max(420, Math.min(580, w * 0.5)) });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // Auto-fit map content
  useEffect(() => {
    if (!mapData || mapData.width === 0 || size.w === 0 || hasAutoFit) return;

    const res = mapData.resolution_m_per_cell || 0.05;
    const minX = mapData.origin.x;
    const maxX = mapData.origin.x + mapData.width * res;
    const minY = mapData.origin.y;
    const maxY = mapData.origin.y + mapData.height * res;
    
    // Include rover (0,0)
    let bMinX = Math.min(minX, 0);
    let bMaxX = Math.max(maxX, 0);
    let bMinY = Math.min(minY, 0);
    let bMaxY = Math.max(maxY, 0);

    if (explorationData?.current_goal) {
       bMinX = Math.min(bMinX, explorationData.current_goal.x);
       bMaxX = Math.max(bMaxX, explorationData.current_goal.x);
       bMinY = Math.min(bMinY, explorationData.current_goal.y);
       bMaxY = Math.max(bMaxY, explorationData.current_goal.y);
    }
    
    const pad = 1.0; 
    bMinX -= pad; bMaxX += pad;
    bMinY -= pad; bMaxY += pad;

    const widthM = bMaxX - bMinX;
    const heightM = bMaxY - bMinY;

    if (widthM > 0 && heightM > 0) {
      const zoomX = size.w / (widthM * 20);
      const zoomY = size.h / (heightM * 20);
      const newZoom = Math.max(4, Math.min(60, Math.min(zoomX, zoomY)));
      setZoom(newZoom);
      
      const newScale = newZoom * 20;
      const cx = (bMinX + bMaxX) / 2;
      const cy = (bMinY + bMaxY) / 2;

      setPan({
        x: size.w / 2 - (cx * newScale),
        y: size.h / 2 - (-cy * newScale)
      });
      setHasAutoFit(true);
    }
  }, [mapData, explorationData, size, hasAutoFit]);

  // Mouse interaction
  const onDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };
  const onMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragRef.current.x, y: e.clientY - dragRef.current.y });
  };
  const onUp = () => setIsDragging(false);

  // Scroll zoom
  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => {
      e.preventDefault();
      setZoom((z) => e.deltaY < 0 ? Math.min(z * 1.2, 60) : Math.max(z / 1.2, 4));
    };
    el.addEventListener('wheel', handler, { passive: false });
    return () => el.removeEventListener('wheel', handler);
  }, []);

  // Draw
  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    const { w, h } = size;
    c.width = w * 2; // 2x for retina
    c.height = h * 2;
    ctx.scale(2, 2);

    // White fill
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);

    ctx.save();
    ctx.translate(pan.x, pan.y);

    // Grid
    const step = zoom * 10;
    ctx.strokeStyle = '#f5f5f5';
    ctx.lineWidth = 0.5;
    const ext = 2000;
    for (let x = -ext; x <= ext; x += step) {
      ctx.beginPath(); ctx.moveTo(x, -ext); ctx.lineTo(x, ext); ctx.stroke();
    }
    for (let y = -ext; y <= ext; y += step) {
      ctx.beginPath(); ctx.moveTo(-ext, y); ctx.lineTo(ext, y); ctx.stroke();
    }

    const scale = zoom * 20; // world-to-pixel

    // Occupancy grid
    if (mapData && mapData.width > 0) {
      const cs = (mapData.resolution_m_per_cell || 0.05) * scale;
      const ox = mapData.origin.x * scale;
      const oy = -mapData.origin.y * scale;

      for (let r = 0; r < mapData.height; r++) {
        for (let c = 0; c < mapData.width; c++) {
          const v = mapData.data[r * mapData.width + c];
          const px = ox + c * cs;
          const py = oy - (r + 1) * cs;

          if (v === -1 || v === undefined) {
            continue; // skip unknown — leave white
          } else if (v === 0) {
            ctx.fillStyle = 'rgba(26,43,95,0.03)';
          } else if (v > 50) {
            ctx.fillStyle = '#e0e0e0';
          } else {
            ctx.fillStyle = '#f0f0f0';
          }
          ctx.fillRect(px, py, cs + 0.5, cs + 0.5);
        }
      }
    }

    // Nav path — red dashed
    if (navigationData?.path && navigationData.path.length > 1) {
      ctx.strokeStyle = '#d62828';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([5, 3]);
      ctx.beginPath();
      navigationData.path.forEach((pt, i) => {
        const px = pt.x * scale;
        const py = -pt.y * scale;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Goal — red crosshair
    if (navigationData?.goal) {
      const gx = navigationData.goal.x * scale;
      const gy = -navigationData.goal.y * scale;
      ctx.strokeStyle = '#d62828';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(gx, gy, 6, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(gx - 9, gy); ctx.lineTo(gx + 9, gy);
      ctx.moveTo(gx, gy - 9); ctx.lineTo(gx, gy + 9);
      ctx.stroke();
    }

    // Frontier goal — red hollow square
    if (explorationData?.current_goal) {
      const fx = explorationData.current_goal.x * scale;
      const fy = -explorationData.current_goal.y * scale;
      ctx.strokeStyle = '#d62828';
      ctx.lineWidth = 1;
      ctx.strokeRect(fx - 4, fy - 4, 8, 8);
    }

    // Rover — blue dot
    const pose = status?.pose;
    const rx = pose ? pose.x * scale : 0;
    const ry = pose ? -pose.y * scale : 0;
    
    ctx.save();
    ctx.translate(rx, ry);
    if (pose) {
      ctx.rotate(-pose.theta);
    }

    ctx.fillStyle = '#1a2b5f';
    ctx.beginPath();
    ctx.arc(0, 0, 5, 0, Math.PI * 2);
    ctx.fill();

    // Heading triangle (red)
    ctx.fillStyle = '#d62828';
    ctx.beginPath();
    ctx.moveTo(0, -9);
    ctx.lineTo(3.5, -2);
    ctx.lineTo(-3.5, -2);
    ctx.closePath();
    ctx.fill();
    
    ctx.restore();

    ctx.restore();
  }, [mapData, navigationData, explorationData, pan, zoom, size, status?.pose]);

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      <div style={{
        position: 'relative', border: '1px solid #eee',
        borderRadius: 4, overflow: 'hidden',
      }}>
        <canvas
          ref={canvasRef}
          style={{
            width: '100%', height: size.h, display: 'block',
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
          onMouseDown={onDown}
          onMouseMove={onMove}
          onMouseUp={onUp}
          onMouseLeave={onUp}
        />

        {/* Zoom buttons */}
        <div style={{
          position: 'absolute', bottom: 10, right: 10,
          display: 'flex', flexDirection: 'column', gap: 2,
        }}>
          {['+', '−'].map((label, i) => (
            <button key={label}
              onClick={() => setZoom((z) => i === 0 ? Math.min(z * 1.3, 60) : Math.max(z / 1.3, 4))}
              style={{
                width: 26, height: 26, borderRadius: 3,
                border: '1px solid #e0e0e0', background: '#fff',
                cursor: 'pointer', fontSize: 13, color: '#757575',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >{label}</button>
          ))}
        </div>

        {/* Legend */}
        <div style={{
          position: 'absolute', bottom: 10, left: 10,
          display: 'flex', gap: 12, fontSize: 9, color: '#bdbdbd',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#1a2b5f' }} />
            Rover
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <span style={{ width: 5, height: 5, borderRadius: 1, background: '#e0e0e0' }} />
            Obstacle
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#d62828' }} />
            Target
          </span>
        </div>
      </div>
    </div>
  );
};
