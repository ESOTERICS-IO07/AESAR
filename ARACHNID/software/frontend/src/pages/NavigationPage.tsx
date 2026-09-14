import React from 'react';
import { useRover } from '../hooks/useRover';
import { Target, MapPin, Route, Navigation as NavIcon } from 'lucide-react';

export const NavigationPage: React.FC = () => {
  const { navigationData, status } = useRover();

  const isNavigating = navigationData?.status === 'NAVIGATING' || status.state === 'NAVIGATING';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Summary */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800 }}>AUTONOMOUS NAVIGATION & TRAJECTORY</h2>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Path Planning provided by Autonomy Engine / Visualized here
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className={`badge ${isNavigating ? 'badge-warn' : 'badge-ok'}`}>
            <NavIcon size={12} />
            <span>STATUS: {navigationData?.status || 'IDLE'}</span>
          </span>
        </div>
      </div>

      {/* Goal & Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>ACTIVE GOAL</span>
            <Target size={16} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
            {navigationData?.goal ? `[${navigationData.goal.x.toFixed(2)}, ${navigationData.goal.y.toFixed(2)}]` : 'NO GOAL SET'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Frame: map coordinate space
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>PLANNED WAYPOINTS</span>
            <MapPin size={16} color="var(--accent-blue)" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
            {navigationData?.path ? navigationData.path.length : 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Discrete waypoints in trajectory
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>MISSION STATE</span>
            <Route size={16} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#10b981' }}>
            {status.mode}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            System state: {status.state}
          </div>
        </div>
      </div>

      {/* Waypoints Sequence List Table & Trajectory Preview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', letterSpacing: '0.05em' }}>
            WAYPOINTS IN ACTIVE PATH
          </h3>

          <div style={{ maxHeight: '360px', overflowY: 'auto' }}>
            {navigationData && navigationData.path && navigationData.path.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem' }}>#</th>
                    <th style={{ padding: '0.5rem' }}>X (m)</th>
                    <th style={{ padding: '0.5rem' }}>Y (m)</th>
                    <th style={{ padding: '0.5rem' }}>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {navigationData.path.map((pt, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>{idx + 1}</td>
                      <td style={{ padding: '0.5rem', color: 'var(--accent-cyan)' }}>{pt.x.toFixed(3)}</td>
                      <td style={{ padding: '0.5rem', color: 'var(--accent-blue)' }}>{pt.y.toFixed(3)}</td>
                      <td style={{ padding: '0.5rem' }}>
                        <span style={{ fontSize: '0.7rem', color: idx === navigationData.path.length - 1 ? '#10b981' : 'var(--text-muted)' }}>
                          {idx === navigationData.path.length - 1 ? 'GOAL' : 'WAYPOINT'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '3rem 0', fontSize: '0.85rem' }}>
                No active navigation path received from planner.
              </div>
            )}
          </div>
        </div>

        {/* Path Guidance Diagram / Canvas */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', letterSpacing: '0.05em', alignSelf: 'flex-start' }}>
            TRAJECTORY OVERVIEW
          </h3>

          <div
            style={{
              width: '100%',
              height: '300px',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: '6px',
              border: '1px dashed var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
            }}
          >
            <Route size={36} color="var(--accent-cyan)" />
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
              {navigationData?.goal ? `Target: [${navigationData.goal.x.toFixed(2)}, ${navigationData.goal.y.toFixed(2)}]` : 'Trajectory Idle'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {navigationData?.path ? `${navigationData.path.length} waypoints queued` : 'Awaiting goal dispatch'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
