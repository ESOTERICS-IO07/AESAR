import React, { useState } from 'react';
import { useRover } from '../hooks/useRover';

export const GlobalEStop: React.FC = () => {
  const { status, resetEmergencyStop } = useRover();
  const [resetting, setResetting] = useState(false);

  const isEStopActive = status.state === 'EMERGENCY_STOP';

  const handleReset = async () => {
    setResetting(true);
    try {
      await resetEmergencyStop();
    } catch (e) {
      console.error('Failed to reset emergency stop:', e);
    } finally {
      setTimeout(() => {
        setResetting(false);
      }, 500);
    }
  };

  if (!isEStopActive) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col justify-center items-center px-6 py-12 overflow-hidden text-white"
      style={{ backgroundColor: '#D71920' }}
    >
      {/* Background circular gradient */}
      <div className="absolute inset-0 flex items-center justify-center opacity-25 pointer-events-none">
        <div className="w-[160%] h-[160%] bg-[radial-gradient(circle_at_center,_transparent_20%,_rgba(0,0,0,0.5)_100%)]" />
      </div>

      {/* Warning stripes */}
      <div
        className="absolute inset-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage:
            'repeating-linear-gradient(45deg, transparent, transparent 20px, #000 20px, #000 40px)',
        }}
      />

      <div className="relative z-10 flex flex-col items-center justify-center text-center max-w-md w-full mx-auto gap-6">
        {/* Warning Icon with Pulsing Halo */}
        <div className="w-28 h-28 rounded-full border border-white/25 flex items-center justify-center shadow-2xl relative">
          <div className="absolute inset-0 rounded-full bg-white/15 animate-pulse-red" />
          <span
            className="material-symbols-outlined text-white text-[64px]"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            warning
          </span>
        </div>

        {/* Text Content */}
        <div className="flex flex-col gap-2">
          <h1 className="font-display-lg text-3xl md:text-4xl text-white uppercase tracking-tight font-extrabold leading-tight">
            Emergency<br />Stop Active
          </h1>
          <p className="font-data-mono-lg text-white/95 uppercase tracking-wider text-sm mt-1">
            Rover motion disabled.
          </p>
          <p className="font-data-mono-lg text-white/95 uppercase tracking-wider text-sm">
            Reset required.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="w-full flex flex-col gap-3 mt-4">
          <button
            onClick={handleReset}
            disabled={resetting}
            className="w-full h-14 bg-white text-[#D71920] font-headline-sm uppercase tracking-wider rounded font-bold shadow-xl flex items-center justify-center gap-2 active:scale-[0.98] transition-all hover:bg-[#f8fafc] disabled:opacity-75"
          >
            <span className={`material-symbols-outlined text-[22px] ${resetting ? 'animate-spin' : ''}`}>
              {resetting ? 'autorenew' : 'power_settings_new'}
            </span>
            <span>{resetting ? 'INITIALIZING...' : 'Reset System'}</span>
          </button>

          <button
            disabled
            className="w-full h-12 bg-transparent border border-white/30 text-white/40 font-label-caps uppercase tracking-[0.2em] rounded flex items-center justify-center cursor-not-allowed text-xs"
          >
            Return to Mission
          </button>
        </div>

        {/* Telemetry Footer */}
        <div className="mt-4 flex items-center justify-center gap-4 text-white/70 font-data-mono-sm text-xs">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px]">speed</span>
            <span>VEL: 0.00 m/s</span>
          </div>
          <div className="w-1.5 h-1.5 rounded-full bg-white/40" />
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px]">sensors</span>
            <span>SENSORS: LATCHED</span>
          </div>
        </div>
      </div>
    </div>
  );
};
