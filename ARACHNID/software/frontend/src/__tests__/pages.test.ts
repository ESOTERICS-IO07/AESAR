import { describe, it, expect } from 'vitest';
import type {
  MapData,
  NavigationData,
  ExplorationData,
  SensorStatus,
  RoverStatus,
} from '../types/index';

describe('B3 Page Schemas & Logic Verification', () => {
  it('should validate MapData coordinate frame structure', () => {
    const map: MapData = {
      resolution_m_per_cell: 0.05,
      width: 20,
      height: 20,
      origin: { x: 0.0, y: 0.0 },
      data: new Array(400).fill(0),
    };
    expect(map.resolution_m_per_cell).toBe(0.05);
    expect(map.width).toBe(20);
    expect(map.height).toBe(20);
    expect(map.data.length).toBe(400);
  });

  it('should validate NavigationData waypoints structure', () => {
    const nav: NavigationData = {
      status: 'NAVIGATING',
      goal: { x: 5.0, y: 2.5 },
      path: [
        { x: 0.0, y: 0.0 },
        { x: 2.5, y: 1.25 },
        { x: 5.0, y: 2.5 },
      ],
    };
    expect(nav.status).toBe('NAVIGATING');
    expect(nav.goal?.x).toBe(5.0);
    expect(nav.path.length).toBe(3);
  });

  it('should validate ExplorationData frontier metrics', () => {
    const exp: ExplorationData = {
      status: 'EXPLORING',
      explored_percent: 42.5,
      frontier_count: 7,
      current_goal: { x: 3.2, y: 1.8 },
    };
    expect(exp.explored_percent).toBe(42.5);
    expect(exp.frontier_count).toBe(7);
    expect(exp.current_goal?.x).toBe(3.2);
  });

  it('should validate Sensor Status Enum mapping', () => {
    const statuses: SensorStatus[] = ['OK', 'TIMEOUT', 'OUT_OF_RANGE', 'DISCONNECTED', 'INVALID'];
    expect(statuses).toContain('OK');
    expect(statuses).toContain('TIMEOUT');
    expect(statuses).toContain('OUT_OF_RANGE');
    expect(statuses).toContain('DISCONNECTED');
    expect(statuses).toContain('INVALID');
  });

  it('should validate Emergency Stop Rover State', () => {
    const emergencyState: RoverStatus = {
      connected: true,
      state: 'EMERGENCY_STOP',
      mode: 'MANUAL',
      battery_percent: 85,
    };
    expect(emergencyState.state).toBe('EMERGENCY_STOP');
  });

  it('should validate Pose2D inside RoverStatus', () => {
    const stateWithPose: RoverStatus = {
      connected: true,
      state: 'AUTONOMOUS',
      mode: 'AUTONOMOUS',
      battery_percent: 90,
      pose: { x: 1.5, y: -2.0, theta: 3.14 }
    };
    expect(stateWithPose.pose?.x).toBe(1.5);
    expect(stateWithPose.pose?.y).toBe(-2.0);
    expect(stateWithPose.pose?.theta).toBe(3.14);
  });
});
