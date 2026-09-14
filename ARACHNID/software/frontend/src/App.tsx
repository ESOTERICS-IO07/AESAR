import React, { useEffect, useCallback } from 'react';
import { RoverProvider, useRover } from './hooks/useRover';
import { LiveMap } from './components/LiveMap';
import { HeaderAesar } from './components/aesar/HeaderAesar';
import { MissionPanel } from './components/aesar/MissionPanel';
import { LiveCamera } from './components/aesar/LiveCamera';
import { EnvironmentSection } from './components/aesar/EnvironmentSection';
import { VisionSection } from './components/aesar/VisionSection';
import { AesaSection } from './components/aesar/AesaSection';
import { StationHistoryTable } from './components/aesar/StationHistoryTable';
import { FieldCardModal } from './components/aesar/FieldCardModal';

/* ─── Tiny SVG arrows ─── */
const ArrowUp = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 11l5-5 5 5"/></svg>
);
const ArrowDown = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 7l5 5 5-5"/></svg>
);
const ArrowLeft = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4l-5 5 5 5"/></svg>
);
const ArrowRight = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 4l5 5-5 5"/></svg>
);

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <h3 style={{
    fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
    color: '#94a3b8', marginBottom: 10, textTransform: 'uppercase',
  }}>
    {children}
  </h3>
);

const Stat: React.FC<{ label: string; value: string; color?: string; mono?: boolean }> = ({
  label, value, color = '#0f172a', mono = true,
}) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
    <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8' }}>
      {label}
    </span>
    <span className={mono ? 'mono' : ''} style={{
      fontSize: 18, fontWeight: 700, color, lineHeight: 1.15,
    }}>
      {value}
    </span>
  </div>
);

const RoverStatusBar: React.FC = () => {
  const { status } = useRover();
  const batteryStr = status.battery_percent >= 0 ? `${Math.round(status.battery_percent)}%` : '--';
  const posX = status.pose?.x !== undefined && status.pose?.x !== null ? status.pose.x.toFixed(2) : '--';
  const posY = status.pose?.y !== undefined && status.pose?.y !== null ? status.pose.y.toFixed(2) : '--';
  const headingStr = status.pose?.theta !== undefined && status.pose?.theta !== null ? `${Math.round(status.pose.theta * (180 / Math.PI))}°` : '--';

  return (
    <div style={{
      padding: '14px 18px', background: '#f8fafc', borderRadius: 8,
      border: '1px solid #e2e8f0', display: 'flex', gap: 32, flexWrap: 'wrap',
    }}>
      <Stat label="BATTERY" value={batteryStr} color={status.battery_percent >= 0 && status.battery_percent < 20 ? '#dc2626' : '#0f172a'} />
      <Stat label="POSITION" value={posX !== '--' && posY !== '--' ? `${posX}, ${posY} m` : '--'} />
      <Stat label="HEADING" value={headingStr} />
      <Stat label="ROVER STATE" value={status.state} color={status.state === 'EMERGENCY_STOP' ? '#dc2626' : '#15803d'} mono={false} />
    </div>
  );
};

const Sensors: React.FC = () => {
  const { telemetry } = useRover();

  const fmt = (mm: number | undefined) => (mm != null && mm > 0) ? (mm / 1000).toFixed(2) : '--';
  const getColor = (mm: number | undefined) => {
    if (mm == null || mm <= 0) return '#cbd5e1';
    if (mm < 300) return '#dc2626';
    if (mm < 800) return '#d97706';
    return '#1e293b';
  };

  const sensors = [
    { id: 'US_FL', val: telemetry?.us_fl_mm },
    { id: 'US_FC', val: telemetry?.us_fc_mm },
    { id: 'US_FR', val: telemetry?.us_fr_mm },
    { id: 'US_L', val: telemetry?.us_l_mm },
    { id: 'US_R', val: telemetry?.us_r_mm },
    { id: 'TOF', val: telemetry?.tof_front_mm },
  ];

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 14 }}>
      <SectionLabel>Distance Sensors (Proximity Safety)</SectionLabel>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '60px 60px 60px',
        gridTemplateRows: 'auto auto auto',
        alignItems: 'center', justifyItems: 'center',
        gap: '8px 0',
        width: 'fit-content',
        margin: '0 auto',
      }}>
        <SensorCell id="US_FL" value={fmt(sensors[0].val)} color={getColor(sensors[0].val)} />
        <SensorCell id="US_FC" value={fmt(sensors[1].val)} color={getColor(sensors[1].val)} />
        <SensorCell id="US_FR" value={fmt(sensors[2].val)} color={getColor(sensors[2].val)} />

        <SensorCell id="US_L" value={fmt(sensors[3].val)} color={getColor(sensors[3].val)} />
        <div />
        <SensorCell id="US_R" value={fmt(sensors[4].val)} color={getColor(sensors[4].val)} />

        <div />
        <div style={{
          width: 34, height: 42, borderRadius: 4,
          border: '2px solid #1e293b',
          position: 'relative', marginTop: 14,
        }}>
          {/* TOF label */}
          <div style={{
            position: 'absolute', top: -30, left: '50%', transform: 'translateX(-50%)',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
          }}>
            <div className="mono" style={{ fontSize: 11, fontWeight: 700, color: '#dc2626', lineHeight: 1.1 }}>
              {telemetry?.tof_distance_mm != null && telemetry.tof_distance_mm > 0 ? (telemetry.tof_distance_mm / 1000).toFixed(2) : '--'}
            </div>
            <div style={{
              background: '#dc2626', color: '#fff', fontSize: 7, padding: '1px 3px',
              borderRadius: 2, fontWeight: 700, letterSpacing: '0.04em', whiteSpace: 'nowrap',
            }}>
              TOF {telemetry?.tof_angle_deg != null ? `${telemetry.tof_angle_deg.toFixed(0)}°` : ''}
            </div>
          </div>

          <div style={{ position: 'absolute', top: -3, left: 3, width: 7, height: 4, background: '#1e293b', borderRadius: 1 }} />
          <div style={{ position: 'absolute', top: -3, right: 3, width: 7, height: 4, background: '#1e293b', borderRadius: 1 }} />
          <div style={{ position: 'absolute', bottom: -3, left: 3, width: 7, height: 4, background: '#1e293b', borderRadius: 1 }} />
          <div style={{ position: 'absolute', bottom: -3, right: 3, width: 7, height: 4, background: '#1e293b', borderRadius: 1 }} />
          <div style={{
            position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
            width: 0, height: 0,
            borderLeft: '4px solid transparent', borderRight: '4px solid transparent',
            borderBottom: '5px solid #1e293b',
          }} />
        </div>
        <div />
      </div>
    </div>
  );
};

