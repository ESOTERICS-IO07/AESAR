from __future__ import annotations

import logging
import sys
import time
from collections import deque
from threading import Lock
from typing import List

from backend.models.schemas import LogEntry


class RoverLogger:
    """
    Structured application logging system for ARACHNID.
    Keeps an in-memory ring buffer of recent logs for REST API and WebSocket retrieval.
    """

    def __init__(self, max_entries: int = 500) -> None:
        self._entries: deque[LogEntry] = deque(maxlen=max_entries)
        self._lock = Lock()

        self._logger = logging.getLogger("arachnid")
        self._logger.setLevel(logging.DEBUG)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(message)s"
                )
            )
            self._logger.addHandler(handler)

    def _add(self, level: str, message: str) -> None:
        try:
            entry = LogEntry(
                timestamp_ms=int(time.time() * 1000),
                level=level,
                message=str(message),
            )

            with self._lock:
                self._entries.append(entry)

            log_method = getattr(self._logger, level.lower(), self._logger.info)
            log_method(message)
        except Exception:
            pass

    def debug(self, message: str) -> None:
        self._add("DEBUG", message)

    def info(self, message: str) -> None:
        self._add("INFO", message)

    def warning(self, message: str) -> None:
        self._add("WARNING", message)

    def error(self, message: str) -> None:
        self._add("ERROR", message)

    def get_logs(self) -> List[LogEntry]:
        with self._lock:
            return list(self._entries)
