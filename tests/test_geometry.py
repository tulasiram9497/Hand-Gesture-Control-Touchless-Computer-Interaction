import math

from src.utils.geometry import euclidean_distance, map_to_screen


def test_euclidean_distance_basic():
    p1 = (0.0, 0.0)
    p2 = (3.0, 4.0)
    assert euclidean_distance(p1, p2) == 5.0


def test_map_to_screen_uses_resolution_and_dead_zone():
    result = map_to_screen((0.5, 0.5), width=1920, height=1080, dead_zone=0.05)
    assert result == (960, 540)

    result = map_to_screen((0.2, 0.2), width=1920, height=1080, dead_zone=0.1)
    assert result == (384, 216)
