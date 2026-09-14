import React, { useState, useEffect, useCallback } from 'react';
import { useRover } from '../hooks/useRover';

export const ControlsPage: React.FC = () => {
  const { sendCommand, stopRover, isEmergencyStopped } = useRover();
  const [linearSpeed, setLinearSpeed] = useState<number>(0.3);
  const [angularSpeed, setAngularSpeed] = useState<number>(0.5);
  const [lastCommandAck, setLastCommandAck] = useState<{ id: string; time: string; success: boolean } | null>(null);

  const executeCommand = useCallback(
    async (lin: number, ang: number, label: string) => {
      if (isEmergencyStopped) return;
      const success = await sendCommand(lin, ang, 'MANUAL');
      setLastCommandAck({
        id: `${label} (${lin.toFixed(2)} m/s, ${ang.toFixed(2)} rad/s)`,
        time: new Date().toLocaleTimeString(),
        success,
      });
    },
    [isEmergencyStopped, sendCommand]
  );

  const handleForward = () => executeCommand(linearSpeed, 0.0, 'FORWARD');
  const handleBackward = () => executeCommand(-linearSpeed, 0.0, 'BACKWARD');
  const handleTurnLeft = () => executeCommand(0.0, angularSpeed, 'TURN_LEFT');
  const handleTurnRight = () => executeCommand(0.0, -angularSpeed, 'TURN_RIGHT');
  const handleStop = async () => {
    const success = await stopRover();
    setLastCommandAck({
      id: 'NORMAL_STOP (0.0, 0.0)',
      time: new Date().toLocaleTimeString(),
      success,
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      if (isEmergencyStopped) return;

      switch (e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
          e.preventDefault();
          handleForward();
          break;
        case 'ArrowDown':
        case 's':
        case 'S':
          e.preventDefault();
          handleBackward();
          break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
          e.preventDefault();
          handleTurnLeft();
          break;
        case 'ArrowRight':
        case 'd':
        case 'D':
          e.preventDefault();
          handleTurnRight();
          break;
        case ' ':
          e.preventDefault();
          handleStop();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleForward, handleBackward, handleTurnLeft, handleTurnRight, handleStop, isEmergencyStopped]);

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="font-headline-md text-2xl text-[#1a1b21] font-bold">Teleoperation Console</h1>
        <span className="font-label-caps text-xs text-[#45464f] bg-[#e8e7ef] px-2.5 py-1 rounded">
          CTRL-01
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Speed Calibration */}
        <div className="bg-[#ffffff] rounded-xl p-5 border border-[#e2e2e9] shadow-sm flex flex-col gap-4">
          <div className="flex justify-between items-center border-b border-[#e2e2e9] pb-3">
            <h2 className="font-headline-sm text-base text-[#1a1b21] font-semibold">Velocity Calibration</h2>
            <span className="font-data-mono-sm text-xs text-[#395aac]">CALIB</span>
          </div>

          <div className="flex flex-col gap-4">
            {/* Linear Speed */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-[#45464f]">LINEAR SPEED</span>
                <span className="font-bold text-[#000928]">{linearSpeed.toFixed(2)} m/s</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.05"
                value={linearSpeed}
                onChange={(e) => setLinearSpeed(parseFloat(e.target.value))}
                disabled={isEmergencyStopped}
                className="w-full accent-[#000928] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#757680] font-mono">
                <span>0.05 m/s (Min)</span>
                <span>1.00 m/s (Limit)</span>
              </div>
            </div>

            {/* Angular Speed */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-[#45464f]">ANGULAR SPEED</span>
                <span className="font-bold text-[#000928]">{angularSpeed.toFixed(2)} rad/s</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.5"
                step="0.1"
                value={angularSpeed}
                onChange={(e) => setAngularSpeed(parseFloat(e.target.value))}
                disabled={isEmergencyStopped}
                className="w-full accent-[#000928] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#757680] font-mono">
                <span>0.10 rad/s</span>
                <span>1.50 rad/s</span>
              </div>
            </div>

            {/* Command ACK */}
            <div className="bg-[#f3f3fa] p-3 rounded border border-[#e2e2e9] text-xs font-mono">
              <span className="text-[#757680] text-[10px] block mb-1">COMMAND ACKNOWLEDGEMENT</span>
              {lastCommandAck ? (
                <span className={lastCommandAck.success ? 'text-[#10b981]' : 'text-[#ba1a1a]'}>
                  [{lastCommandAck.time}] {lastCommandAck.id}
                </span>
              ) : (
                <span className="text-[#757680]">Ready for operator command input.</span>
              )}
            </div>
          </div>
        </div>

        {/* D-Pad Controller */}
        <div className="bg-[#ffffff] rounded-xl p-5 border border-[#e2e2e9] shadow-sm flex flex-col items-center justify-between">
          <div className="w-full flex justify-between items-center border-b border-[#e2e2e9] pb-3 mb-2">
            <h2 className="font-headline-sm text-base text-[#1a1b21] font-semibold">Directional Telepad</h2>
            <span className="font-data-mono-sm text-xs text-[#45464f]">WASD</span>
          </div>

          <div className="grid grid-cols-3 gap-2 w-48 my-auto">
            <div />
            <button
              onClick={handleForward}
              disabled={isEmergencyStopped}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_upward</span>
            </button>
            <div />

            <button
              onClick={handleTurnLeft}
              disabled={isEmergencyStopped}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_back</span>
            </button>
            <button
              onClick={handleStop}
              disabled={isEmergencyStopped}
              className="w-14 h-14 bg-[#ffdad6] text-[#93000a] rounded-lg flex items-center justify-center hover:bg-[#D71920] hover:text-white transition-colors active:scale-95 border-2 border-[#D71920]"
            >
              <span className="font-label-caps text-[10px] font-bold">STOP</span>
            </button>
            <button
              onClick={handleTurnRight}
              disabled={isEmergencyStopped}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_forward</span>
            </button>

            <div />
            <button
              onClick={handleBackward}
              disabled={isEmergencyStopped}
              className="w-14 h-14 bg-[#ededf5] rounded-lg flex items-center justify-center hover:bg-[#89a8ff] hover:text-[#000928] transition-colors active:scale-95 border border-[#e2e2e9]"
            >
              <span className="material-symbols-outlined">arrow_downward</span>
            </button>
            <div />
          </div>

          <div className="w-full text-center text-[10px] text-[#757680] font-mono mt-3">
            Keys: W (Forward), S (Rev), A (Left), D (Right), Space (Stop)
          </div>
        </div>
      </div>
    </div>
  );
};