const SensorCell: React.FC<{ id: string; value: string; color: string }> = ({ id, value, color }) => (
  <div style={{ textAlign: 'center', padding: '1px 0' }}>
    <div className="mono" style={{ fontSize: 12, fontWeight: 700, color, lineHeight: 1.1 }}>
      {value}
    </div>
    <div style={{ fontSize: 8, color: '#94a3b8', letterSpacing: '0.04em' }}>{id}</div>
  </div>
);

const Navigation: React.FC = () => {
  const { navigationData } = useRover();
  const navStatus = navigationData?.status ?? 'IDLE';
  const isNavigating = navStatus === 'NAVIGATING';
  const waypoints = navigationData?.path?.length ?? 0;
  const goalText = navigationData?.goal
    ? `(${navigationData.goal.x.toFixed(1)}, ${navigationData.goal.y.toFixed(1)})`
    : '—';

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 14 }}>
      <SectionLabel>Autonomous Waypoint Guidance</SectionLabel>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
        <span style={{
          fontSize: 12, fontWeight: 700,
          color: isNavigating ? '#2563eb' : '#0f172a',
        }}>
          {navStatus}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11, color: '#64748b' }}>
        <div>Station Goal: <strong className="mono" style={{ color: '#0f172a' }}>{goalText}</strong></div>
        <div>Active Waypoints: <strong className="mono" style={{ color: '#0f172a' }}>{waypoints}</strong></div>
      </div>
    </div>
  );
};

