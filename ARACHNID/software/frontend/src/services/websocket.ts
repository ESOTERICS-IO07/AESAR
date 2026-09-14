import { config } from '../config/index';
import type { ConnectionState, WebSocketEnvelope } from '../types/index';

export type WebSocketEventHandler<T = any> = (data: T, envelope: WebSocketEnvelope<T>) => void;
export type ConnectionStateChangeHandler = (state: ConnectionState, ageMs: number) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private state: ConnectionState = 'disconnected';
  private lastMessageTimestamp: number = 0;
  private listeners: Map<string, Set<WebSocketEventHandler>> = new Map();
  private stateListeners: Set<ConnectionStateChangeHandler> = new Set();
  private reconnectTimer: any = null;
  private stalenessTimer: any = null;
  private shouldReconnect: boolean = true;

  constructor(url: string = config.wsUrl) {
    this.url = url;
  }

  public setUrl(url: string): void {
    if (this.url !== url) {
      this.url = url;
      if (this.ws) {
        this.disconnect();
        this.connect();
      }
    }
  }

  public getUrl(): string {
    return this.url;
  }

  public getState(): ConnectionState {
    return this.state;
  }

  public getLastMessageTimestamp(): number {
    return this.lastMessageTimestamp;
  }

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.shouldReconnect = true;
    this.setState('connecting');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.setState('connected');
        this.lastMessageTimestamp = Date.now();
        this.startStalenessCheck();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          this.lastMessageTimestamp = Date.now();
          if (this.state === 'stale') {
            this.setState('connected');
          }
          const envelope: WebSocketEnvelope = JSON.parse(event.data);
          this.handleEnvelope(envelope);
        } catch (parseError) {
          console.warn('Failed to parse WebSocket message:', parseError);
        }
      };

      this.ws.onerror = () => {
        this.setState('error');
      };

      this.ws.onclose = () => {
        this.setState('disconnected');
        this.stopStalenessCheck();
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };
    } catch {
      this.setState('error');
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    }
  }

  public disconnect(): void {
    this.shouldReconnect = false;
    this.stopStalenessCheck();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setState('disconnected');
  }

  public subscribe<T = any>(eventType: string, handler: WebSocketEventHandler<T>): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);

    return () => {
      const handlers = this.listeners.get(eventType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  public onStateChange(handler: ConnectionStateChangeHandler): () => void {
    this.stateListeners.add(handler);
    handler(this.state, this.getConnectionAgeMs());
    return () => {
      this.stateListeners.delete(handler);
    };
  }

  public send(type: string, data: any = {}): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const envelope = {
        type,
        timestamp_ms: Date.now(),
        data,
      };
      this.ws.send(JSON.stringify(envelope));
    } else {
      console.warn('Cannot send message, WebSocket is not open.');
    }
  }

  public getConnectionAgeMs(): number {
    if (this.lastMessageTimestamp === 0) return -1;
    return Math.max(0, Date.now() - this.lastMessageTimestamp);
  }

  private handleEnvelope(envelope: WebSocketEnvelope): void {
    const handlers = this.listeners.get(envelope.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(envelope.data, envelope);
        } catch (handlerErr) {
          console.error(`Error in WebSocket event handler for ${envelope.type}:`, handlerErr);
        }
      });
    }

    // Also trigger wildcard subscribers if any
    const wildcardHandlers = this.listeners.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(envelope.data, envelope));
    }
  }

  private setState(newState: ConnectionState): void {
    this.state = newState;
    const age = this.getConnectionAgeMs();
    this.stateListeners.forEach((handler) => handler(newState, age));
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.shouldReconnect) {
        this.connect();
      }
    }, config.reconnectIntervalMs);
  }

  private startStalenessCheck(): void {
    this.stopStalenessCheck();
    this.stalenessTimer = setInterval(() => {
      if (this.state === 'connected' && this.lastMessageTimestamp > 0) {
        const age = Date.now() - this.lastMessageTimestamp;
        if (age > config.staleThresholdMs) {
          this.setState('stale');
        }
      }
    }, config.heartbeatIntervalMs);
  }

  private stopStalenessCheck(): void {
    if (this.stalenessTimer) {
      clearInterval(this.stalenessTimer);
      this.stalenessTimer = null;
    }
  }
}

export const wsService = new WebSocketService();
