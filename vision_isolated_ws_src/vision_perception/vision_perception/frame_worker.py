"""Single-slot latest-frame worker (no rclpy).

Busy replacement drops older pending frames and counts them. The capture
callback must not run inference.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional


class LatestFrameWorker:
    """One worker thread, pending_frames=1 semantics."""

    def __init__(
        self,
        process_fn: Callable[[Any], None],
        *,
        min_interval_sec: float = 0.0,
        name: str = "vision-detect-worker",
    ):
        self._process_fn = process_fn
        self._min_interval_sec = max(0.0, float(min_interval_sec))
        self._lock = threading.Lock()
        self._pending: Optional[Any] = None
        self._event = threading.Event()
        self._stop = threading.Event()
        self._finished = threading.Event()
        self._dropped = 0
        self._processed = 0
        self._last_error: Optional[str] = None
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)

    @property
    def dropped(self) -> int:
        with self._lock:
            return self._dropped

    @property
    def processed(self) -> int:
        with self._lock:
            return self._processed

    @property
    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> bool:
        """Request shutdown; False means the caller must retain shared resources."""
        self._stop.set()
        self._event.set()
        self._thread.join(timeout=timeout)
        return self._finished.is_set() and not self._thread.is_alive()

    def submit(self, item: Any) -> None:
        with self._lock:
            if self._stop.is_set():
                return
            if self._pending is not None:
                self._dropped += 1
            self._pending = item
            self._event.set()

    def clear_pending(self) -> int:
        """Drop any waiting frame (STALE / shutdown). Returns how many were cleared."""
        with self._lock:
            if self._pending is None:
                self._event.clear()
                return 0
            self._pending = None
            self._dropped += 1
            self._event.clear()
            return 1

    def _take(self) -> Optional[Any]:
        with self._lock:
            item = self._pending
            self._pending = None
            if item is None:
                self._event.clear()
            return item

    def _run(self) -> None:
        try:
            self._run_frames()
        finally:
            self._finished.set()

    def _run_frames(self) -> None:
        last_start = 0.0
        while not self._stop.is_set():
            self._event.wait(timeout=0.1)
            if self._stop.is_set():
                break
            if self._min_interval_sec > 0.0:
                now = time.monotonic()
                wait = self._min_interval_sec - (now - last_start)
                if wait > 0 and self._stop.wait(wait):
                    break
            # Keep the slot replaceable throughout rate limiting, then take
            # the newest frame rather than aging an already removed frame.
            item = self._take()
            if item is None or self._stop.is_set():
                continue
            last_start = time.monotonic()
            try:
                self._process_fn(item)
                with self._lock:
                    self._processed += 1
                    self._last_error = None
            except Exception as exc:  # noqa: BLE001 - isolate worker failures
                with self._lock:
                    self._last_error = str(exc)
