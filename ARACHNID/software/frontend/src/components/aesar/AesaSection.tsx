import React from 'react';
import { useRover } from '../../hooks/useRover';

export const AesaSection: React.FC = () => {
  const { latestAesa, latestObservation } = useRover();

  const aesa = latestAesa || latestObservation?.analysis;
  const pdr = aesa?.pdr != null ? aesa.pdr.toFixed(2) : '--';
  const state = aesa?.ecosystem_state || 'unknown';
  const abiotic = aesa?.abiotic_risk;
  const abioticLevel = abiotic?.risk_level || 'LOW';
  const stressors = abiotic?.primary_stressors || [];
  const recommendation = aesa?.recommendation || 'Awaiting initial AESA data fusion...';

  const stateConfig: Record<string, { label: string; desc: string; bg: string; text: string; border: string; icon: string }> = {
    balanced: {
      label: 'BALANCED',
      desc: 'Natural biological control active',
      bg: '#f0fdf4',
      text: '#15803d',
      border: '#86efac',
      icon: '🌿',
    },
    moderate: {
      label: 'MODERATE',
      desc: 'Transitional strain · Monitor hotspot',
      bg: '#fefce8',
      text: '#ca8a04',
      border: '#fde047',
      icon: '⚠️',
    },
    imbalanced: {
      label: 'IMBALANCED',
      desc: 'Pest outbreak exceeds predator equilibrium',
      bg: '#fef2f2',
      text: '#dc2626',
      border: '#fca5a5',
      icon: '🚨',
    },
    unknown: {
      label: 'INSUFFICIENT DATA',
      desc: 'Awaiting sensor/vision fusion',
      bg: '#f8fafc',
      text: '#64748b',
      border: '#e2e8f0',
      icon: 'ℹ️',
    },
  };

  const current = stateConfig[state.toLowerCase()] || stateConfig.unknown;

  const abioticColor =
    abioticLevel === 'HIGH' ? '#dc2626' : abioticLevel === 'MODERATE' ? '#d97706' : '#15803d';

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
            Decision Intelligence
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', margin: 0 }}>
            AESA Analysis Engine
          </h2>
        </div>

        <span style={{
          fontSize: 9, fontWeight: 700, color: '#64748b',
          background: '#f1f5f9', padding: '2px 6px', borderRadius: 4,
        }}>
          DETERMINISTIC FORMULAS
        </span>
      </div>

      {/* Main Ecosystem State Card */}
      <div style={{
        background: current.bg,
        border: `2px solid ${current.border}`,
        borderRadius: 8,
        padding: '14px 18px',
        marginBottom: 14,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 28 }}>{current.icon}</span>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: current.text, letterSpacing: '0.04em' }}>
              AGRO-ECOSYSTEM EQUILIBRIUM
            </div>
            <div style={{ fontSize: 18, fontWeight: 900, color: current.text, letterSpacing: '0.02em' }}>
              {current.label}
            </div>
            <div style={{ fontSize: 11, color: '#475569', fontWeight: 500 }}>
              {current.desc}
            </div>
          </div>
        </div>

        {/* PDR & Abiotic Metrics */}
        <div style={{ display: 'flex', gap: 20, textAlign: 'right' }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>PDR RATIO</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#0f172a' }}>{pdr}</div>
            <div style={{ fontSize: 9, color: '#94a3b8' }}>Target &le; 2.0</div>
          </div>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>ABIOTIC RISK</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: abioticColor }}>{abioticLevel}</div>
            <div style={{ fontSize: 9, color: '#94a3b8' }}>Micro-climate</div>
          </div>
        </div>
      </div>

      {/* Stressors */}
      {stressors.length > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
          fontSize: 11, color: '#475569',
        }}>
          <span style={{ fontWeight: 700, color: '#64748b' }}>Climatic Factors:</span>
          {stressors.map((st, i) => (
            <span
              key={i}
              style={{
                background: '#f8fafc', padding: '2px 8px', borderRadius: 4,
                border: '1px solid #e2e8f0', fontSize: 10, fontWeight: 600,
              }}
            >
              {st}
            </span>
          ))}
        </div>
      )}

      {/* Non-Pesticidal Management Recommendation */}
      <div style={{
        background: '#f8fafc', borderRadius: 8, padding: '12px 14px',
        border: '1px solid #e2e8f0',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 11, fontWeight: 800, color: '#0f172a' }}>
            NPM PROTOCOL RECOMMENDATION:
          </span>
        </div>
        <p style={{ margin: 0, fontSize: 12, color: '#334155', lineHeight: 1.4 }}>
          {recommendation}
        </p>
      </div>
    </div>
  );
};
