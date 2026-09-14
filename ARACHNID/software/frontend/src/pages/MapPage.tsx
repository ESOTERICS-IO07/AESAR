import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useRover } from '../hooks/useRover';

export const MapPage: React.FC = () => {
  const { mapData, navigationData, explorationData } = useRover();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [zoom, setZoom] = useState<number>(18);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 300, y: 260 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const handleResetView = useCallback(() => {
    setZoom(18);
    setPan({ x: 300, y: 260 });
  }, []);

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.25, 60));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.25, 6));

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width;
    canvas.height = height;

    // Clear background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    ctx.save();
    ctx.translate(pan.x, pan.y);

    // 1. Draw Grid Coordinate Reference Lines (1 meter spacing)
    const meterPx = zoom * 10;
    ctx.strokeStyle = '#E4E7EC';
    ctx.lineWidth = 1;

    const gridExtent = 1000;
    for (let x = -gridExtent; x <= gridExtent; x += meterPx) {
      ctx.beginPath();
      ctx.moveTo(x, -gridExtent);
      ctx.lineTo(x, gridExtent);
      ctx.stroke();
    }
    for (let y = -gridExtent; y <= gridExtent; y += meterPx) {
      ctx.beginPath();
      ctx.moveTo(-gridExtent, y);
      ctx.lineTo(gridExtent, y);
      ctx.stroke();
    }

    // 2. Draw Occupancy Grid Cells
    if (mapData && mapData.width > 0 && mapData.height > 0) {
      const cellSize = (mapData.resolution_m_per_cell || 0.05) * zoom * 20;
      const originX = mapData.origin.x * zoom * 20;
      const originY = -mapData.origin.y * zoom * 20;

      const mapWidth = mapData.width;
      const mapHeight = mapData.height;

      for (let r = 0; r < mapHeight; r++) {
        for (let c = 0; c < mapWidth; c++) {
          const idx = r * mapWidth + c;
          const val = mapData.data[idx];
          const px = originX + c * cellSize;
          const py = originY - (r + 1) * cellSize;

          if (val === -1 || val === undefined) {
            ctx.fillStyle = '#f3f3fa'; // Unknown
          } else if (val === 0) {
            ctx.fillStyle = 'rgba(219, 225, 255, 0.3)'; // Free Space
          } else if (val > 50) {
            ctx.fillStyle = '#e2e2e9'; // Obstacle
          } else {
            ctx.fillStyle = '#ededf5';
          }

          ctx.fillRect(px, py, cellSize + 0.5, cellSize + 0.5);
        }
      }
    }

    // 3. Draw Navigation Path
    if (navigationData && navigationData.path && navigationData.path.length > 1) {
      ctx.strokeStyle = '#D71920';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();

      navigationData.path.forEach((pt, idx) => {
        const px = pt.x * zoom * 20;
        const py = -pt.y * zoom * 20;
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 4. Draw Active Goal Crosshair
    if (navigationData && navigationData.goal) {
      const gx = navigationData.goal.x * zoom * 20;
      const gy = -navigationData.goal.y * zoom * 20;

      ctx.strokeStyle = '#10B981';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(gx, gy, 8, 0, Math.PI * 2);
      ctx.stroke();
    }

    // 5. Draw Robot Marker
    ctx.fillStyle = '#0b1f4d';
    ctx.beginPath();
    ctx.arc(0, 0, 8, 0, Math.PI * 2);
    ctx.fill();

    // Direction arrow pointing forward
    ctx.fillStyle = '#D71920';
    ctx.beginPath();
    ctx.moveTo(0, -14);
    ctx.lineTo(5, -2);
    ctx.lineTo(-5, -2);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }, [mapData, navigationData, explorationData, pan, zoom]);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-headline-md text-2xl text-[#1a1b21] font-bold">Occupancy Grid Map</h1>
          <span className="font-data-mono-sm text-xs text-[#757680]">
            Resolution: {mapData ? `${mapData.resolution_m_per_cell} m/cell` : '0.05 m/cell'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomIn}
            className="w-9 h-9 bg-[#ffffff] border border-[#e2e2e9] rounded flex items-center justify-center text-[#1a1b21] hover:border-[#000928] shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
          </button>
          <button
            onClick={handleZoomOut}
            className="w-9 h-9 bg-[#ffffff] border border-[#e2e2e9] rounded flex items-center justify-center text-[#1a1b21] hover:border-[#000928] shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">remove</span>
          </button>
          <button
            onClick={handleResetView}
            className="px-3 py-2 bg-[#ffffff] border border-[#e2e2e9] rounded font-label-caps text-xs text-[#1a1b21] hover:border-[#000928] shadow-sm transition-colors"
          >
            RESET VIEW
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Canvas Viewport */}
        <div className="lg:col-span-3 bg-[#ffffff] border border-[#e2e2e9] rounded-xl overflow-hidden shadow-sm h-[520px] relative">
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="w-full h-full block cursor-grab active:cursor-grabbing"
          />

          {/* Floating Map Legend */}
          <div className="absolute bottom-3 left-3 bg-[#ffffff]/90 backdrop-blur-md border border-[#e2e2e9] rounded px-3 py-1.5 flex gap-4 text-xs font-mono shadow-sm">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0b1f4d]" />
              <span className="text-[#45464f]">ROVER</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#e2e2e9]" />
              <span className="text-[#45464f]">OBSTACLE</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
              <span className="text-[#45464f]">GOAL</span>
            </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="flex flex-col gap-4">
          <div className="bg-[#ffffff] rounded-xl p-4 border border-[#e2e2e9] shadow-sm flex flex-col gap-3 font-mono text-xs">
            <h2 className="font-label-caps text-xs text-[#1a1b21] font-bold border-b border-[#e2e2e9] pb-2">
              GRID PROPERTIES
            </h2>
            <div className="flex justify-between">
              <span className="text-[#757680]">DIMENSIONS:</span>
              <span className="font-bold text-[#000928]">
                {mapData ? `${mapData.width} × ${mapData.height}` : '20 × 20'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#757680]">RESOLUTION:</span>
              <span className="font-bold text-[#000928]">
                {mapData ? `${mapData.resolution_m_per_cell} m` : '0.05 m'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#757680]">ORIGIN X:</span>
              <span className="font-bold text-[#000928]">{mapData?.origin.x.toFixed(2) || '0.00'} m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#757680]">ORIGIN Y:</span>
              <span className="font-bold text-[#000928]">{mapData?.origin.y.toFixed(2) || '0.00'} m</span>
            </div>
          </div>

          <div className="bg-[#ffffff] rounded-xl p-4 border border-[#e2e2e9] shadow-sm flex flex-col gap-3 font-mono text-xs">
            <h2 className="font-label-caps text-xs text-[#1a1b21] font-bold border-b border-[#e2e2e9] pb-2">
              MISSION TARGETS
            </h2>
            <div className="flex justify-between">
              <span className="text-[#757680]">NAV STATUS:</span>
              <span className="font-bold text-[#395aac]">
                {navigationData ? navigationData.status : 'IDLE'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#757680]">WAYPOINTS:</span>
              <span className="font-bold text-[#000928]">
                {navigationData ? navigationData.path.length : 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#757680]">FRONTIERS:</span>
              <span className="font-bold text-[#000928]">
                {explorationData ? explorationData.frontier_count : 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
