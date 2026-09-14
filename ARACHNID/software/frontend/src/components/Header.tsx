import React from 'react';
import { useRover } from '../hooks/useRover';
import { ArachnidLogo } from './ArachnidLogo';

interface HeaderProps {
  activeTabTitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ activeTabTitle = 'Mission Control' }) => {
  const { status, connectionState, connectionAgeMs } = useRover();

  const isConnected = connectionState === 'connected' && status.connected;

  return (
    <header className="fixed top-0 left-0 w-full z-50 bg-[#ffffff]/90 backdrop-blur-xl border-b border-[#e2e2e9] shadow-[0_1px_8px_rgba(0,0,0,0.03)]">
      <div className="max-w-[1440px] mx-auto px-4 md:px-6 h-20 flex flex-col justify-center gap-1">
        {/* Top line */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ArachnidLogo size={34} />
            <div className="flex flex-col">
              <span className="font-headline-sm text-lg font-bold tracking-tight text-[#000928] uppercase leading-none">
                ARACHNID
              </span>
              <span className="font-label-caps text-[9px] text-[#757680] tracking-widest">
                AUTONOMOUS COMMAND
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Rover Connection */}
            <div className="flex items-center gap-1.5 bg-[#f3f3fa] px-2.5 py-1 rounded border border-[#e2e2e9]">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-[#10B981]' : 'bg-[#BA1A1A] animate-pulse'
                }`}
              />
              <span className="font-label-caps text-[10px] text-[#45464f]">
                {isConnected ? 'ROVER CONNECTED' : 'DISCONNECTED'}
              </span>
            </div>

            {/* Backend Link Status */}
            <div className="hidden sm:flex items-center gap-1.5 bg-[#f3f3fa] px-2.5 py-1 rounded border border-[#e2e2e9]">
              <span
                className={`w-2 h-2 rounded-full ${
                  connectionState === 'connected' ? 'bg-[#10B981]' : 'bg-[#D97706]'
                }`}
              />
              <span className="font-label-caps text-[10px] text-[#45464f]">
                LINK {connectionAgeMs > 0 && connectionAgeMs < 2000 ? `${connectionAgeMs}ms` : ''}
              </span>
            </div>

            {/* User Avatar */}
            <div className="w-8 h-8 rounded-full bg-[#000928] flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>

        {/* Sub banner: Mission Active */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                status.state === 'EMERGENCY_STOP'
                  ? 'bg-[#BA1A1A] animate-bounce'
                  : 'bg-[#D71920] animate-pulse-red'
              }`}
            />
            <span className="font-data-mono-sm text-[11px] text-[#45464f]">
              MISSION ACTIVE:{' '}
              <strong className="text-[#000928] uppercase font-semibold">
                {status.state === 'EMERGENCY_STOP' ? 'EMERGENCY OVERRIDE' : activeTabTitle}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-2 font-data-mono-sm text-[11px] text-[#757680]">
            <span className="hidden md:inline">MODE:</span>
            <span className="font-semibold text-[#000928]">{status.mode || 'MANUAL'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
