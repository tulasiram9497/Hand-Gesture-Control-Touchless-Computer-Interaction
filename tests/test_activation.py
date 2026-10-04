from src.safety.activation_manager import ActivationManager


def test_activation_requires_open_palm_hold_time():
    manager = ActivationManager(hold_duration=1.5)

    manager.update("OPEN_PALM", elapsed=0.5)
    assert manager.is_active() is False

    manager.update("OPEN_PALM", elapsed=1.6)
    assert manager.is_active() is True

    manager.update("ONE_FINGER", elapsed=0.1)
    assert manager.is_active() is True

    manager.update("NO_HAND", elapsed=0.1)
    assert manager.is_active() is False


def test_unrecognized_tracking_times_out_to_inactive():
    manager = ActivationManager(hold_duration=0.1, inactive_after_seconds=0.2)
    manager.update("OPEN_PALM", elapsed=0.1)
    assert manager.is_active() is True

    manager.update("NONE", elapsed=0.1)
    assert manager.is_active() is True
    manager.update("NONE", elapsed=0.1)
    assert manager.is_active() is False
