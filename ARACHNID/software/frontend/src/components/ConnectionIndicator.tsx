import React from 'react';
import { Radio, AlertTriangle, WifiOff, RefreshCw } from 'lucide-react';
import type { ConnectionState } from '../types/index';

interface Props {
  state: ConnectionState;
  ageMs: number;
}

export const ConnectionIndicator: React.FC<Props> = ({ state, ageMs }) => {
  const getBadgeClass = () => {
    switch (state) {
      case 'connected':
        return 'badge-ok';
      case 'stale':
        return 'badge-warn';
      case 'connecting':
        return 'badge-warn';
      case 'disconnected':
      case 'error':
      default:
        return 'badge-danger';
    }
  };

  const getIcon = () => {
    switch (state) {
      case 'connected':
        return <Radio size={14} className="text-emerald-400" />;
      case 'stale':
        return <AlertTriangle size={14} className="text-amber-400" />;
      case 'connecting':
        return <RefreshCw size={14} className="animate-spin text-amber-400" />;
      case 'disconnected':
      case 'error':
      default:
        return <WifiOff size={14} className="text-rose-400" />;
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <div className={`badge ${getBadgeClass()}`} title={`Connection Age: ${ageMs >= 0 ? `${ageMs}ms` : 'N/A'}`}>
        {getIcon()}
        <span>{state.toUpperCase()}</span>
      </div>
      {ageMs >= 0 && state === 'connected' && (
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {ageMs < 1000 ? `${ageMs}ms` : `${(ageMs / 1000).toFixed(1)}s`}
        </span>
      )}
    </div>
  );
};
