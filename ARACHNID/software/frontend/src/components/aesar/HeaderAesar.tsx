import React from 'react';
import { useRover } from '../../hooks/useRover';

export const HeaderAesar: React.FC = () => {
  const { status, connectionState, aesarMode, toggleAesarMode } = useRover();
  const connected = connectionState === 'connected' && status.connected;
  const batteryStr = status.battery_percent >= 0 ? `${Math.round(status.battery_percent)}%` : '--';

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 40,
      background: '#ffffff',
      borderBottom: '1px solid #e2e8f0',
      padding: '0 28px',
      height: 60,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
    }}>
      {/* Brand & Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 8,
          background: '#15803d', display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#ffffff', fontWeight: 800, fontSize: 16, letterSpacing: '-0.02em',
          boxShadow: '0 2px 6px rgba(21,128,61,0.3)',
        }}>
          A
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 800, fontSize: 16, letterSpacing: '0.06em', color: '#0f172a' }}>
              AESAR
            </span>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.04em',
              color: '#15803d', background: '#dcfce7', padding: '2px 6px', borderRadius: 4,
            }}>
              AGRI-INTELLIGENCE
            </span>
          </div>
          <div style={{ fontSize: 10, color: '#64748b', letterSpacing: '0.02em' }}>
            Autonomous Ecosystem Scouting & Analysis Rover
          </div>
        </div>
      </div>

      {/* Center / Right controls: Mode Toggle, Connection, Battery */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        {/* Mode Indicator & Switcher */}
        <div style={{
          display: 'flex', alignItems: 'center',
          background: '#f1f5f9', padding: '3px 4px', borderRadius: 6,
          border: '1px solid #e2e8f0',
        }}>
          <button
            onClick={toggleAesarMode}
            style={{
              padding: '4px 10px', borderRadius: 4, border: 'none',
              fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
              cursor: 'pointer',
              background: aesarMode === 'DEMO' ? '#2563eb' : 'transparent',
              color: aesarMode === 'DEMO' ? '#ffffff' : '#64748b',
              boxShadow: aesarMode === 'DEMO' ? '0 1px 3px rgba(37,99,235,0.3)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            DEMO MODE
          </button>
          <button
            onClick={toggleAesarMode}
            style={{
              padding: '4px 10px', borderRadius: 4, border: 'none',
              fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
              cursor: 'pointer',
              background: aesarMode === 'LIVE' ? '#15803d' : 'transparent',
              color: aesarMode === 'LIVE' ? '#ffffff' : '#64748b',
              boxShadow: aesarMode === 'LIVE' ? '0 1px 3px rgba(21,128,61,0.3)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            LIVE SENSORS
          </button>
        </div>

        {/* Rover Hardware Connection */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: 11, fontWeight: 600, color: connected ? '#166534' : '#991b1b',
          background: connected ? '#dcfce7' : '#fee2e2',
          padding: '4px 10px', borderRadius: 6, border: `1px solid ${connected ? '#bbf7d0' : '#fecaca'}`,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: connected ? '#16a34a' : '#dc2626',
            boxShadow: connected ? '0 0 6px #16a34a' : 'none',
          }} />
          {connected ? 'ROVER ONLINE' : 'OFFLINE'}
        </div>

        {/* Rover State Badge */}
        <div style={{
          fontSize: 11, fontWeight: 600, color: '#334155',
          background: '#f8fafc', padding: '4px 8px', borderRadius: 6, border: '1px solid #e2e8f0',
        }}>
          MODE: <strong style={{ color: '#0f172a' }}>{status.mode}</strong>
        </div>

        {/* Battery */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 5,
          fontSize: 12, fontWeight: 700,
          color: status.battery_percent >= 0 && status.battery_percent < 25 ? '#dc2626' : '#0f172a',
        }}>
          <span style={{ fontSize: 13 }}>🔋</span>
          <span>{batteryStr}</span>
        </div>
      </div>
    </header>
  );
};
