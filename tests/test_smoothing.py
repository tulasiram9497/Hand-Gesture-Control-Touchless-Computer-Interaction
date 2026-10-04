from src.utils.smoothing import ExponentialSmoother, smooth_point


def test_smoothing_reduces_jitter():
    smoother = ExponentialSmoother(alpha=0.5)
    value = smoother.update(10)
    value2 = smoother.update(20)

    assert value == 10
    assert value2 == 15.0


def test_smooth_point_geometry():
    result = smooth_point((0, 0), (100, 100), alpha=0.5)
    assert result == (50.0, 50.0)
