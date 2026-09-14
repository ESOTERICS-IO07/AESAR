import React from 'react';
import { useRover } from '../../hooks/useRover';

export const MissionPanel: React.FC = () => {
  const {
    missionStatus,
    startMission,
    pauseMission,
    resumeMission,
    abortMission,
    analyzeCurrentStation,
    setFieldCardModalOpen,
  } = useRover();

  const isRunning =
    missionStatus?.state &&
    !['IDLE', 'COMPLETED', 'ABORTED', 'ERROR'].includes(missionStatus.state);

  const isPaused = missionStatus?.state === 'STABILIZING' && false; // Or state check

  const total = missionStatus?.total_stations || 10;
  const completed = missionStatus?.completed_stations || 0;
  const pct = Math.round((completed / Math.max(1, total)) * 100);

  const curStation = missionStatus?.current_station;
  const stationName = curStation?.name || (curStation?.id ? `Station ${curStation.id} (${curStation.x}, ${curStation.y})` : 'Awaiting Mission Start');

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: 10,
      padding: '16px 20px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
    }}>
      {/* Header & Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8', textTransform: 'uppercase' }}>
            AESA Mission Controller
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', margin: '2px 0 0' }}>
            Autonomous Scouting Lifecycle
          </h2>
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          padding: '4px 10px', borderRadius: 20,
          background: isRunning ? '#eff6ff' : missionStatus?.state === 'COMPLETED' ? '#f0fdf4' : '#f8fafc',
          border: `1px solid ${isRunning ? '#bfdbfe' : missionStatus?.state === 'COMPLETED' ? '#bbf7d0' : '#e2e8f0'}`,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: isRunning ? '#2563eb' : missionStatus?.state === 'COMPLETED' ? '#16a34a' : '#64748b',
          }} />
          <span style={{
            fontSize: 11, fontWeight: 700,
            color: isRunning ? '#1d4ed8' : missionStatus?.state === 'COMPLETED' ? '#15803d' : '#475569',
          }}>
            {missionStatus?.state || 'IDLE'}
          </span>
        </div>
      </div>

      {/* Current Station Info */}
      <div style={{
        background: '#f8fafc', borderRadius: 8, padding: '10px 14px',
        border: '1px solid #f1f5f9', marginBottom: 14,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>Active Sampling Target:</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{stationName}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>Scouted Stations:</div>
          <div style={{ fontSize: 14, fontWeight: 800, color: '#15803d' }}>
            {completed} / {total} <span style={{ fontSize: 11, color: '#64748b', fontWeight: 500 }}>({pct}%)</span>
          </div>
        </div>
      </div>

      {/* Station Dots Map (10 stations) */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, justifyContent: 'space-between' }}>
        {Array.from({ length: total }, (_, i) => {
          const stNum = i + 1;
          const obs = missionStatus?.observations?.find((o) => o.station?.id === stNum);
          const isCurrent = curStation?.id === stNum;
          const isDone = Boolean(obs);

          let dotBg = '#e2e8f0';
          let borderCol = '#cbd5e1';
          if (isCurrent && isRunning) {
            dotBg = '#3b82f6';
            borderCol = '#1d4ed8';
          } else if (isDone) {
            const stState = obs?.analysis?.ecosystem_state;
            if (stState === 'balanced') {
              dotBg = '#22c55e';
              borderCol = '#16a34a';
            } else if (stState === 'moderate') {
              dotBg = '#eab308';
              borderCol = '#ca8a04';
            } else if (stState === 'imbalanced') {
              dotBg = '#ef4444';
              borderCol = '#dc2626';
            } else {
              dotBg = '#94a3b8';
              borderCol = '#64748b';
            }
          }

          return (
            <div
              key={stNum}
              title={`Station ${stNum}: ${obs?.analysis?.ecosystem_state || (isCurrent ? 'Scanning' : 'Pending')}`}
              style={{
                flex: 1, height: 26, borderRadius: 5,
                background: dotBg,
                border: `1px solid ${borderCol}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 700,
                color: isDone || isCurrent ? '#ffffff' : '#64748b',
                transition: 'all 0.2s ease',
              }}
            >
              {stNum}
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      <div style={{ height: 4, background: '#f1f5f9', borderRadius: 2, overflow: 'hidden', marginBottom: 16 }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: '#15803d', borderRadius: 2,
          transition: 'width 0.4s ease',
        }} />
      </div>

      {/* Controls row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
        {!isRunning ? (
          <button
            onClick={() => startMission()}
            style={{
              padding: '8px 18px', borderRadius: 6, border: 'none',
              background: '#15803d', color: '#ffffff',
              fontSize: 12, fontWeight: 700, cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
              boxShadow: '0 2px 4px rgba(21,128,61,0.2)',
            }}
          >
            ▶ Start 10-Station Mission
          </button>
        ) : (
          <>
            <button
              onClick={() => (isPaused ? resumeMission() : pauseMission())}
              style={{
                padding: '8px 16px', borderRadius: 6, border: '1px solid #f59e0b',
                background: '#fef3c7', color: '#b45309',
                fontSize: 12, fontWeight: 700, cursor: 'pointer',
              }}
            >
              ⏸ Pause
            </button>
            <button
              onClick={() => abortMission()}
              style={{
                padding: '8px 16px', borderRadius: 6, border: '1px solid #fca5a5',
                background: '#fee2e2', color: '#b91c1c',
                fontSize: 12, fontWeight: 700, cursor: 'pointer',
              }}
            >
              ⏹ Abort
            </button>
          </>
        )}

        <button
          onClick={() => analyzeCurrentStation()}
          disabled={isRunning}
          style={{
            padding: '8px 16px', borderRadius: 6,
            border: '1px solid #bfdbfe', background: isRunning ? '#f1f5f9' : '#eff6ff',
            color: isRunning ? '#94a3b8' : '#1d4ed8',
            fontSize: 12, fontWeight: 700,
            cursor: isRunning ? 'not-allowed' : 'pointer',
          }}
        >
          📷 Analyze Current Station
        </button>

        <button
          onClick={() => setFieldCardModalOpen(true)}
          style={{
            marginLeft: 'auto',
            padding: '8px 16px', borderRadius: 6,
            border: '1px solid #0f172a', background: '#0f172a', color: '#ffffff',
            fontSize: 12, fontWeight: 700, cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(15,23,42,0.2)',
          }}
        >
          📋 View AESA Field Card
        </button>
      </div>
    </div>
  );
};
