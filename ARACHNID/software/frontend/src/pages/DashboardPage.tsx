import React, { useEffect, useRef, useState } from 'react';
import { ShaderBackground } from '../components/ShaderBackground';
import { useRover } from '../hooks/useRover';

export const DashboardPage: React.FC = () => {
  const {
    status,
    mapData,
    explorationData,
    navigationData,
    triggerEmergencyStop,
  } = useRover();

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zoom, setZoom] = useState(1.0);
  const [followRobot, setFollowRobot] = useState(true);

  // Render occupancy grid on HTML5 canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !mapData) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    // Draw meter coordinate grid lines
    ctx.strokeStyle = '#E4E7EC';
    ctx.lineWidth = 1;
    const gridSize = 20 * zoom;

    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const mapCols = mapData.width || 20;
    const mapRows = mapData.height || 20;
    const cellPixelSize = (Math.min(width, height) / mapCols) * zoom;
    const offsetX = width / 2 - (mapCols * cellPixelSize) / 2;
    const offsetY = height / 2 - (mapRows * cellPixelSize) / 2;

    // Render cells
    for (let r = 0; r < mapRows; r++) {
      for (let c = 0; c < mapCols; c++) {
        const idx = r * mapCols + c;
        const val = mapData.data[idx] ?? 0;
        const px = offsetX + c * cellPixelSize;
        const py = offsetY + r * cellPixelSize;

        if (val === 100) {
          // Obstacle
          ctx.fillStyle = '#e2e2e9';
          ctx.fillRect(px, py, cellPixelSize - 0.5, cellPixelSize - 0.5);
        } else if (val === 0) {
          // Free space
          ctx.fillStyle = 'rgba(219, 225, 255, 0.25)';
          ctx.fillRect(px, py, cellPixelSize - 0.5, cellPixelSize - 0.5);
        }
      }
    }

    // Trajectory path
    if (navigationData && navigationData.path && navigationData.path.length > 1) {
      ctx.beginPath();
      ctx.strokeStyle = '#D71920';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);

      navigationData.path.forEach((pt, i) => {
        const ptX = offsetX + (pt.x / 0.05) * (cellPixelSize / mapCols);
        const ptY = offsetY + (pt.y / 0.05) * (cellPixelSize / mapRows);
        if (i === 0) ctx.moveTo(ptX, ptY);
        else ctx.lineTo(ptX, ptY);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Robot Heading / Position Marker
    const pose = status?.pose;
    const originX = mapData?.origin?.x || -10;
    const originY = mapData?.origin?.y || -10;
    const res = mapData?.resolution_m_per_cell || 0.05;
    
    // Default to center if no pose is available
    const rx = pose ? offsetX + ((pose.x - originX) / res) * cellPixelSize : width / 2;
    const ry = pose ? offsetY + ((pose.y - originY) / res) * cellPixelSize : height / 2;

    ctx.save();
    ctx.translate(rx, ry);
    
    // Rotate based on heading (theta)
    if (pose) {
      // In canvas, y grows downwards. If theta is counter-clockwise, we might need -theta.
      // Assuming standard mathematical theta (0 is right, pi/2 is up)
      // Actually the standard canvas rotation is clockwise.
      ctx.rotate(-pose.theta);
    }

    // Robot chassis hexagon
    ctx.fillStyle = '#0b1f4d';
    ctx.beginPath();
    ctx.arc(0, 0, 9 * zoom, 0, Math.PI * 2);
    ctx.fill();

    // Red direction heading triangle
    ctx.fillStyle = '#D71920';
    ctx.beginPath();
    ctx.moveTo(0, -12 * zoom);
    ctx.lineTo(5 * zoom, -4 * zoom);
    ctx.lineTo(-5 * zoom, -4 * zoom);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }, [mapData, navigationData, zoom, followRobot, status?.pose]);

  const batteryPct = status?.battery_percent >= 0 ? Math.round(status.battery_percent) : '--';
  const exploredPct = explorationData?.explored_percent !== undefined ? Math.round(explorationData.explored_percent) : '--';
  const frontierCount = explorationData?.frontier_count ?? '--';
  const currentTarget = explorationData?.current_goal
    ? `X: ${explorationData.current_goal.x.toFixed(2)}, Y: ${explorationData.current_goal.y.toFixed(2)}`
    : '--';

  const posX = status?.pose?.x !== undefined ? status.pose.x.toFixed(2) : '--';
  const posY = status?.pose?.y !== undefined ? status.pose.y.toFixed(2) : '--';
  const headingDeg = status?.pose?.theta !== undefined ? Math.round(status.pose.theta * (180 / Math.PI)) : '--';
  const velocityMps = '--'; // True velocity isn't tracked in status currently, default to -- instead of fake

  return (
    <div className="flex flex-col gap-6">
      {/* Stitch Hero Banner */}
      <div className="relative w-full overflow-hidden p-6 border border-[#c5c6d0] bg-[#ffffff] rounded-lg shadow-sm">
        <ShaderBackground className="absolute inset-0 w-full h-full pointer-events-none" opacity={0.35} />

        {/* 45 degree decorative corner markers */}
        <div className="absolute top-0 right-0 w-16 h-16 border-t border-r border-[#c5c6d0] opacity-30 transform rotate-45 translate-x-4 -translate-y-4" />
        <div className="absolute bottom-0 left-0 w-16 h-16 border-b border-l border-[#c5c6d0] opacity-30 transform rotate-45 -translate-x-4 translate-y-4" />

        <div className="relative z-10 flex flex-col gap-1 mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 bg-[#D71920] rounded-full animate-pulse-red" />
            <span className="font-label-caps text-[#D71920] tracking-widest uppercase text-[11px]">
              Mission Active
            </span>
          </div>
          <h1 className="font-display-lg text-3xl md:text-5xl text-[#000928] tracking-tight uppercase leading-none font-bold">
            Autonomous<br />Exploration
          </h1>
        </div>

        <div className="relative z-10 flex flex-col gap-3">
          <div className="flex justify-between items-end border-b border-[#c5c6d0] pb-2">
            <span className="font-label-caps text-[#45464f] text-xs">Progress</span>
            <span className="font-data-mono-lg text-lg text-[#000928] font-bold">
              {exploredPct}% <span className="text-xs font-normal text-[#45464f]">EXPLORED</span>
            </span>
          </div>

          <div className="flex justify-between items-end border-b border-[#c5c6d0] pb-2">
            <span className="font-label-caps text-[#45464f] text-xs">Targets</span>
            <span className="font-data-mono-lg text-lg text-[#000928] font-bold">
              {frontierCount} <span className="text-xs font-normal text-[#45464f]">FRONTIERS</span>
            </span>
          </div>

          <div className="flex justify-between items-center bg-[#BA1A1A]/5 border border-[#BA1A1A]/20 p-3 rounded">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#D71920] text-[18px]">my_location</span>
              <span className="font-label-caps text-[#D71920] text-xs">Current Target</span>
            </div>
            <span className="font-data-mono-lg text-sm text-[#D71920] font-bold">{currentTarget}</span>
          </div>
        </div>
      </div>

      {/* Stitch Occupancy Grid Card */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="font-label-caps text-[#45464f] text-xs">Occupancy Grid</h2>
          <span className="font-data-mono-sm text-[#757680] text-xs">SYS-MAP-01</span>
        </div>

        <div className="relative w-full h-[420px] border border-[#c5c6d0] bg-[#ffffff] rounded-lg overflow-hidden shadow-sm">
          <canvas ref={canvasRef} width={800} height={420} className="w-full h-full block" />

          {/* Map Controls */}
          <div className="absolute bottom-3 right-3 flex flex-col gap-1 z-30">
            <button
              onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
              className="w-9 h-9 bg-[#ffffff] border border-[#c5c6d0] rounded flex items-center justify-center text-[#1a1b21] hover:text-[#000928] hover:border-[#000928] shadow-sm transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))}
              className="w-9 h-9 bg-[#ffffff] border border-[#c5c6d0] rounded flex items-center justify-center text-[#1a1b21] hover:text-[#000928] hover:border-[#000928] shadow-sm transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">remove</span>
            </button>
          </div>

          <div className="absolute top-3 left-3 flex gap-2 z-30">
            <button
              onClick={() => setZoom(1.0)}
              className="px-2.5 py-1 bg-[#ffffff] border border-[#c5c6d0] rounded font-label-caps text-[10px] text-[#1a1b21] hover:border-[#000928] shadow-sm transition-colors"
            >
              CENTER
            </button>
            <button
              onClick={() => setFollowRobot(!followRobot)}
              className={`px-2.5 py-1 rounded font-label-caps text-[10px] border shadow-sm transition-colors ${
                followRobot
                  ? 'bg-[#000928]/5 border-[#000928] text-[#000928] font-bold'
                  : 'bg-[#ffffff] border-[#c5c6d0] text-[#757680]'
              }`}
            >
              FOLLOW
            </button>
          </div>
        </div>
      </div>

      {/* Stitch Telemetry Grid Card */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="font-label-caps text-[#45464f] text-xs">Telemetry</h2>
          <span className="font-data-mono-sm text-[#757680] text-xs">SYS-TLM-01</span>
        </div>

        <div className="border border-[#c5c6d0] bg-[#ffffff] rounded-lg p-3.5 flex items-center justify-between shadow-sm">
          <span className="font-label-caps text-[#45464f] text-xs w-24">BATTERY</span>
          <div className="flex-1 mx-3 h-1.5 bg-[#ededf5] rounded-full overflow-hidden">
            <div
              className={`h-full ${typeof batteryPct === 'number' && batteryPct < 20 ? 'bg-[#D71920]' : 'bg-[#10B981]'}`}
              style={{ width: `${typeof batteryPct === 'number' ? batteryPct : 0}%` }}
            />
          </div>
          <span className="font-data-mono-sm text-[#000928] font-bold text-xs">{batteryPct}{typeof batteryPct === 'number' ? '%' : ''}</span>
        </div>

        <div className="border border-[#c5c6d0] bg-[#ffffff] rounded-lg p-3.5 flex items-center justify-between shadow-sm">
          <span className="font-label-caps text-[#45464f] text-xs w-24">POSITION</span>
          <span className="font-data-mono-sm text-[#000928] font-bold text-xs">
            X {posX}, Y {posY}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="border border-[#c5c6d0] bg-[#ffffff] rounded-lg p-3.5 flex flex-col shadow-sm">
            <span className="font-label-caps text-[#45464f] text-[10px] mb-1">HEADING</span>
            <span className="font-data-mono-lg text-lg text-[#000928] font-bold">{headingDeg}°</span>
          </div>

          <div className="border border-[#c5c6d0] bg-[#ffffff] rounded-lg p-3.5 flex flex-col shadow-sm">
            <span className="font-label-caps text-[#45464f] text-[10px] mb-1">VELOCITY</span>
            <span className="font-data-mono-lg text-lg text-[#000928] font-bold">{velocityMps}</span>
          </div>
        </div>
      </div>

      {/* Stitch Emergency Stop Button */}
      <div className="mt-2 mb-6">
        <button
          onClick={triggerEmergencyStop}
          className="w-full h-16 bg-[#D71920] border-2 border-[#D71920] hover:bg-[#B91C1C] transition-all rounded shadow-md flex items-center justify-center gap-3 active:scale-[0.98] text-white"
        >
          <span className="material-symbols-outlined text-[24px]">warning</span>
          <span className="font-headline-sm text-base uppercase tracking-wider font-bold">
            Emergency Stop
          </span>
        </button>
      </div>
    </div>
  );
};
