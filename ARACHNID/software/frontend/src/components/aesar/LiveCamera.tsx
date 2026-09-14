import React, { useState, useEffect } from 'react';
import { useRover } from '../../hooks/useRover';
import { apiService } from '../../services/api';

export const LiveCamera: React.FC = () => {
  const { cameraStatus, updateCameraConfig, analyzeCurrentStation, aesarMode } = useRover();
  const [snapshotUrl, setSnapshotUrl] = useState<string>(apiService.getCameraSnapshotUrl());
  const [isLiveStreaming, setIsLiveStreaming] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(false);
  const [providerInput, setProviderInput] = useState<string>(cameraStatus?.provider || 'local');
  const [indexInput, setIndexInput] = useState<number>(cameraStatus?.camera_index ?? 0);
  const [snapshotInput, setSnapshotInput] = useState<string>(cameraStatus?.snapshot_url || '');
  const [isCapturing, setIsCapturing] = useState<boolean>(false);

  useEffect(() => {
    if (cameraStatus?.provider) setProviderInput(cameraStatus.provider);
    if (cameraStatus?.camera_index !== undefined && cameraStatus?.camera_index !== null) {
      setIndexInput(cameraStatus.camera_index);
    }
    if (cameraStatus?.snapshot_url) setSnapshotInput(cameraStatus.snapshot_url);
  }, [cameraStatus]);

  // Gentle periodic refresh ONLY when live streaming preview is explicitly enabled
  useEffect(() => {
    if (!isLiveStreaming) return;
    const interval = setInterval(() => {
      setSnapshotUrl(apiService.getCameraSnapshotUrl());
    }, 3000);
    return () => clearInterval(interval);
  }, [isLiveStreaming]);

  const handleManualCapture = async () => {
    setIsCapturing(true);
    setSnapshotUrl(apiService.getCameraSnapshotUrl());
    setTimeout(() => setIsCapturing(false), 500);
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateCameraConfig({
      provider: providerInput,
      local_camera_index: Number(indexInput),
      snapshot_url: snapshotInput,
      enabled: true,
    });
    setShowConfig(false);
    // Refresh frame immediately with new config
    setSnapshotUrl(apiService.getCameraSnapshotUrl());
  };

  const isOnline = cameraStatus?.state === 'online' || cameraStatus?.state === 'ready';
  const isUnavailable = cameraStatus?.state === 'camera_unavailable' || cameraStatus?.state === 'unavailable' || cameraStatus?.state === 'offline';

  const cameraSourceLabel = aesarMode === 'DEMO'
    ? 'Simulated Camera'
    : cameraStatus?.provider === 'local'
    ? `Laptop Webcam (Index ${cameraStatus.camera_index ?? 0})`
    : 'Phone IP Webcam';

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8', textTransform: 'uppercase' }}>
            Vision Feed
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', margin: 0 }}>
            {cameraSourceLabel}
          </h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Status badge */}
          <span style={{
            fontSize: 10, fontWeight: 700,
            padding: '3px 8px', borderRadius: 4,
            background: aesarMode === 'DEMO' ? '#f1f5f9' : isOnline ? '#dcfce7' : '#fee2e2',
            color: aesarMode === 'DEMO' ? '#475569' : isOnline ? '#15803d' : '#b91c1c',
            border: `1px solid ${aesarMode === 'DEMO' ? '#e2e8f0' : isOnline ? '#bbf7d0' : '#fecaca'}`,
          }}>
            {aesarMode === 'DEMO' ? 'SIMULATED CAMERA' : isUnavailable ? 'CAMERA UNAVAILABLE' : cameraStatus?.state?.toUpperCase() || 'STANDBY'}
          </span>

          {/* Config toggle */}
          <button
            onClick={() => setShowConfig(!showConfig)}
            style={{
              padding: '3px 8px', borderRadius: 4, border: '1px solid #cbd5e1',
              background: '#f8fafc', color: '#475569', fontSize: 11, fontWeight: 600, cursor: 'pointer',
            }}
          >
            ⚙ Source
          </button>
        </div>
      </div>

      {/* Camera Config Bar (collapsible) */}
      {showConfig && (
        <form onSubmit={handleSaveConfig} style={{
          background: '#f8fafc', padding: 12, borderRadius: 6,
          border: '1px solid #e2e8f0', marginBottom: 12,
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          <div>
            <label style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>CAMERA SOURCE PROVIDER:</label>
            <select
              value={providerInput}
              onChange={(e) => setProviderInput(e.target.value)}
              style={{
                width: '100%', padding: '6px 10px', fontSize: 12, borderRadius: 4,
                border: '1px solid #cbd5e1', background: '#ffffff', marginTop: 2,
              }}
            >
              <option value="local">Laptop Built-in Webcam (Local cv2)</option>
              <option value="http">Phone IP Webcam (HTTP Snapshot)</option>
              <option value="simulated">Simulated Synthetic Frames</option>
            </select>
          </div>

          {providerInput === 'local' && (
            <div>
              <label style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>LOCAL CAMERA INDEX (0 = default webcam):</label>
              <input
                type="number"
                min="0"
                max="5"
                value={indexInput}
                onChange={(e) => setIndexInput(parseInt(e.target.value, 10) || 0)}
                style={{
                  width: '100%', padding: '6px 10px', fontSize: 12, borderRadius: 4,
                  border: '1px solid #cbd5e1', background: '#ffffff', marginTop: 2,
                }}
              />
            </div>
          )}

          {providerInput === 'http' && (
            <div>
              <label style={{ fontSize: 10, fontWeight: 700, color: '#64748b' }}>PHONE SNAPSHOT URL:</label>
              <input
                type="text"
                placeholder="http://192.168.1.105:8080/shot.jpg"
                value={snapshotInput}
                onChange={(e) => setSnapshotInput(e.target.value)}
                style={{
                  width: '100%', padding: '6px 10px', fontSize: 12, borderRadius: 4,
                  border: '1px solid #cbd5e1', background: '#ffffff', marginTop: 2,
                }}
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
            <button
              type="button"
              onClick={() => setShowConfig(false)}
              style={{ padding: '4px 12px', fontSize: 11, borderRadius: 4, border: '1px solid #cbd5e1', background: '#fff' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ padding: '4px 12px', fontSize: 11, borderRadius: 4, border: 'none', background: '#15803d', color: '#fff', fontWeight: 600 }}
            >
              Save Camera Source
            </button>
          </div>
        </form>
      )}

      {/* Frame Container */}
      <div style={{
        position: 'relative', width: '100%', height: 260,
        background: '#090d16', borderRadius: 8, overflow: 'hidden',
        border: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <img
          src={snapshotUrl}
          alt="AESAR Scouting Frame"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480"><rect width="100%" height="100%" fill="%230f172a"/><text x="50%" y="50%" fill="%2364748b" font-family="sans-serif" font-size="16" text-anchor="middle">CAMERA UNAVAILABLE / STANDBY</text></svg>';
          }}
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />

        {/* Live HUD overlay */}
        <div style={{
          position: 'absolute', top: 10, left: 10,
          background: 'rgba(15,23,42,0.75)', backdropFilter: 'blur(4px)',
          color: '#ffffff', padding: '3px 8px', borderRadius: 4,
          fontSize: 10, fontWeight: 700, letterSpacing: '0.04em',
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: isLiveStreaming ? '#22c55e' : '#94a3b8' }} />
          {isLiveStreaming ? 'LIVE PREVIEW (3s)' : 'SINGLE-FRAME MODE'}
        </div>

        {isCapturing && (
          <div style={{
            position: 'absolute', inset: 0,
            background: 'rgba(255,255,255,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#0f172a' }}>Capturing Frame...</span>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
        <button
          onClick={handleManualCapture}
          style={{
            flex: 1, padding: '8px 14px', borderRadius: 6,
            border: '1px solid #cbd5e1', background: '#f8fafc',
            color: '#0f172a', fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}
        >
          🔄 Refresh Frame
        </button>
        <button
          onClick={() => setIsLiveStreaming(!isLiveStreaming)}
          style={{
            flex: 1, padding: '8px 14px', borderRadius: 6,
            border: '1px solid #cbd5e1', background: isLiveStreaming ? '#f1f5f9' : '#e2e8f0',
            color: '#334155', fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}
        >
          {isLiveStreaming ? '⏸ Pause Stream' : '▶ Live Preview'}
        </button>
        <button
          onClick={() => analyzeCurrentStation()}
          style={{
            flex: 1.2, padding: '8px 14px', borderRadius: 6,
            border: 'none', background: '#2563eb',
            color: '#ffffff', fontSize: 12, fontWeight: 700, cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
          }}
        >
          🔍 Analyze Frame
        </button>
      </div>
    </div>
  );
};
