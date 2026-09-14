import { describe, it, expect, vi, beforeEach } from 'vitest';
import { wsService } from '../services/websocket';

describe('WebSocketService', () => {
  beforeEach(() => {
    wsService.disconnect();
  });

  it('should initialize with configured URL', () => {
    expect(wsService.getUrl()).toBeDefined();
    expect(wsService.getState()).toBe('disconnected');
  });

  it('should allow subscribing to specific event types', () => {
    const handler = vi.fn();
    const unsubscribe = wsService.subscribe('sensor_telemetry', handler);
    expect(typeof unsubscribe).toBe('function');
    unsubscribe();
  });

  it('should track state listeners', () => {
    const stateHandler = vi.fn();
    const unsubscribe = wsService.onStateChange(stateHandler);
    expect(stateHandler).toHaveBeenCalledWith('disconnected', -1);
    unsubscribe();
  });

  it('should calculate connection age correctly', () => {
    expect(wsService.getConnectionAgeMs()).toBe(-1);
  });
});
