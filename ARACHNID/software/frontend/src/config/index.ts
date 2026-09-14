/**
 * ARACHNID Frontend Runtime Configuration
 * Canonical single source of truth for Backend REST and WebSocket addresses
 */

export interface AppConfig {
  apiBaseUrl: string;
  wsUrl: string;
  heartbeatIntervalMs: number;
  staleThresholdMs: number;
  reconnectIntervalMs: number;
}

const BACKEND_PORT = '8000';

const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && window.location) {
    const port = window.location.port === '5173' ? BACKEND_PORT : window.location.port || BACKEND_PORT;
    return `${window.location.protocol}//${window.location.hostname}:${port}/api`;
  }
  return `http://127.0.0.1:${BACKEND_PORT}/api`;
};

const getWsUrl = (): string => {
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const port = window.location.port === '5173' ? BACKEND_PORT : window.location.port || BACKEND_PORT;
    return `${protocol}//${window.location.hostname}:${port}/ws`;
  }
  return `ws://127.0.0.1:${BACKEND_PORT}/ws`;
};

export const config: AppConfig = {
  apiBaseUrl: getApiBaseUrl(),
  wsUrl: getWsUrl(),
  heartbeatIntervalMs: 1000,
  staleThresholdMs: 3000,
  reconnectIntervalMs: 2000,
};
