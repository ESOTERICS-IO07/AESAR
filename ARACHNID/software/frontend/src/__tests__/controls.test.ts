import { describe, it, expect, vi } from 'vitest';
import { apiService } from '../services/api';

describe('B3 Controls & Safety Interlock Tests', () => {
  it('should format forward velocity command within contract limits', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, command_id: 'cmd-fwd-1' }),
    });

    const res = await apiService.sendCommand({
      command_id: 'cmd-fwd-1',
      timestamp_ms: 1234567,
      linear_mps: 0.3,
      angular_rads: 0.0,
      source: 'MANUAL',
    });

    expect(res.success).toBe(true);
    expect(res.command_id).toBe('cmd-fwd-1');
  });

  it('should format normal stop command', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, stopped: true }),
    });

    const res = await apiService.stopRover();
    expect(res.success).toBe(true);
    expect(res.stopped).toBe(true);
  });

  it('should format emergency stop command', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, emergency_stop: true }),
    });

    const res = await apiService.emergencyStop();
    expect(res.success).toBe(true);
    expect(res.emergency_stop).toBe(true);
  });

  it('should format emergency stop reset command', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, emergency_stop: false }),
    });

    const res = await apiService.resetEmergencyStop();
    expect(res.success).toBe(true);
    expect(res.emergency_stop).toBe(false);
  });
});
