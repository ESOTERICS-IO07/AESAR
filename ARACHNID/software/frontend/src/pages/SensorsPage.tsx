import React from 'react';
import { useRover } from '../hooks/useRover';

export const SensorsPage: React.FC = () => {
  const { telemetry, status, setMode, sendCommand, stopRover } = useRover();

  const isAutonomous = status?.mode === 'AUTONOMOUS';

  const usFlM = (telemetry?.us_fl_mm != null && telemetry.us_fl_mm > 0) ? (telemetry.us_fl_mm / 1000).toFixed(2) + 'm' : '--';
  const usFcM = (telemetry?.us_fc_mm != null && telemetry.us_fc_mm > 0) ? (telemetry.us_fc_mm / 1000).toFixed(2) + 'm' : '--';
  const usFrM = (telemetry?.us_fr_mm != null && telemetry.us_fr_mm > 0) ? (telemetry.us_fr_mm / 1000).toFixed(2) + 'm' : '--';
  const tofM = (telemetry?.tof_distance_mm != null && telemetry.tof_distance_mm > 0) ? (telemetry.tof_distance_mm / 1000).toFixed(2) + 'm' : '--';
  const tofAngle = (telemetry?.tof_angle_deg != null && telemetry?.tof_distance_mm != null && telemetry.tof_distance_mm > 0) ? telemetry.tof_angle_deg.toFixed(0) + '°' : '';
  const usLmM = (telemetry?.us_l_mm != null && telemetry.us_l_mm > 0) ? (telemetry.us_l_mm / 1000).toFixed(2) + 'm' : '--';
  const usRmM = (telemetry?.us_r_mm != null && telemetry.us_r_mm > 0) ? (telemetry.us_r_mm / 1000).toFixed(2) + 'm' : '--';

  const isLeftWarn = (telemetry?.us_l_mm != null && telemetry.us_l_mm > 0 && telemetry.us_l_mm < 1000);
  const isRightWarn = (telemetry?.us_r_mm != null && telemetry.us_r_mm > 0 && telemetry.us_r_mm < 1000);

  const handleDrive = (linear: number, angular: number) => {
    sendCommand(linear, angular);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="font-headline-md text-2xl text-[#1a1b21] font-bold">Diagnostics</h1>
        <span className="font-label-caps text-xs text-[#45464f] bg-[#e8e7ef] px-2.5 py-1 rounded">
          V 2.1.4
        </span>
      </div>

      {/* Spatial Array Card */}
      <div className="bg-[#ffffff] rounded-xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.03)] border border-[#e2e2e9] relative overflow-hidden">
        {/* Radial Web Pattern SVG */}
        <svg
          className="absolute inset-0 w-full h-full opacity-15 pointer-events-none"
          preserveAspectRatio="none"
          viewBox="0 0 100 100"
        >
          <g fill="none" stroke="#395aac" strokeWidth="0.5">
            <circle cx="50" cy="50" r="12" />
            <circle cx="50" cy="50" r="26" />
            <circle cx="50" cy="50" r="40" />
            <path d="M50 10 L50 90 M10 50 L90 50 M22 22 L78 78 M22 78 L78 22" />
          </g>
        </svg>

        <div className="flex justify-between items-center mb-4 relative z-10">
          <h2 className="font-headline-sm text-base text-[#1a1b21] font-semibold">Spatial Array</h2>
          <span className="font-data-mono-sm text-xs text-[#395aac] font-bold">ARR-01</span>
        </div>

        {/* 2D Rover Chassis & Rays */}
        <div className="relative h-72 w-full flex flex-col items-center justify-center pt-2">
          
          <div className="w-full max-w-[280px] relative z-20">
            {/* Front Row (Ultrasonics) */}
            <div className="flex justify-between w-full mb-6 px-2">
              <div className="flex flex-col items-center">
                <span className="font-label-caps text-[10px] text-[#45464f]">Front Left</span>
                <span className="font-data-mono-sm text-xs text-[#1a1b21] font-bold">{usFlM}</span>
                <div className="w-2 h-2 rounded-full bg-[#89a8ff] mt-1" />
              </div>
              
              <div className="flex flex-col items-center">
                <span className="font-label-caps text-[10px] text-[#45464f]">Front Center</span>
                <span className="font-data-mono-sm text-xs text-[#1a1b21] font-bold">{usFcM}</span>
                <div className="w-2 h-2 rounded-full bg-[#89a8ff] mt-1" />
              </div>

              <div className="flex flex-col items-center">
                <span className="font-label-caps text-[10px] text-[#45464f]">Front Right</span>
                <span className="font-data-mono-sm text-xs text-[#1a1b21] font-bold">{usFrM}</span>
                <div className="w-2 h-2 rounded-full bg-[#89a8ff] mt-1" />
              </div>
            </div>

            {/* Middle Row (Ultrasonics) */}
            <div className="flex justify-between w-full px-4 mb-2">
              <div className="flex flex-col items-center">
                <span className="font-label-caps text-[10px] text-[#45464f]">Left Middle</span>
                <span className={`font-data-mono-sm text-xs font-bold ${isLeftWarn ? 'text-[#d97706]' : 'text-[#1a1b21]'}`}>{usLmM}</span>
                <div className={`w-2 h-2 rounded-full mt-1 ${isLeftWarn ? 'bg-[#d97706]' : 'bg-[#89a8ff]'}`} />
              </div>

              <div className="flex flex-col items-center">
                <span className="font-label-caps text-[10px] text-[#45464f]">Right Middle</span>
                <span className={`font-data-mono-sm text-xs font-bold ${isRightWarn ? 'text-[#d97706]' : 'text-[#1a1b21]'}`}>{usRmM}</span>
                <div className={`w-2 h-2 rounded-full mt-1 ${isRightWarn ? 'bg-[#d97706]' : 'bg-[#89a8ff]'}`} />
              </div>
            </div>
          </div>

          {/* Rover Diagram with Elevated TOF */}
          <div className="relative w-24 h-32 border-2 border-[#000928] rounded-lg flex flex-col items-center justify-center z-10 bg-[#ffffff] shadow-sm mt-1">
            {/* Wheels */}
            <div className="absolute -top-1 left-2 w-4 h-2 bg-[#000928] rounded-t-sm" />
            <div className="absolute -top-1 right-2 w-4 h-2 bg-[#000928] rounded-t-sm" />
            <div className="absolute -bottom-1 left-2 w-4 h-2 bg-[#000928] rounded-b-sm" />
            <div className="absolute -bottom-1 right-2 w-4 h-2 bg-[#000928] rounded-b-sm" />
            
            {/* TOF Elevated Center */}
            <div className="absolute -top-6 flex flex-col items-center drop-shadow-md z-30">
              <div className="w-0 h-0 border-l-[6px] border-r-[6px] border-b-[8px] border-transparent border-b-[#D71920]" />
              <div className="bg-[#D71920] text-white px-2 py-0.5 rounded shadow-lg flex flex-col items-center mt-1 border border-[#93000a]">
                <span className="font-label-caps text-[8px] font-bold tracking-wider">TOF (ELEVATED)</span>
                <span className="font-data-mono-sm text-[10px] font-bold">{tofM} {tofAngle}</span>
              </div>
            </div>

            <span className="font-label-caps text-xs text-[#000928] font-bold mt-8">ROVER</span>
          </div>
        </div>
      </div>

      {/* Mode & Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Operation Mode */}
        <div className="bg-[#ffffff] rounded-xl p-4 shadow-[0_2px_8px_rgba(0,0,0,0.03)] border border-[#e2e2e9]">
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-headline-sm text-base text-[#1a1b21] font-semibold">Operation Mode</h2>
            <span className="font-data-mono-sm text-xs text-[#45464f]">SYS-OP</span>
          </div>
          <div className="flex bg-[#ededf5] rounded-lg p-1">
            <button
              onClick={() => setMode('MANUAL')}
              className={`flex-1 py-2 font-label-caps text-xs rounded-md transition-all ${
                !isAutonomous
                  ? 'bg-[#000928] text-white shadow-sm font-bold'
                  : 'bg-transparent text-[#45464f] hover:text-[#000928]'
              }`}
            >
              MANUAL
            </button>
            <button
              onClick={() => setMode('AUTONOMOUS')}
              className={`flex-1 py-2 font-label-caps text-xs rounded-md transition-all ${
                isAutonomous
                  ? 'bg-[#000928] text-white shadow-sm font-bold'
                  : 'bg-transparent text-[#45464f] hover:text-[#000928]'
              }`}
            >
              AUTONOMOUS
            </button>
          </div>
        </div>

        {/* Teleoperation D-Pad */}
        <div className="bg-[#ffffff] rounded-xl p-4 shadow-[0_2px_8px_rgba(0,0,0,0.03)] border border-[#e2e2e9] flex flex-col items-center">
          <div className="w-full flex justify-between items-center mb-2">
            <h2 className="font-headline-sm text-base text-[#1a1b21] font-semibold">Teleoperation</h2>
            <span className="font-data-mono-sm text-xs text-[#45464f]">CTRL-1</span>
          </div>

          <div className="grid grid-cols-3 gap-2 w-48 mt-2">
            <div />
            <button
              onClick={() => handleDrive(0.3, 0.0)}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_upward</span>
            </button>
            <div />

            <button
              onClick={() => handleDrive(0.0, 0.5)}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_back</span>
            </button>
            <button
              onClick={stopRover}
              className="w-14 h-14 bg-[#ffdad6] text-[#93000a] rounded-lg flex items-center justify-center hover:bg-[#D71920] hover:text-white transition-colors active:scale-95 border-2 border-[#D71920]"
            >
              <span className="font-label-caps text-[10px] font-bold">STOP</span>
            </button>
            <button
              onClick={() => handleDrive(0.0, -0.5)}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_forward</span>
            </button>

            <div />
            <button
              onClick={() => handleDrive(-0.3, 0.0)}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_downward</span>
            </button>
            <div />
          </div>
        </div>
      </div>

      {/* Telemetry Metrics Grid */}
      <div className="bg-[#ffffff] rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.03)] border border-[#e2e2e9] overflow-hidden">
        <div className="p-3.5 border-b border-[#e2e2e9] flex justify-between items-center bg-[#f9f9ff]">
          <h2 className="font-headline-sm text-base text-[#1a1b21] font-semibold">Telemetry</h2>
          <span className="font-data-mono-sm text-xs text-[#45464f]">TLM-RAW</span>
        </div>
        <div className="grid grid-cols-2 divide-x divide-y divide-[#e2e2e9]">
          <div className="p-4 flex flex-col">
            <span className="font-label-caps text-[10px] text-[#45464f] mb-1">UPTIME</span>
            <span className="font-data-mono-lg text-[#1a1b21] font-bold">04:12:33</span>
          </div>
          <div className="p-4 flex flex-col">
            <span className="font-label-caps text-[10px] text-[#45464f] mb-1">CORE TEMP</span>
            <span className="font-data-mono-lg text-[#1a1b21] font-bold">42.4°C</span>
          </div>
          <div className="p-4 flex flex-col">
            <span className="font-label-caps text-[10px] text-[#45464f] mb-1">MOTOR CURRENT</span>
            <span className="font-data-mono-lg text-[#1a1b21] font-bold">2.4 A</span>
          </div>
          <div className="p-4 flex flex-col">
            <span className="font-label-caps text-[10px] text-[#45464f] mb-1">SIGNAL STRENGTH</span>
            <div className="flex items-center gap-2">
              <span className="font-data-mono-lg text-[#395aac] font-bold">-68 dBm</span>
              <span className="material-symbols-outlined text-[#395aac] text-sm">wifi</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
