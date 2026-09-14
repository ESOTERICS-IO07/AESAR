import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';
import type {
  AesarMode,
  AESAStationAnalysis,
  CameraConfigRequest,
  CameraStatus,
  CommandSource,
  ConnectionState,
  EnvironmentData,
  ExplorationData,
  FieldAssessment,
  LogEntry,
  MapData,
  MissionStatusResponse,
  NavigationData,
  RoverMode,
  RoverStatus,
  StationObservationRecord,
  Telemetry,
  ToFScanData,
} from '../types/index';

interface RoverContextType {
  // Existing Rover Telemetry & Control
  status: RoverStatus;
  telemetry: Telemetry | null;
  tofScan: ToFScanData | null;
  mapData: MapData | null;
  navigationData: NavigationData | null;
  explorationData: ExplorationData | null;
  logs: LogEntry[];
  connectionState: ConnectionState;
  connectionAgeMs: number;
  isEmergencyStopped: boolean;
  setMode: (mode: RoverMode) => Promise<boolean>;
  sendCommand: (linear_mps: number, angular_rads: number, source?: CommandSource) => Promise<boolean>;
  stopRover: () => Promise<boolean>;
  triggerEmergencyStop: () => Promise<boolean>;
  resetEmergencyStop: () => Promise<boolean>;
  refreshStatus: () => Promise<void>;

  // AESAR Agricultural Ecosystem Intelligence
  aesarMode: AesarMode;
  toggleAesarMode: () => Promise<void>;
  environment: EnvironmentData | null;
  cameraStatus: CameraStatus | null;
  missionStatus: MissionStatusResponse | null;
  latestAesa: AESAStationAnalysis | null;
  latestObservation: StationObservationRecord | null;
  fieldAssessment: FieldAssessment | null;
  isFieldCardModalOpen: boolean;
  setFieldCardModalOpen: (open: boolean) => void;
  startMission: (plan?: any) => Promise<boolean>;
  pauseMission: () => Promise<boolean>;
  resumeMission: () => Promise<boolean>;
  abortMission: () => Promise<boolean>;
  analyzeCurrentStation: () => Promise<boolean>;
  updateCameraConfig: (config: CameraConfigRequest) => Promise<boolean>;
  refreshAesarData: () => Promise<void>;
}

const defaultStatus: RoverStatus = {
  connected: false,
  state: 'DISCONNECTED',
  mode: 'MANUAL',
  battery_percent: -1,
};

const defaultCameraStatus: CameraStatus = {
  connected: false,
  state: 'ready',
  enabled: true,
  stream_url: '',
  snapshot_url: '',
};

const defaultMissionStatus: MissionStatusResponse = {
  state: 'IDLE',
  current_station_index: 0,
  total_stations: 10,
  completed_stations: 0,
  remaining_stations: 10,
  observations: [],
};

const RoverContext = createContext<RoverContextType | undefined>(undefined);

