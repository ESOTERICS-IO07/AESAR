"""ARACHNID Motor Bridge Serial Interface.

Handles UART/USB serial communication with Drive ESP32, including auto-reconnect,
error handling, and JSON packet dispatch strictly adhering to Contract v1.0.0.
"""

from typing import Any, Callable, Dict, Optional
import json
import time

try:
    import serial
except ImportError:
    serial = None


class SerialBridge:
    """Manages serial connection, auto-reconnect, and message transfer."""

    def __init__(
        self,
        port: str = "COM5",
        baudrate: int = 115200,
        timeout_s: float = 0.05,
        reconnect_interval_s: float = 2.0,
        mock_mode: bool = False,
        error_callback: Optional[Callable[[str, str, str, str], None]] = None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.reconnect_interval_s = reconnect_interval_s
        self.mock_mode = mock_mode
        self.error_callback = error_callback

        self.serial_conn: Optional[Any] = None
        self.is_connected = False
        self.last_reconnect_attempt = 0.0

        self.connect()

    def connect(self) -> bool:
        """Attempt connection to serial device."""
        if self.mock_mode:
            self.is_connected = True
            return True

        if serial is None:
            self._report_error(
                component="motor_bridge",
                code="NO_SERIAL_MODULE",
                severity="WARNING",
                message="pyserial not installed. Serial bridge running in mock mode.",
            )
            self.mock_mode = True
            self.is_connected = True
            return True

        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout_s,
            )
            self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            self.serial_conn = None
            self._report_error(
                component="motor_bridge",
                code="SERIAL_CONNECT_FAILED",
                severity="WARNING",
                message=f"Failed to connect to {self.port} at {self.baudrate} baud: {e}",
            )
            return False

    def send_packet(self, packet: Dict[str, Any]) -> bool:
        """Encode packet as JSON string and transmit over serial."""
        if self.mock_mode:
            return True

        if not self.is_connected or self.serial_conn is None:
            self._try_auto_reconnect()
            return False

        try:
            line = json.dumps(packet) + "\n"
            if hasattr(self.serial_conn, "is_open") and self.serial_conn.is_open:
                self.serial_conn.write(line.encode("utf-8"))
                return True
            else:
                self.is_connected = False
                return False
        except Exception as e:
            self.is_connected = False
            self._report_error(
                component="motor_bridge",
                code="SERIAL_WRITE_ERROR",
                severity="ERROR",
                message=f"Error writing to serial port: {e}",
            )
            return False

    def _try_auto_reconnect(self) -> None:
        """Periodically try to re-establish connection."""
        now = time.time()
        if now - self.last_reconnect_attempt >= self.reconnect_interval_s:
            self.last_reconnect_attempt = now
            self.connect()

    def _report_error(self, component: str, code: str, severity: str, message: str) -> None:
        if self.error_callback:
            self.error_callback(component, code, severity, message)

    def close(self) -> None:
        if self.serial_conn and hasattr(self.serial_conn, "is_open") and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.is_connected = False
