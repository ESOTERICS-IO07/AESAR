import React from 'react';
import { useRover } from '../../hooks/useRover';

export const EnvironmentSection: React.FC = () => {
  const { environment, telemetry } = useRover();

  // Pick up environmental reading from environment state or telemetry
  const env = environment || telemetry?.environment;

  const isAvail = Boolean(env && env.available);
  const tempStr = isAvail && env?.temperature_c != null ? `${env.temperature_c.toFixed(1)}°C` : '--';
  const humStr = isAvail && env?.humidity_percent != null ? `${env.humidity_percent.toFixed(1)}%` : '--';
  const soilPctStr = isAvail && env?.soil_moisture_percent != null ? `${env.soil_moisture_percent.toFixed(1)}%` : '--';
  const soilRawStr = isAvail && env?.soil_moisture_raw != null ? `ADC: ${env.soil_moisture_raw}` : 'ADC: --';

  const statusLabel = isAvail ? 'AVAILABLE' : (env?.status?.toUpperCase() || 'SENSOR OFFLINE');
  const statusColor = isAvail ? '#15803d' : '#991b1b';
  const statusBg = isAvail ? '#dcfce7' : '#fee2e2';

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: 10,
      padding: '16px 20px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8', textTransform: 'uppercase' }}>
            Micro-Climate Telemetry
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', margin: 0 }}>
            Environmental Sensors
          </h2>
        </div>

        <div style={{
          fontSize: 10, fontWeight: 700,
          padding: '3px 8px', borderRadius: 4,
          background: statusBg, color: statusColor,
          border: `1px solid ${isAvail ? '#bbf7d0' : '#fecaca'}`,
        }}>
          {statusLabel}
        </div>
      </div>

      {/* Sensor 3-Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 12,
      }}>
        {/* Temperature */}
        <div style={{
          background: '#f8fafc', padding: '12px 14px', borderRadius: 8,
          border: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>TEMPERATURE</span>
            <span style={{ fontSize: 14 }}>🌡️</span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {tempStr}
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8' }}>
            DHT22 sensor · Optimal 18-28°C
          </div>
        </div>

        {/* Humidity */}
        <div style={{
          background: '#f8fafc', padding: '12px 14px', borderRadius: 8,
          border: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>HUMIDITY</span>
            <span style={{ fontSize: 14 }}>💧</span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {humStr}
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8' }}>
            Relative humidity · Optimal 50-70%
          </div>
        </div>

        {/* Soil Moisture */}
        <div style={{
          background: '#f8fafc', padding: '12px 14px', borderRadius: 8,
          border: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>SOIL MOISTURE</span>
            <span style={{ fontSize: 14 }}>🌱</span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {soilPctStr}
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8' }}>
            {soilRawStr} (Calibrated)
          </div>
        </div>
      </div>
    </div>
  );
};