export const RoverProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Rover base state
  const [status, setStatus] = useState<RoverStatus>(defaultStatus);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [tofScan, setTofScan] = useState<ToFScanData | null>(null);
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [navigationData, setNavigationData] = useState<NavigationData | null>(null);
  const [explorationData, setExplorationData] = useState<ExplorationData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [connectionAgeMs, setConnectionAgeMs] = useState<number>(-1);

  // AESAR intelligence state
  const [aesarMode, setAesarModeState] = useState<AesarMode>('DEMO');
  const [environment, setEnvironment] = useState<EnvironmentData | null>(null);
  const [cameraStatus, setCameraStatus] = useState<CameraStatus | null>(defaultCameraStatus);
  const [missionStatus, setMissionStatus] = useState<MissionStatusResponse | null>(defaultMissionStatus);
  const [latestAesa, setLatestAesa] = useState<AESAStationAnalysis | null>(null);
  const [latestObservation, setLatestObservation] = useState<StationObservationRecord | null>(null);
  const [fieldAssessment, setFieldAssessment] = useState<FieldAssessment | null>(null);
  const [isFieldCardModalOpen, setFieldCardModalOpen] = useState<boolean>(false);

  const isEmergencyStopped = status.state === 'EMERGENCY_STOP';

  // Poll baseline data
  const refreshStatus = useCallback(async () => {
    try {
      const [s, t, m, n, e, l] = await Promise.allSettled([
        apiService.getRoverStatus(),
        apiService.getTelemetry(),
        apiService.getMap(),
        apiService.getNavigation(),
        apiService.getExploration(),
        apiService.getLogs(),
      ]);

      if (s.status === 'fulfilled') setStatus(s.value);
      if (t.status === 'fulfilled') {
        setTelemetry(t.value);
        if (t.value.environment) setEnvironment(t.value.environment);
      }
      if (m.status === 'fulfilled') setMapData(m.value);
      if (n.status === 'fulfilled') setNavigationData(n.value);
      if (e.status === 'fulfilled') setExplorationData(e.value);
      if (l.status === 'fulfilled') setLogs(l.value.logs || []);
    } catch {
      // Ignored
    }
  }, []);

  const refreshAesarData = useCallback(async () => {
    try {
      const [modeRes, envRes, camRes, missRes] = await Promise.allSettled([
        apiService.getAesarMode(),
        apiService.getEnvironment(),
        apiService.getCameraStatus(),
        apiService.getMissionStatus(),
      ]);

      if (modeRes.status === 'fulfilled') setAesarModeState(modeRes.value.mode);
      if (envRes.status === 'fulfilled') setEnvironment(envRes.value);
      if (camRes.status === 'fulfilled') setCameraStatus(camRes.value);
      if (missRes.status === 'fulfilled') {
        const m = missRes.value;
        setMissionStatus(m);
        if (m.observations && m.observations.length > 0) {
          const last = m.observations[m.observations.length - 1];
          setLatestObservation(last);
          if (last.analysis) setLatestAesa(last.analysis);
        }
        if (m.field_assessment) setFieldAssessment(m.field_assessment);
      }
    } catch {
      // Ignored
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    refreshAesarData();
    wsService.connect();

    const unsubState = wsService.onStateChange((state, age) => {
      setConnectionState(state);
      setConnectionAgeMs(age);
    });

    const unsubRoverStatus = wsService.subscribe<RoverStatus>('rover_status', (data) => {
      setStatus((prev) => ({ ...prev, ...data }));
    });

    const unsubTelemetry = wsService.subscribe<Telemetry>('sensor_telemetry', (data) => {
      setTelemetry(data);
      if (data.environment) setEnvironment(data.environment);
    });

    const unsubTofScan = wsService.subscribe<ToFScanData>('tof_scan', (data) => {
      setTofScan(data);
    });

    const unsubBattery = wsService.subscribe<{ battery_percent: number }>('battery_update', (data) => {
      setStatus((prev) => ({ ...prev, battery_percent: data.battery_percent }));
    });

    const unsubMap = wsService.subscribe<MapData>('map_update', (data) => {
      setMapData(data);
    });

    const unsubNav = wsService.subscribe<NavigationData>('navigation_update', (data) => {
      setNavigationData(data);
    });

    const unsubExp = wsService.subscribe<ExplorationData>('exploration_update', (data) => {
      setExplorationData(data);
    });

    const unsubLogs = wsService.subscribe<LogEntry>('log_event', (data) => {
      setLogs((prev) => [...prev.slice(-499), data]);
    });

    const unsubSafety = wsService.subscribe<{ state: string }>('safety_event', (data) => {
      if (data.state === 'EMERGENCY_STOP') {
        setStatus((prev) => ({ ...prev, state: 'EMERGENCY_STOP' }));
      }
    });

    // AESAR-Specific WebSocket Streams
    const unsubAgri = wsService.subscribe<EnvironmentData>('agri_telemetry', (data) => {
      setEnvironment(data);
    });

    const unsubCamStatus = wsService.subscribe<CameraStatus>('camera_status', (data) => {
      setCameraStatus(data);
    });

    const unsubMission = wsService.subscribe<MissionStatusResponse>('mission_status', (data) => {
      setMissionStatus(data);
      if (data.observations && data.observations.length > 0) {
        const last = data.observations[data.observations.length - 1];
        setLatestObservation(last);
        if (last.analysis) setLatestAesa(last.analysis);
      }
      if (data.field_assessment) {
        setFieldAssessment(data.field_assessment);
      }
    });

    const unsubStationComp = wsService.subscribe<StationObservationRecord>('station_completed', (data) => {
      setLatestObservation(data);
      if (data.analysis) setLatestAesa(data.analysis);
      setMissionStatus((prev) => {
        if (!prev) return prev;
        const exists = prev.observations?.some((o) => o.station?.id === data.station?.id);
        const obsList = exists ? prev.observations : [...(prev.observations || []), data];
        return {
          ...prev,
          completed_stations: obsList ? obsList.length : prev.completed_stations + 1,
          remaining_stations: Math.max(0, prev.total_stations - (obsList ? obsList.length : prev.completed_stations + 1)),
          observations: obsList,
        };
      });
    });

    const unsubAesa = wsService.subscribe<AESAStationAnalysis>('aesa_update', (data) => {
      setLatestAesa(data);
    });

    const unsubFieldCard = wsService.subscribe<FieldAssessment>('field_card_generated', (data) => {
      setFieldAssessment(data);
      setFieldCardModalOpen(true);
    });

    return () => {
      unsubState();
      unsubRoverStatus();
      unsubTelemetry();
      unsubTofScan();
      unsubBattery();
      unsubMap();
      unsubNav();
      unsubExp();
      unsubLogs();
      unsubSafety();
      unsubAgri();
      unsubCamStatus();
      unsubMission();
      unsubStationComp();
      unsubAesa();
      unsubFieldCard();
      wsService.disconnect();
    };
  }, [refreshStatus, refreshAesarData]);

  // Mode toggling
  const toggleAesarMode = useCallback(async () => {
    const nextMode: AesarMode = aesarMode === 'DEMO' ? 'LIVE' : 'DEMO';
    try {
      const res = await apiService.setAesarMode(nextMode);
      setAesarModeState(res.mode);
      await refreshAesarData();
    } catch (err) {
      console.error('Failed to toggle AESAR mode:', err);
    }
  }, [aesarMode, refreshAesarData]);

  // Rover controls
  const setMode = useCallback(async (mode: RoverMode): Promise<boolean> => {
    try {
      const res = await apiService.setRoverMode(mode);
      if (res.success) {
        setStatus((prev) => ({ ...prev, mode: res.mode }));
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to change rover mode:', err);
      return false;
    }
  }, []);

  const sendCommand = useCallback(
    async (linear_mps: number, angular_rads: number, source: CommandSource = 'MANUAL'): Promise<boolean> => {
      if (status.state === 'EMERGENCY_STOP') {
        console.warn('Cannot send command while in EMERGENCY_STOP state');
        return false;
      }
      try {
        const cmd = {
          command_id: `cmd-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
          timestamp_ms: Date.now(),
          linear_mps,
          angular_rads,
          source,
        };
        const res = await apiService.sendCommand(cmd);
        return res.success;
      } catch (err) {
        console.error('Failed to send velocity command:', err);
        return false;
      }
    },
    [status.state]
  );

  const stopRover = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.stopRover();
      if (res.success) {
        setStatus((prev) => (prev.state !== 'EMERGENCY_STOP' ? { ...prev, state: 'IDLE' } : prev));
        return true;
      }
      return false;
    } catch (err) {
      console.error('Failed to normal stop:', err);
      return false;
    }
  }, []);

  const triggerEmergencyStop = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.emergencyStop();
      if (res.success) {
        setStatus((prev) => ({ ...prev, state: 'EMERGENCY_STOP' }));
        return true;
      }
      return false;
    } catch (err) {
      console.error('Emergency stop trigger failed:', err);
      return false;
    }
  }, []);

  const resetEmergencyStop = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.resetEmergencyStop();
      if (res.success) {
        setStatus((prev) => ({ ...prev, state: 'IDLE', mode: 'MANUAL' }));
        return true;
      }
      return false;
    } catch (err) {
      console.error('Emergency stop reset failed:', err);
      return false;
    }
  }, []);

  // AESAR Mission Actions
  const startMission = useCallback(async (plan?: any): Promise<boolean> => {
    try {
      const res = await apiService.startMission(plan);
      setMissionStatus(res);
      return true;
    } catch (err) {
      console.error('Failed to start mission:', err);
      return false;
    }
  }, []);

  const pauseMission = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.pauseMission();
      setMissionStatus(res);
      return true;
    } catch (err) {
      console.error('Failed to pause mission:', err);
      return false;
    }
  }, []);

  const resumeMission = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.resumeMission();
      setMissionStatus(res);
      return true;
    } catch (err) {
      console.error('Failed to resume mission:', err);
      return false;
    }
  }, []);

  const abortMission = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.abortMission();
      setMissionStatus(res);
      return true;
    } catch (err) {
      console.error('Failed to abort mission:', err);
      return false;
    }
  }, []);

  const analyzeCurrentStation = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiService.analyzeCurrentStation();
      setLatestObservation(res);
      if (res.analysis) setLatestAesa(res.analysis);
      return true;
    } catch (err) {
      console.error('Failed to analyze current station:', err);
      return false;
    }
  }, []);

  const updateCameraConfig = useCallback(async (config: CameraConfigRequest): Promise<boolean> => {
    try {
      const res = await apiService.updateCameraConfig(config);
      setCameraStatus(res);
      return true;
    } catch (err) {
      console.error('Failed to update camera config:', err);
      return false;
    }
  }, []);

  return (
    <RoverContext.Provider
      value={{
        status,
        telemetry,
        tofScan,
        mapData,
        navigationData,
        explorationData,
        logs,
        connectionState,
        connectionAgeMs,
        isEmergencyStopped,
        setMode,
        sendCommand,
        stopRover,
        triggerEmergencyStop,
        resetEmergencyStop,
        refreshStatus,
        aesarMode,
        toggleAesarMode,
        environment,
        cameraStatus,
        missionStatus,
        latestAesa,
        latestObservation,
        fieldAssessment,
        isFieldCardModalOpen,
        setFieldCardModalOpen,
        startMission,
        pauseMission,
        resumeMission,
        abortMission,
        analyzeCurrentStation,
        updateCameraConfig,
        refreshAesarData,
      }}
    >
      {children}
    </RoverContext.Provider>
  );
};

export const useRover = (): RoverContextType => {
  const context = useContext(RoverContext);
  if (!context) {
    throw new Error('useRover must be used within a RoverProvider');
  }
  return context;
};
