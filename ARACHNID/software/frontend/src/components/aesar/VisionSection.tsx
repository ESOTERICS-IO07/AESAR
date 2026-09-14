import React from 'react';
import { useRover } from '../../hooks/useRover';

export const VisionSection: React.FC = () => {
  const { latestObservation, aesarMode } = useRover();
  const vision = latestObservation?.vision;

  const detections = vision?.detections || [];
  const pests = detections.length > 0 
    ? detections.filter((d) => d.category === 'pest').map((d) => ({ name: d.class, count: d.count, confidence: d.confidence }))
    : vision?.pests || [];
  const defenders = detections.length > 0
    ? detections.filter((d) => d.category === 'defender').map((d) => ({ name: d.class, count: d.count, confidence: d.confidence }))
    : vision?.defenders || [];

  const view = vision?.view ? vision.view.toUpperCase() : 'MIDDLE';
  const status = vision?.status ? vision.status.toUpperCase().replace('_', ' ') : 'READY';
  const plantHealth = vision?.plant_health || 'healthy';
  const symptoms = vision?.leaf_damage_symptoms || [];
  const confidence = vision?.overall_confidence ? Math.round(vision.overall_confidence * 100) : null;
  const quality = vision?.image_quality || 'GOOD';
  const isModelNotConfigured = vision?.status === 'model_not_configured';
  const isImageUnavailable = vision?.status === 'image_unavailable';

  const healthColorMap: Record<string, { bg: string; text: string; border: string }> = {
    healthy: { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' },
    mild_stress: { bg: '#fef9c3', text: '#854d0e', border: '#fef08a' },
    moderate_stress: { bg: '#ffedd5', text: '#c2410c', border: '#fed7aa' },
    severe_stress: { bg: '#fee2e2', text: '#b91c1c', border: '#fecaca' },
    unknown: { bg: '#f1f5f9', text: '#475569', border: '#e2e8f0' },
  };

  const currentHealthStyle = healthColorMap[plantHealth] || healthColorMap.unknown;

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
            YOLO & Scouting Intelligence
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', margin: 0 }}>
            Visual Scouting
          </h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* Mode Badge */}
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.04em',
            padding: '2px 6px', borderRadius: 4,
            background: aesarMode === 'LIVE' ? '#ecfdf5' : '#f8fafc',
            color: aesarMode === 'LIVE' ? '#047857' : '#64748b',
            border: `1px solid ${aesarMode === 'LIVE' ? '#a7f3d0' : '#e2e8f0'}`,
          }}>
            {aesarMode}
          </span>

          {/* Canopy View Badge */}
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.04em',
            padding: '2px 6px', borderRadius: 4,
            background: '#e0e7ff', color: '#3730a3', border: '1px solid #c7d2fe',
          }}>
            VIEW: {view}
          </span>

          {/* Status Badge */}
          <span style={{
            fontSize: 9, fontWeight: 700,
            padding: '2px 6px', borderRadius: 4,
            background: isModelNotConfigured ? '#fee2e2' : isImageUnavailable ? '#fef3c7' : '#dcfce7',
            color: isModelNotConfigured ? '#991b1b' : isImageUnavailable ? '#92400e' : '#15803d',
            border: `1px solid ${isModelNotConfigured ? '#fecaca' : isImageUnavailable ? '#fde68a' : '#bbf7d0'}`,
          }}>
            {status}
          </span>

          {confidence !== null && (
            <div style={{
              fontSize: 9, fontWeight: 700,
              padding: '2px 6px', borderRadius: 4,
              background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0',
            }}>
              {confidence}% · {quality}
            </div>
          )}
        </div>
      </div>

      {isModelNotConfigured ? (
        <div style={{
          padding: '16px', borderRadius: 8,
          background: '#fef2f2', border: '1px solid #fecaca',
          color: '#991b1b', fontSize: 12,
        }}>
          <div style={{ fontWeight: 800, marginBottom: 4 }}>⚠️ YOLO MODEL NOT CONFIGURED</div>
          <div style={{ color: '#7f1d1d', fontSize: 11 }}>
            No trained weights configured. Switch to <strong>DEMO MODE</strong> to run deterministic validation, or set <code>VISION_MODEL_PATH</code> in configuration.
          </div>
        </div>
      ) : !vision ? (
        <div style={{
          padding: '24px 16px', textAlign: 'center',
          background: '#f8fafc', borderRadius: 8, border: '1px dashed #cbd5e1',
          color: '#94a3b8', fontSize: 12,
        }}>
          No plant scouting frame analyzed yet. Start mission or trigger &quot;Analyze Frame&quot;.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Pests & Defenders 2-Column */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {/* Pests */}
            <div style={{
              background: '#fef2f2', padding: '10px 12px', borderRadius: 8,
              border: '1px solid #fecaca',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 800, color: '#991b1b', letterSpacing: '0.04em' }}>
                  DETECTED PESTS
                </span>
                <span style={{
                  fontSize: 11, fontWeight: 800, color: '#b91c1c',
                  background: '#ffffff', padding: '1px 6px', borderRadius: 10,
                }}>
                  {pests.reduce((a, c) => a + c.count, 0)} Total
                </span>
              </div>
              {pests.length === 0 ? (
                <div style={{ fontSize: 11, color: '#64748b' }}>None visible (Clean canopy)</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {pests.map((p, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                      <span style={{ fontWeight: 600, color: '#7f1d1d', textTransform: 'capitalize' }}>
                        {p.name.replace(/_/g, ' ')}:
                      </span>
                      <span style={{ fontWeight: 700, color: '#991b1b' }}>
                        {p.count} <span style={{ fontSize: 9, color: '#64748b', fontWeight: 500 }}>({Math.round(p.confidence * 100)}%)</span>
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Defenders */}
            <div style={{
              background: '#f0fdf4', padding: '10px 12px', borderRadius: 8,
              border: '1px solid #bbf7d0',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 800, color: '#166534', letterSpacing: '0.04em' }}>
                  BENEFICIAL DEFENDERS
                </span>
                <span style={{
                  fontSize: 11, fontWeight: 800, color: '#15803d',
                  background: '#ffffff', padding: '1px 6px', borderRadius: 10,
                }}>
                  {defenders.reduce((a, c) => a + c.count, 0)} Total
                </span>
              </div>
              {defenders.length === 0 ? (
                <div style={{ fontSize: 11, color: '#64748b' }}>Zero predators observed</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {defenders.map((d, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                      <span style={{ fontWeight: 600, color: '#14532d', textTransform: 'capitalize' }}>
                        {d.name.replace(/_/g, ' ')}:
                      </span>
                      <span style={{ fontWeight: 700, color: '#166534' }}>
                        {d.count} <span style={{ fontSize: 9, color: '#64748b', fontWeight: 500 }}>({Math.round(d.confidence * 100)}%)</span>
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Plant Health & Symptoms */}
          <div style={{
            background: '#f8fafc', padding: '10px 14px', borderRadius: 8,
            border: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#475569' }}>PLANT HEALTH:</span>
              <span style={{
                fontSize: 11, fontWeight: 800,
                padding: '2px 8px', borderRadius: 4,
                background: currentHealthStyle.bg, color: currentHealthStyle.text,
                border: `1px solid ${currentHealthStyle.border}`,
                textTransform: 'uppercase',
              }}>
                {plantHealth.replace(/_/g, ' ')}
              </span>
            </div>

            {symptoms.length > 0 && (
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {symptoms.map((s, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: 10, fontWeight: 600,
                      background: '#e2e8f0', color: '#334155',
                      padding: '2px 6px', borderRadius: 4, textTransform: 'capitalize',
                    }}
                  >
                    {s.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
