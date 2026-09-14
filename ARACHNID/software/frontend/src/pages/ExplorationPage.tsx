import React from 'react';
import { useRover } from '../hooks/useRover';
import { Flag, Target, Percent, Play, Square } from 'lucide-react';

export const ExplorationPage: React.FC = () => {
  const { explorationData, setMode, status, isEmergencyStopped } = useRover();

  const handleStartExploration = async () => {
    if (isEmergencyStopped) return;
    await setMode('AUTONOMOUS');
  };

  const handleStopExploration = async () => {
    await setMode('MANUAL');
  };

  const percent = explorationData ? Math.min(Math.max(explorationData.explored_percent, 0), 100) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Summary */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800 }}>FRONTIER-BASED AUTONOMOUS EXPLORATION</h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Unmapped frontier detection and autonomous goal assignment
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className={`badge ${status.mode === 'AUTONOMOUS' ? 'badge-ok' : 'badge-neutral'}`}>
            <span>STATUS: {explorationData?.status || 'IDLE'}</span>
          </span>
        </div>
      </div>

      {/* Exploration Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        {/* Explored Area Percentage */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              EXPLORED MAP COVERAGE
            </span>
            <Percent size={16} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#10b981' }}>
            {percent.toFixed(1)}%
          </div>
          {/* Progress Bar */}
          <div style={{ height: '8px', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden', marginTop: '0.75rem' }}>
            <div
              style={{
                height: '100%',
                width: `${percent}%`,
                backgroundColor: '#10b981',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>

        {/* Frontier Count */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              DETECTED FRONTIERS
            </span>
            <Flag size={16} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#f59e0b' }}>
            {explorationData ? explorationData.frontier_count : 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Open boundary candidate zones
          </div>
        </div>

        {/* Frontier Target Goal */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              CURRENT FRONTIER TARGET
            </span>
            <Target size={16} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
            {explorationData?.current_goal
              ? `[${explorationData.current_goal.x.toFixed(2)}, ${explorationData.current_goal.y.toFixed(2)}]`
              : 'NONE'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Coordinates in map coordinate frame
          </div>
        </div>
      </div>

      {/* Mission Control Panel */}
      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', letterSpacing: '0.05em' }}>
          EXPLORATION MISSION CONTROLS
        </h3>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            onClick={handleStartExploration}
            disabled={isEmergencyStopped || status.mode === 'AUTONOMOUS'}
            className="btn-reset"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              backgroundColor: '#065f46',
              borderColor: '#10b981',
              color: '#fff',
              cursor: isEmergencyStopped || status.mode === 'AUTONOMOUS' ? 'not-allowed' : 'pointer',
              opacity: isEmergencyStopped || status.mode === 'AUTONOMOUS' ? 0.5 : 1,
            }}
          >
            <Play size={18} />
            <span>START AUTONOMOUS EXPLORATION</span>
          </button>

          <button
            onClick={handleStopExploration}
            disabled={isEmergencyStopped || status.mode === 'MANUAL'}
            className="btn-reset"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              backgroundColor: '#1e293b',
              borderColor: '#64748b',
              color: '#fff',
              cursor: isEmergencyStopped || status.mode === 'MANUAL' ? 'not-allowed' : 'pointer',
              opacity: isEmergencyStopped || status.mode === 'MANUAL' ? 0.5 : 1,
            }}
          >
            <Square size={18} />
            <span>SWITCH TO MANUAL MODE</span>
          </button>
        </div>

        {isEmergencyStopped && (
          <div style={{ marginTop: '1rem', color: '#f87171', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            ⚠️ Cannot start autonomous exploration while emergency stop is latched.
          </div>
        )}
      </div>
    </div>
  );
};