const Controls: React.FC = () => {
  const { sendCommand, stopRover, setMode, status, isEmergencyStopped } = useRover();

  const btn: React.CSSProperties = {
    width: 36, height: 36, borderRadius: 4,
    border: '1px solid #cbd5e1', background: '#f8fafc',
    cursor: 'pointer', display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    color: '#0f172a', transition: 'background 0.12s',
  };

  const handleKey = useCallback((e: KeyboardEvent) => {
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;
    if (isEmergencyStopped) return;
    switch (e.key) {
      case 'w': case 'W': case 'ArrowUp': e.preventDefault(); sendCommand(0.3, 0); break;
      case 's': case 'S': case 'ArrowDown': e.preventDefault(); sendCommand(-0.3, 0); break;
      case 'a': case 'A': case 'ArrowLeft': e.preventDefault(); sendCommand(0, 0.5); break;
      case 'd': case 'D': case 'ArrowRight': e.preventDefault(); sendCommand(0, -0.5); break;
      case ' ': e.preventDefault(); stopRover(); break;
    }
  }, [sendCommand, stopRover, isEmergencyStopped]);

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 14 }}>
      <SectionLabel>Manual Rover Velocity Controls</SectionLabel>

      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {/* D-Pad */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 36px)', gap: 3 }}>
          <div />
          <button style={btn} onClick={() => sendCommand(0.3, 0)} disabled={isEmergencyStopped}><ArrowUp /></button>
          <div />
          <button style={btn} onClick={() => sendCommand(0, 0.5)} disabled={isEmergencyStopped}><ArrowLeft /></button>
          <button
            style={{ ...btn, background: '#dc2626', color: '#fff', border: 'none', fontSize: 8, fontWeight: 800 }}
            onClick={stopRover}
          >STOP</button>
          <button style={btn} onClick={() => sendCommand(0, -0.5)} disabled={isEmergencyStopped}><ArrowRight /></button>
          <div />
          <button style={btn} onClick={() => sendCommand(-0.3, 0)} disabled={isEmergencyStopped}><ArrowDown /></button>
          <div />
        </div>

        {/* Mode toggle */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {(['MANUAL', 'AUTONOMOUS'] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)} style={{
              padding: '6px 14px', borderRadius: 4, fontSize: 10, fontWeight: 700,
              letterSpacing: '0.04em', cursor: 'pointer',
              border: status.mode === m ? '1px solid #0f172a' : '1px solid #cbd5e1',
              background: status.mode === m ? '#0f172a' : '#ffffff',
              color: status.mode === m ? '#ffffff' : '#64748b',
            }}>
              {m}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

const EStopButton: React.FC = () => {
  const { triggerEmergencyStop } = useRover();

  return (
    <button
      onClick={triggerEmergencyStop}
      style={{
        position: 'fixed', bottom: 20, right: 20, zIndex: 50,
        padding: '10px 20px', borderRadius: 6,
        background: '#dc2626', color: '#ffffff', border: 'none',
        fontSize: 11, fontWeight: 800, letterSpacing: '0.06em',
        cursor: 'pointer', boxShadow: '0 4px 12px rgba(220,38,38,0.3)',
      }}
    >
      🛑 EMERGENCY STOP
    </button>
  );
};

const EStopOverlay: React.FC = () => {
  const { status, resetEmergencyStop } = useRover();
  if (status.state !== 'EMERGENCY_STOP') return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(255,255,255,0.96)',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 16,
    }}>
      <div style={{
        width: 60, height: 60, borderRadius: '50%', background: '#dc2626',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#ffffff', fontSize: 26, fontWeight: 800,
      }}>
        !
      </div>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: '#dc2626', margin: 0 }}>
        EMERGENCY STOP ENGAGED
      </h1>
      <p style={{ fontSize: 13, color: '#64748b', margin: 0 }}>
        Motors isolated · Physical failsafe active · Operator reset required
      </p>
      <button
        onClick={resetEmergencyStop}
        style={{
          marginTop: 8, padding: '10px 28px', borderRadius: 6,
          border: '1px solid #cbd5e1', background: '#0f172a', color: '#ffffff',
          fontSize: 12, fontWeight: 700, cursor: 'pointer',
        }}
      >
        Reset Rover Safety System
      </button>
    </div>
  );
};

const Logs: React.FC = () => {
  const { logs } = useRover();
  const recent = logs.slice(-6).reverse();

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 14 }}>
      <SectionLabel>System Activity Log</SectionLabel>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {recent.length === 0 && (
          <span style={{ fontSize: 11, color: '#94a3b8' }}>Waiting for system events…</span>
        )}
        {recent.map((log, i) => {
          const t = new Date(log.timestamp_ms);
          const ts = `${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}:${String(t.getSeconds()).padStart(2, '0')}`;
          const isErr = log.level === 'ERROR' || log.level === 'CRITICAL';
          const isWarn = log.level === 'WARNING' || log.level === 'WARN';
          return (
            <div key={i} style={{ display: 'flex', gap: 10, fontSize: 11, alignItems: 'baseline' }}>
              <span className="mono" style={{ fontSize: 10, color: '#94a3b8', flexShrink: 0 }}>{ts}</span>
              <span style={{ color: isErr ? '#dc2626' : isWarn ? '#d97706' : '#334155' }}>
                {log.message}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const AppContent: React.FC = () => {
  return (
    <div style={{ background: '#f8fafc', minHeight: '100vh', color: '#0f172a' }}>
      <HeaderAesar />
      <EStopOverlay />
      <EStopButton />
      <FieldCardModal />

      {/* Main 2-Column Responsive Dashboard */}
      <main style={{
        maxWidth: 1440, margin: '0 auto', padding: '20px 24px 80px',
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
        gap: 20, alignItems: 'start',
      }}>
        {/* Left Column: Agricultural Intelligence & Sensing */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <MissionPanel />
          <LiveCamera />
          <EnvironmentSection />
          <VisionSection />
          <AesaSection />
        </div>

        {/* Right Column: Spatial Tracking, Rover Subsystems & Logs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <section style={{
            background: '#ffffff', border: '1px solid #e2e8f0',
            borderRadius: 10, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                Spatial Telemetry & Grid
              </span>
              <span style={{ fontSize: 11, fontWeight: 600, color: '#15803d' }}>
                Field Sampling Grid (200x200)
              </span>
            </div>
            <LiveMap />
          </section>

          <RoverStatusBar />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Sensors />
            <Controls />
          </div>

          <Navigation />
          <StationHistoryTable />
          <Logs />
        </div>
      </main>
    </div>
  );
};

export const App: React.FC = () => (
  <RoverProvider>
    <AppContent />
  </RoverProvider>
);

export default App;
