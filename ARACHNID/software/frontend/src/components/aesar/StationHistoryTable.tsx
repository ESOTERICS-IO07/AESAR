import React from 'react';
import { useRover } from '../../hooks/useRover';

export const StationHistoryTable: React.FC = () => {
  const { missionStatus } = useRover();
  const observations = missionStatus?.observations || [];

  const stateBadgeMap: Record<string, { bg: string; text: string }> = {
    balanced: { bg: '#dcfce7', text: '#15803d' },
    moderate: { bg: '#fef9c3', text: '#854d0e' },
    imbalanced: { bg: '#fee2e2', text: '#b91c1c' },
    unknown: { bg: '#f1f5f9', text: '#475569' },
  };

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: 10,
      padding: '16px 20px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8', textTransform: 'uppercase' }}>
            Mission Telemetry Log
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', margin: 0 }}>
            Station Observations History
          </h2>
        </div>

        <span style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>
          {observations.length} Recorded Stations
        </span>
      </div>

      {observations.length === 0 ? (
        <div style={{
          padding: '20px 16px', textAlign: 'center',
          background: '#f8fafc', borderRadius: 8, border: '1px dashed #cbd5e1',
          color: '#94a3b8', fontSize: 12,
        }}>
          No station observations recorded yet in active mission.
        </div>
      ) : (
        <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #f1f5f9', borderRadius: 6 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                <th style={{ padding: '8px 10px' }}>STATION</th>
                <th style={{ padding: '8px 10px' }}>TEMP</th>
                <th style={{ padding: '8px 10px' }}>HUM</th>
                <th style={{ padding: '8px 10px' }}>SOIL</th>
                <th style={{ padding: '8px 10px' }}>PESTS</th>
                <th style={{ padding: '8px 10px' }}>DEFENDERS</th>
                <th style={{ padding: '8px 10px' }}>PDR</th>
                <th style={{ padding: '8px 10px' }}>STATE</th>
              </tr>
            </thead>
            <tbody>
              {observations.map((obs, i) => {
                const stNum = obs.station?.id ?? obs.station_id ?? i + 1;
                const temp = obs.environment?.temperature_c != null ? `${obs.environment.temperature_c.toFixed(1)}°` : '--';
                const hum = obs.environment?.humidity_percent != null ? `${obs.environment.humidity_percent.toFixed(0)}%` : '--';
                const soil = obs.environment?.soil_moisture_percent != null ? `${obs.environment.soil_moisture_percent.toFixed(0)}%` : '--';

                const pestCount = (obs.vision?.pests || []).reduce((a, c) => a + c.count, 0);
                const defCount = (obs.vision?.defenders || []).reduce((a, c) => a + c.count, 0);
                const pdr = obs.analysis?.pdr != null ? obs.analysis.pdr.toFixed(1) : '--';
                const stState = obs.analysis?.ecosystem_state || 'unknown';
                const badge = stateBadgeMap[stState.toLowerCase()] || stateBadgeMap.unknown;

                return (
                  <tr key={i} style={{ borderBottom: '1px solid #f1f5f9', color: '#1e293b' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 700 }}>#{stNum}</td>
                    <td style={{ padding: '8px 10px' }}>{temp}</td>
                    <td style={{ padding: '8px 10px' }}>{hum}</td>
                    <td style={{ padding: '8px 10px' }}>{soil}</td>
                    <td style={{ padding: '8px 10px', color: pestCount > 10 ? '#dc2626' : '#1e293b', fontWeight: 600 }}>
                      {pestCount}
                    </td>
                    <td style={{ padding: '8px 10px', color: defCount > 0 ? '#16a34a' : '#64748b', fontWeight: 600 }}>
                      {defCount}
                    </td>
                    <td style={{ padding: '8px 10px', fontWeight: 700 }}>{pdr}</td>
                    <td style={{ padding: '8px 10px' }}>
                      <span style={{
                        padding: '2px 6px', borderRadius: 4,
                        fontSize: 9, fontWeight: 700,
                        background: badge.bg, color: badge.text,
                        textTransform: 'uppercase',
                      }}>
                        {stState}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
