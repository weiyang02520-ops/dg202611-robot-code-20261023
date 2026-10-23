import pytest

from ylhb_llm.camera_preview import PreviewRateLimiter, image_to_qimage


def make_clock(values):
    iterator = iter(values)
    return lambda: next(iterator)


def test_rate_limiter_allows_first_frame_then_limits_to_max_hz():
    limiter = PreviewRateLimiter(5.0, clock=make_clock([0.0, 0.05, 0.19, 0.2, 0.25, 0.41]))

    assert [limiter.allow() for _ in range(6)] == [True, False, False, True, False, True]


def test_rate_limiter_keeps_average_rate_with_jittery_15hz_input():
    times = [index / 15.0 + (0.003 if index % 2 else -0.003) for index in range(1, 151)]
    limiter = PreviewRateLimiter(5.0, clock=make_clock(times))

    allowed = sum(limiter.allow() for _ in times)

    assert 48 <= allowed <= 51


def test_rate_limiter_reset_and_disabled_limit():
    limiter = PreviewRateLimiter(1.0, clock=make_clock([10.0, 10.1, 10.2]))
    assert limiter.allow() is True
    assert limiter.allow() is False
    limiter.reset()
    assert limiter.allow() is True

    unlimited = PreviewRateLimiter(0.0, clock=make_clock([1.0, 1.0, 1.0]))
    assert [unlimited.allow() for _ in range(3)] == [True, True, True]


def test_unsupported_or_inconsistent_images_return_none_without_qt():
    assert image_to_qimage(2, 1, 4, '16UC1', b'\x00' * 4) is None
    assert image_to_qimage(2, 1, 4, 'yuv422', b'\x00' * 4) is None
    assert image_to_qimage(0, 1, 0, 'rgb8', b'') is None
    assert image_to_qimage(2, 1, 5, 'rgb8', b'\x00' * 5) is None
    assert image_to_qimage(2, 2, 6, 'rgb8', b'\x00' * 11) is None


def pixel_rgb(image, x, y):
    from PyQt5.QtGui import QColor

    color = QColor(image.pixel(x, y))
    return color.red(), color.green(), color.blue()


@pytest.fixture
def qt_gui():
    pytest.importorskip('PyQt5.QtGui')
    from PyQt5.QtGui import QGuiApplication

    return QGuiApplication.instance() or QGuiApplication(['test'])


@pytest.mark.parametrize(
    ('encoding', 'pixels', 'bytes_per_pixel'),
    [
        ('bgra8', [bytes((30, 20, 10, 255)), bytes((60, 50, 40, 0))], 4),
        ('rgba8', [bytes((10, 20, 30, 255)), bytes((40, 50, 60, 0))], 4),
        ('bgr8', [bytes((30, 20, 10)), bytes((60, 50, 40))], 3),
        ('rgb8', [bytes((10, 20, 30)), bytes((40, 50, 60))], 3),
    ],
)
def test_color_encodings_convert_with_step_padding(qt_gui, encoding, pixels, bytes_per_pixel):
    padding = b'\xEE' * 3
    step = 2 * bytes_per_pixel + len(padding)
    row0 = pixels[0] + pixels[1] + padding
    row1 = pixels[1] + pixels[0] + padding
    data = bytearray(row0 + row1)

    image = image_to_qimage(2, 2, step, encoding, data)
    data[:] = b'\x00' * len(data)

    assert image is not None and not image.isNull()
    assert (image.width(), image.height()) == (2, 2)
    if bytes_per_pixel == 4:
        from PyQt5.QtGui import QImage

        assert image.format() == QImage.Format_RGB32
    assert pixel_rgb(image, 0, 0) == (10, 20, 30)
    assert pixel_rgb(image, 1, 0) == (40, 50, 60)
    assert pixel_rgb(image, 0, 1) == (40, 50, 60)
    assert pixel_rgb(image, 1, 1) == (10, 20, 30)


def test_mono8_converts_with_step_padding(qt_gui):
    data = bytes((0, 128, 255, 9, 9, 64, 200, 32, 9, 9))

    image = image_to_qimage(3, 2, 5, 'mono8', data)

    assert image is not None
    assert (image.width(), image.height()) == (3, 2)
    assert pixel_rgb(image, 0, 0) == (0, 0, 0)
    assert pixel_rgb(image, 1, 0) == (128, 128, 128)
    assert pixel_rgb(image, 2, 0) == (255, 255, 255)
    assert pixel_rgb(image, 0, 1) == (64, 64, 64)
    assert pixel_rgb(image, 2, 1) == (32, 32, 32)


def test_large_frames_are_downscaled_keeping_aspect(qt_gui):
    width, height = 1920, 1080
    data = bytes((0, 0, 255, 255)) * (width * height)

    image = image_to_qimage(width, height, width * 4, 'bgra8', data)
    small = image_to_qimage(width, height, width * 4, 'bgra8', data, max_width=480)

    assert (image.width(), image.height()) == (960, 540)
    assert (small.width(), small.height()) == (480, 270)
    assert pixel_rgb(image, 100, 100) == (255, 0, 0)


def test_frames_at_or_below_max_width_keep_size(qt_gui):
    data = bytes((1, 2, 3)) * (960 * 540)

    image = image_to_qimage(960, 540, 960 * 3, 'rgb8', data)

    assert (image.width(), image.height()) == (960, 540)
    assert pixel_rgb(image, 959, 539) == (1, 2, 3)
