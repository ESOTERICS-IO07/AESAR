import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiService } from '../services/api';

describe('ApiService', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with base URL', () => {
    expect(apiService.getBaseUrl()).toBeDefined();
    apiService.setBaseUrl('http://127.0.0.1:8100/api');
    expect(apiService.getBaseUrl()).toBe('http://127.0.0.1:8100/api');
  });

  it('should get health successfully', async () => {
    const mockHealth = { status: 'ok', backend: true, ros2_connected: true };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    });

    const res = await apiService.getHealth();
    expect(res).toEqual(mockHealth);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8100/api/health',
      expect.objectContaining({
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      })
    );
  });

  it('should get telemetry successfully', async () => {
    const mockTelemetry = {
      timestamp_ms: 1000,
      seq: 10,
      us_fl_mm: 1200,
      us_fr_mm: 950,
      us_l_mm: 760,
      us_r_mm: 1430,
      tof_front_mm: 880,
      sensor_status: { us_fl: 'OK', us_fr: 'OK', us_l: 'OK', us_r: 'OK', tof_front: 'OK' },
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockTelemetry,
    });

    const res = await apiService.getTelemetry();
    expect(res.us_fl_mm).toBe(1200);
    expect(res.tof_front_mm).toBe(880);
  });

  it('should send velocity command with correct contract payload', async () => {
    const mockCommand = {
      command_id: 'cmd-test-1',
      timestamp_ms: 123456,
      linear_mps: 0.3,
      angular_rads: 0.0,
      source: 'MANUAL' as const,
    };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, command_id: 'cmd-test-1' }),
    });

    const res = await apiService.sendCommand(mockCommand);
    expect(res.success).toBe(true);
    expect(res.command_id).toBe('cmd-test-1');
  });

  it('should trigger emergency stop', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, emergency_stop: true }),
    });

    const res = await apiService.emergencyStop();
    expect(res.success).toBe(true);
    expect(res.emergency_stop).toBe(true);
  });

  it('should reset emergency stop', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, emergency_stop: false }),
    });

    const res = await apiService.resetEmergencyStop();
    expect(res.success).toBe(true);
    expect(res.emergency_stop).toBe(false);
  });

  it('should handle HTTP errors gracefully', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      statusText: 'Conflict',
      json: async () => ({ detail: 'Rover is in EMERGENCY_STOP state' }),
    });

    await expect(
      apiService.sendCommand({
        command_id: 'cmd-err',
        timestamp_ms: 1000,
        linear_mps: 0.1,
        angular_rads: 0.0,
        source: 'MANUAL',
      })
    ).rejects.toThrow('Rover is in EMERGENCY_STOP state');
  });
});
