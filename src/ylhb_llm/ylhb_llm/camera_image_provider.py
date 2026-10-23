import threading

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtQuick import QQuickImageProvider


class CameraImageProvider(QQuickImageProvider):
    """Serves the latest camera preview frame as ``image://camera/...``."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._lock = threading.Lock()
        self._image = QImage()

    def set_frame(self, image: QImage) -> None:
        with self._lock:
            self._image = image if image is not None else QImage()

    def clear(self) -> None:
        self.set_frame(QImage())

    def has_frame(self) -> bool:
        with self._lock:
            return not self._image.isNull()

    def requestImage(self, image_id, requested_size):
        with self._lock:
            image = self._image
        if image.isNull():
            image = QImage(1, 1, QImage.Format_RGB32)
            image.fill(QColor(Qt.black))
        if requested_size is not None and requested_size.isValid() and not requested_size.isEmpty():
            image = image.scaled(requested_size, Qt.KeepAspectRatio, Qt.FastTransformation)
        return image, QSize(image.width(), image.height())
