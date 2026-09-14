import { config } from '../config/index';
import type {
  CommandResponse,
  EmergencyStopResponse,
  ExplorationData,
  HealthResponse,
  LogsResponse,
  MapData,
  ModeResponse,
  NavigationData,
  RoverMode,
  RoverStatus,
  StopResponse,
  Telemetry,
  VelocityCommand,
} from '../types/index';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = config.apiBaseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorBody = await response.json();
          if (errorBody && errorBody.detail) {
            errorMessage = typeof errorBody.detail === 'string' ? errorBody.detail : JSON.stringify(errorBody.detail);
          }
        } catch {
          // Ignore JSON parse errors on non-json error responses
        }
        throw new Error(errorMessage);
      }
      return (await response.json()) as T;
    } catch (err: any) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error(String(err));
    }
  }

  // 1. Health
  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // 2. Rover status
  public async getRoverStatus(): Promise<RoverStatus> {
    return this.request<RoverStatus>('/rover/status');
  }

  // 3. Rover telemetry
  public async getTelemetry(): Promise<Telemetry> {
    return this.request<Telemetry>('/rover/telemetry');
  }

  // 4. Mode
  public async setRoverMode(mode: RoverMode): Promise<ModeResponse> {
    return this.request<ModeResponse>('/rover/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
  }

  // 5. Velocity command
  public async sendCommand(command: VelocityCommand): Promise<CommandResponse> {
    return this.request<CommandResponse>('/rover/command', {
      method: 'POST',
      body: JSON.stringify(command),
    });
  }

  // 6. Stop
  public async stopRover(): Promise<StopResponse> {
    return this.request<StopResponse>('/rover/stop', {
      method: 'POST',
    });
  }

  // 7. Emergency stop
  public async emergencyStop(): Promise<EmergencyStopResponse> {
    return this.request<EmergencyStopResponse>('/rover/emergency-stop', {
      method: 'POST',
    });
  }

  // 8. Emergency stop reset
  public async resetEmergencyStop(): Promise<EmergencyStopResponse> {
    return this.request<EmergencyStopResponse>('/rover/emergency-stop/reset', {
      method: 'POST',
    });
  }

  // 9. Map
  public async getMap(): Promise<MapData> {
    return this.request<MapData>('/map');
  }

  // 10. Navigation
  public async getNavigation(): Promise<NavigationData> {
    return this.request<NavigationData>('/navigation');
  }

  // 11. Exploration
  public async getExploration(): Promise<ExplorationData> {
    return this.request<ExplorationData>('/exploration');
  }

  // 12. Logs
  public async getLogs(): Promise<LogsResponse> {
    return this.request<LogsResponse>('/logs');
  }

  // ─────────────────────────────────────────────────────────────
  // AESAR Agricultural Ecosystem Intelligence Endpoints
  // ─────────────────────────────────────────────────────────────

  // Environment
  public async getEnvironment(): Promise<any> {
    return this.request('/environment/current');
  }

  public async getEnvironmentCalibration(): Promise<any> {
    return this.request('/environment/calibration');
  }

  // Mode
  public async getAesarMode(): Promise<{ mode: 'LIVE' | 'DEMO'; description: string }> {
    return this.request('/mode');
  }

  public async setAesarMode(mode: 'LIVE' | 'DEMO'): Promise<{ mode: 'LIVE' | 'DEMO'; description: string }> {
    return this.request('/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
  }

  // Camera
  public async getCameraStatus(): Promise<any> {
    return this.request('/camera/status');
  }

  public async updateCameraConfig(config: any): Promise<any> {
    return this.request('/camera/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  public getCameraSnapshotUrl(): string {
    return `${this.baseUrl}/camera/snapshot?t=${Date.now()}`;
  }

  // Vision
  public async analyzeVision(imageBase64?: string, stationId?: number): Promise<any> {
    return this.request('/vision/analyze', {
      method: 'POST',
      body: JSON.stringify({ image_base64: imageBase64, station_id: stationId }),
    });
  }

  // AESA
  public async evaluateAesa(payload: any): Promise<any> {
    return this.request('/aesa/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Mission Controller
  public async getMissionStatus(): Promise<any> {
    return this.request('/mission/status');
  }

  public async startMission(plan?: any): Promise<any> {
    return this.request('/mission/start', {
      method: 'POST',
      body: plan ? JSON.stringify(plan) : undefined,
    });
  }

  public async pauseMission(): Promise<any> {
    return this.request('/mission/pause', {
      method: 'POST',
    });
  }

  public async resumeMission(): Promise<any> {
    return this.request('/mission/resume', {
      method: 'POST',
    });
  }

  public async abortMission(): Promise<any> {
    return this.request('/mission/abort', {
      method: 'POST',
    });
  }

  public async analyzeCurrentStation(): Promise<any> {
    return this.request('/mission/analyze-current', {
      method: 'POST',
    });
  }

  // Historical Data & Field Cards
  public async getMissions(): Promise<any[]> {
    return this.request('/missions');
  }

  public async getMission(id: string): Promise<any> {
    return this.request(`/missions/${id}`);
  }

  public async getMissionStations(id: string): Promise<any[]> {
    return this.request(`/missions/${id}/stations`);
  }

  public async getMissionFieldCard(id: string): Promise<any> {
    return this.request(`/missions/${id}/field-card`);
  }
}

export const apiService = new ApiService();

