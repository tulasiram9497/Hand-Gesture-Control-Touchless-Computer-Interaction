from dataclasses import dataclass, field


@dataclass
class CameraConfig:
    index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30


@dataclass
class ActivationConfig:
    hold_duration: float = 1.5
    inactive_after_seconds: float = 2.0


@dataclass
class GestureConfig:
    confidence_threshold: float = 0.75
    cooldown: float = 0.8
    pinch_threshold: float = 0.06
    volume_step: int = 5
    dead_zone: float = 0.02


@dataclass
class MouseConfig:
    sensitivity: float = 1.2
    smoothing: float = 0.35
    dead_zone: float = 0.02
    max_jump: float = 0.2


@dataclass
class PresentationConfig:
    next_key: str = "right"
    previous_key: str = "left"
    cooldown: float = 0.8


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    activation: ActivationConfig = field(default_factory=ActivationConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    presentation: PresentationConfig = field(default_factory=PresentationConfig)


CONFIG = AppConfig()
