from typing import Iterable, List, Sequence, Tuple, Union


class ExponentialSmoother:
    def __init__(self, alpha: float = 0.2, initial: float | None = None) -> None:
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1.")
        self.alpha = alpha
        self.value = initial

    def update(self, new_value: float) -> float:
        if self.value is None:
            self.value = float(new_value)
            return self.value
        self.value = (self.alpha * float(new_value)) + ((1.0 - self.alpha) * self.value)
        return self.value


def smooth_point(
    previous: Tuple[float, float],
    current: Tuple[float, float],
    alpha: float = 0.5,
) -> Tuple[float, float]:
    return (
        (alpha * current[0]) + ((1.0 - alpha) * previous[0]),
        (alpha * current[1]) + ((1.0 - alpha) * previous[1]),
    )
