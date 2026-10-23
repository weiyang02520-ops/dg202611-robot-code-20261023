import sys
import threading
import time
from typing import Any, Callable, Optional

DEFAULT_MAX_PREVIEW_WIDTH = 960

# encoding -> (bytes per pixel, QImage format used to wrap the raw bytes, swap red/blue)
_LITTLE_ENDIAN = sys.byteorder == 'little'
SUPPORTED_ENCODINGS = {
    'bgra8': (4, 'Format_ARGB32', False) if _LITTLE_ENDIAN else (4, 'Format_RGBA8888', True),
    'rgba8': (4, 'Format_RGBA8888', False),
    'bgr8': (3, 'Format_RGB888', True),
    'rgb8': (3, 'Format_RGB888', False),
    'mono8': (1, 'Format_Grayscale8', False),
}


def image_to_qimage(
    width: int,
    height: int,
    step: int,
    encoding: str,
    data: Any,
    max_width: int = DEFAULT_MAX_PREVIEW_WIDTH,
):
    """Convert raw sensor_msgs/Image fields into a QImage that owns its pixels.

    Returns None for unsupported encodings or inconsistent sizes.
    """
    spec = SUPPORTED_ENCODINGS.get(str(encoding or '').lower())
    if spec is None:
        return None
    bytes_per_pixel, format_name, swap_rb = spec
    width = int(width)
    height = int(height)
    step = int(step)
    if width <= 0 or height <= 0 or step < width * bytes_per_pixel:
        return None
    buffer = data if isinstance(data, bytes) else bytes(data)
    row_bytes = width * bytes_per_pixel
    if len(buffer) < step * (height - 1) + row_bytes:
        return None
    if bytes_per_pixel == 4 and step % 4:
        # 32-bit QImage formats require 4-byte aligned scanlines.
        buffer = b''.join(buffer[row * step:row * step + row_bytes] for row in range(height))
        step = row_bytes

    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QImage

    image = QImage(buffer, width, height, step, getattr(QImage, format_name))
    if image.isNull():
        return None
    owned = False
    if swap_rb:
        image = image.rgbSwapped()
        owned = True
    if bytes_per_pixel == 4:
        # Camera alpha is meaningless for display; RGB32 forces opaque pixels.
        image = image.convertToFormat(QImage.Format_RGB32)
        owned = True
    limit = max(1, int(max_width or DEFAULT_MAX_PREVIEW_WIDTH))
    if width > limit:
        scaled_height = max(1, round(height * limit / width))
        image = image.scaled(limit, scaled_height, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        owned = True
    return image if owned else image.copy()


class PreviewRateLimiter:
    """Allow at most ``max_hz`` events per second; ``max_hz <= 0`` disables limiting."""

    def __init__(self, max_hz: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_hz = float(max_hz)
        self.clock = clock
        self._lock = threading.Lock()
        self._next_due: Optional[float] = None

    @property
    def min_interval(self) -> float:
        return 1.0 / self.max_hz if self.max_hz > 0 else 0.0

    def reset(self) -> None:
        with self._lock:
            self._next_due = None

    def allow(self) -> bool:
        now = self.clock()
        interval = self.min_interval
        with self._lock:
            if self._next_due is not None and now < self._next_due:
                return False
            # Advance from the previous slot so input jitter does not lower the average rate.
            if self._next_due is None or now - self._next_due >= interval:
                self._next_due = now + interval
            else:
                self._next_due += interval
            return True
