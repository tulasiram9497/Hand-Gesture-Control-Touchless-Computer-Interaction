import math
from typing import Iterable, Sequence, Tuple, Union

Point = Tuple[float, float]


def euclidean_distance(point_a: Point, point_b: Point) -> float:
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def normalize_point(point: Union[Sequence[float], Iterable[float]]) -> Point:
    if len(point) < 2:
        raise ValueError("Point requires at least x and y coordinates.")
    return float(point[0]), float(point[1])


def midpoint(point_a: Point, point_b: Point) -> Point:
    return ((point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0)


def map_to_screen(
    point: Point,
    width: int = 1920,
    height: int = 1080,
    dead_zone: float = 0.0,
) -> Point:
    x, y = point
    if dead_zone > 0.0:
        x = max(dead_zone, min(1.0 - dead_zone, x))
        y = max(dead_zone, min(1.0 - dead_zone, y))
    return int(round(x * width)), int(round(y * height))


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
