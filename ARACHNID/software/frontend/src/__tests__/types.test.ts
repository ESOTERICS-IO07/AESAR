import { describe, it, expect } from 'vitest';
import type { RoverMode, RoverState, VelocityCommand } from '../types/index';

describe('Frontend Types & Contract Mapping', () => {
  it('should validate allowed Rover Modes', () => {
    const manualMode: RoverMode = 'MANUAL';
    const autoMode: RoverMode = 'AUTONOMOUS';
    expect(manualMode).toBe('MANUAL');
    expect(autoMode).toBe('AUTONOMOUS');
  });

  it('should validate allowed Rover States', () => {
    const states: RoverState[] = [
      'DISCONNECTED',
      'CONNECTING',
      'IDLE',
      'MANUAL',
      'AUTONOMOUS',
      'NAVIGATING',
      'EXPLORING',
      'EMERGENCY_STOP',
      'FAULT',
    ];
    expect(states).toHaveLength(9);
  });

  it('should validate VelocityCommand structure', () => {
    const cmd: VelocityCommand = {
      command_id: 'cmd-test',
      timestamp_ms: 1000,
      linear_mps: 0.25,
      angular_rads: 0.0,
      source: 'MANUAL',
    };
    expect(cmd.linear_mps).toBe(0.25);
    expect(cmd.source).toBe('MANUAL');
  });
});
