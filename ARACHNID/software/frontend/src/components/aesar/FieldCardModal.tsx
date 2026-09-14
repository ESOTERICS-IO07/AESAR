import React from 'react';
import { useRover } from '../../hooks/useRover';

export const FieldCardModal: React.FC = () => {
  const { fieldAssessment, isFieldCardModalOpen, setFieldCardModalOpen, missionStatus } = useRover();

  if (!isFieldCardModalOpen) return null;

  const card = fieldAssessment || missionStatus?.field_assessment;
  const missionId = card?.mission_id || missionStatus?.mission_id || 'AESAR-MISSION';
  const total = card?.total_stations_scouted || missionStatus?.completed_stations || 0;
  const balanced = card?.balanced_stations_count || 0;
  const moderate = card?.moderate_stations_count || 0;
  const imbalanced = card?.imbalanced_stations_count || 0;
  const hotspots = card?.hotspot_stations || [];
  const state = card?.overall_field_state || 'unknown';
  const avgPdr = card?.average_pdr != null ? card.average_pdr.toFixed(2) : '--';
  const avgTemp = card?.average_temperature_c != null ? `${card.average_temperature_c.toFixed(1)}°C` : '--';
  const avgHum = card?.average_humidity_percent != null ? `${card.average_humidity_percent.toFixed(1)}%` : '--';
  const avgSoil = card?.average_soil_moisture_percent != null ? `${card.average_soil_moisture_percent.toFixed(1)}%` : '--';
  const rec = card?.field_recommendation || 'Complete a full scouting mission to generate comprehensive field recommendations.';

  const stateThemeMap: Record<string, { bg: string; text: string; border: string; title: string }> = {
    balanced: {
      bg: '#f0fdf4',
      text: '#15803d',
      border: '#86efac',
      title: 'ECOSYSTEM EQUILIBRIUM · BALANCED',
    },
    moderate: {
      bg: '#fefce8',
      text: '#ca8a04',
      border: '#fde047',
      title: 'MODERATE PEST STRAIN · TARGETED OBSERVATION REQUIRED',
    },
    imbalanced: {
      bg: '#fef2f2',
      text: '#dc2626',
      border: '#fca5a5',
      title: 'PEST OUTBREAK THRESHOLD EXCEEDED · INTERVENTION ADVISORY',
    },
    unknown: {
      bg: '#f8fafc',
      text: '#475569',
      border: '#cbd5e1',
      title: 'INTERIM / INSUFFICIENT FIELD SCOUTING DATA',
    },
  };

  const theme = stateThemeMap[state.toLowerCase()] || stateThemeMap.unknown;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(15,23,42,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      <div style={{
        background: '#ffffff',
        borderRadius: 14,
        maxWidth: 720,
        width: '100%',
        boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)',
        border: '1px solid #e2e8f0',
        overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Card Top Banner */}
        <div style={{
          background: '#0f172a', color: '#ffffff', padding: '16px 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8' }}>
              AESAR AGRI-INTELLIGENCE REPORT
            </div>
            <h1 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0', letterSpacing: '-0.01em' }}>
              AESA Whole-Field Assessment Card
            </h1>
          </div>

          <button
            onClick={() => setFieldCardModalOpen(false)}
            style={{
              background: 'transparent', border: 'none', color: '#94a3b8',
              fontSize: 22, cursor: 'pointer', padding: 4, lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {/* Card Body */}
        <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Status Header */}
          <div style={{
            background: theme.bg,
            border: `2px solid ${theme.border}`,
            borderRadius: 10,
            padding: '14px 18px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ fontSize: 10, fontWeight: 800, color: theme.text, letterSpacing: '0.06em' }}>
                OVERALL FIELD ECOSYSTEM STATUS
              </div>
              <div style={{ fontSize: 17, fontWeight: 900, color: theme.text, marginTop: 2 }}>
                {theme.title}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: '#64748b', fontWeight: 600 }}>MISSION ID:</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#0f172a' }}>{missionId}</div>
            </div>
          </div>

          {/* Metric Quad-Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            <div style={{ background: '#f8fafc', padding: 12, borderRadius: 8, border: '1px solid #f1f5f9', textAlign: 'center' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>AVG PDR RATIO</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginTop: 2 }}>{avgPdr}</div>
              <div style={{ fontSize: 9, color: '#94a3b8' }}>Target &le; 2.0</div>
            </div>

            <div style={{ background: '#f8fafc', padding: 12, borderRadius: 8, border: '1px solid #f1f5f9', textAlign: 'center' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>AVG TEMPERATURE</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginTop: 2 }}>{avgTemp}</div>
              <div style={{ fontSize: 9, color: '#94a3b8' }}>Canopy ambient</div>
            </div>

            <div style={{ background: '#f8fafc', padding: 12, borderRadius: 8, border: '1px solid #f1f5f9', textAlign: 'center' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>AVG HUMIDITY</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginTop: 2 }}>{avgHum}</div>
              <div style={{ fontSize: 9, color: '#94a3b8' }}>Micro-climate</div>
            </div>

            <div style={{ background: '#f8fafc', padding: 12, borderRadius: 8, border: '1px solid #f1f5f9', textAlign: 'center' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>SOIL MOISTURE</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginTop: 2 }}>{avgSoil}</div>
              <div style={{ fontSize: 9, color: '#94a3b8' }}>Root zone</div>
            </div>
          </div>

          {/* Station Distribution Bar */}
          <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: 8, border: '1px solid #f1f5f9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, fontWeight: 700, color: '#475569', marginBottom: 8 }}>
              <span>SCOUTING STATION BREAKDOWN ({total} Stations Total)</span>
              <span>
                {balanced} Balanced · {moderate} Moderate · {imbalanced} Imbalanced
              </span>
            </div>

            {/* Distribution Multi-Bar */}
            <div style={{ height: 12, background: '#e2e8f0', borderRadius: 6, display: 'flex', overflow: 'hidden' }}>
              {total > 0 && (
                <>
                  <div style={{ width: `${(balanced / total) * 100}%`, background: '#22c55e' }} title="Balanced" />
                  <div style={{ width: `${(moderate / total) * 100}%`, background: '#eab308' }} title="Moderate" />
                  <div style={{ width: `${(imbalanced / total) * 100}%`, background: '#ef4444' }} title="Imbalanced" />
                </>
              )}
            </div>

            {hotspots.length > 0 && (
              <div style={{ fontSize: 11, color: '#b91c1c', fontWeight: 600, marginTop: 8 }}>
                🚨 Outbreak Hotspot Stations: {hotspots.map((h) => `#${h}`).join(', ')}
              </div>
            )}
          </div>

          {/* Expert Non-Pesticidal Management (NPM) Protocol */}
          <div style={{
            background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '14px 16px',
          }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: '#166534', marginBottom: 4 }}>
              AGRONOMIC NON-PESTICIDAL MANAGEMENT (NPM) DIRECTIVE:
            </div>
            <p style={{ margin: 0, fontSize: 13, color: '#14532d', lineHeight: 1.5 }}>
              {rec}
            </p>
          </div>

          {/* Scientific Prototype Validation Disclaimer */}
          <div style={{
            fontSize: 10, color: '#94a3b8', fontStyle: 'italic', borderTop: '1px solid #f1f5f9', paddingTop: 10,
          }}>
            * Prototype decision rules pending agricultural field validation. Metrics synthesize visual observations and calibrated sensor data under prototype thresholds.
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{
          background: '#f8fafc', borderTop: '1px solid #e2e8f0', padding: '12px 24px',
          display: 'flex', justifyContent: 'flex-end', gap: 12,
        }}>
          <button
            onClick={() => window.print()}
            style={{
              padding: '8px 16px', borderRadius: 6, border: '1px solid #cbd5e1',
              background: '#ffffff', color: '#0f172a', fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}
          >
            🖨 Print / Export
          </button>
          <button
            onClick={() => setFieldCardModalOpen(false)}
            style={{
              padding: '8px 20px', borderRadius: 6, border: 'none',
              background: '#0f172a', color: '#ffffff', fontSize: 12, fontWeight: 700, cursor: 'pointer',
            }}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
