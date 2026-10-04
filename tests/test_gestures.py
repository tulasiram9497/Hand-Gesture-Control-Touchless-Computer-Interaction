from src.vision.gesture_recognizer import (
    GestureRecognizer,
    detect_open_palm,
    detect_one_finger,
    detect_pinch,
    detect_thumbs_down,
    detect_thumbs_up,
    detect_two_fingers,
)


def _make_landmarks():
    return {
        "WRIST": (0.50, 0.90),
        "THUMB_CMC": (0.64, 0.76),
        "THUMB_MCP": (0.70, 0.67),
        "THUMB_IP": (0.75, 0.58),
        "THUMB_TIP": (0.73, 0.65),
        "INDEX_MCP": (0.40, 0.68),
        "INDEX_PIP": (0.39, 0.55),
        "INDEX_DIP": (0.39, 0.47),
        "INDEX_TIP": (0.38, 0.37),
        "MIDDLE_MCP": (0.50, 0.65),
        "MIDDLE_PIP": (0.50, 0.50),
        "MIDDLE_DIP": (0.50, 0.41),
        "MIDDLE_TIP": (0.50, 0.31),
        "RING_MCP": (0.60, 0.68),
        "RING_PIP": (0.60, 0.57),
        "RING_DIP": (0.61, 0.63),
        "RING_TIP": (0.61, 0.73),
        "PINKY_MCP": (0.68, 0.73),
        "PINKY_PIP": (0.69, 0.66),
        "PINKY_DIP": (0.70, 0.70),
        "PINKY_TIP": (0.70, 0.78),
    }


def test_detect_thumbs_up():
    landmarks = _make_landmarks()
    for key in ("INDEX_TIP", "MIDDLE_TIP", "RING_TIP", "PINKY_TIP"):
        landmarks[key] = (landmarks[key][0], 0.72)
    landmarks["THUMB_TIP"] = (0.73, 0.40)
    landmarks["THUMB_IP"] = (0.73, 0.56)
    result = detect_thumbs_up(landmarks)
    assert result["gesture"] == "THUMBS_UP"
    assert result["confidence"] > 0.7


def test_detect_two_fingers():
    landmarks = _make_landmarks()
    landmarks["THUMB_TIP"] = (0.70, 0.68)
    result = detect_two_fingers(landmarks)
    assert result["gesture"] == "TWO_FINGERS"
    assert result["active"] is True


def test_detect_open_palm():
    landmarks = _make_landmarks()
    landmarks["THUMB_TIP"] = (0.78, 0.43)
    landmarks["INDEX_TIP"] = (0.38, 0.28)
    landmarks["MIDDLE_TIP"] = (0.50, 0.22)
    landmarks["RING_TIP"] = (0.61, 0.31)
    landmarks["PINKY_TIP"] = (0.70, 0.43)
    result = detect_open_palm(landmarks)
    assert result["gesture"] == "OPEN_PALM"


def test_detect_one_finger():
    landmarks = _make_landmarks()
    landmarks["THUMB_TIP"] = (0.70, 0.68)
    landmarks["MIDDLE_TIP"] = (0.50, 0.72)
    result = detect_one_finger(landmarks)
    assert result["gesture"] == "ONE_FINGER"


def test_detect_pinch():
    landmarks = _make_landmarks()
    landmarks["THUMB_TIP"] = (0.40, 0.38)
    landmarks["INDEX_TIP"] = (0.405, 0.385)
    result = detect_pinch(landmarks)
    assert result["gesture"] == "PINCH"
    assert result["active"] is True


def test_detect_thumbs_down():
    landmarks = _make_landmarks()
    for key in ("INDEX_TIP", "MIDDLE_TIP", "RING_TIP", "PINKY_TIP"):
        landmarks[key] = (landmarks[key][0], 0.72)
    landmarks["THUMB_TIP"] = (0.73, 0.82)
    landmarks["THUMB_IP"] = (0.73, 0.65)
    assert detect_thumbs_down(landmarks)["gesture"] == "THUMBS_DOWN"


def test_recognize_vertical_hand_movement_from_mediapipe_landmarks():
    recognizer = GestureRecognizer(movement_threshold=0.02)
    landmarks = _make_landmarks()
    for key in ("INDEX_TIP", "MIDDLE_TIP", "RING_TIP", "PINKY_TIP"):
        landmarks[key] = (landmarks[key][0], 0.72)
    landmarks["THUMB_TIP"] = (0.70, 0.68)

    result = {"gesture": "NONE"}
    for offset in (0.0, -0.01, -0.02, -0.03, -0.04, -0.05, -0.06, -0.07, -0.08):
        moved = {key: value for key, value in landmarks.items()}
        moved["WRIST"] = (0.50, 0.90 + offset)
        moved["MIDDLE_MCP"] = (0.50, 0.65 + offset)
        result = recognizer.recognize(moved)

    assert result["gesture"] == "HAND_MOVING_UP"
    assert result["confidence"] > 0.0


def test_open_hand_lifting_is_reported_as_motion():
    recognizer = GestureRecognizer(movement_threshold=0.02)
    landmarks = _make_landmarks()
    landmarks.update({
        "THUMB_TIP": (0.78, 0.43),
        "INDEX_TIP": (0.38, 0.28),
        "MIDDLE_TIP": (0.50, 0.22),
        "RING_TIP": (0.61, 0.31),
        "PINKY_TIP": (0.70, 0.43),
    })

    result = {"gesture": "NONE"}
    for offset in (0.0, -0.01, -0.02, -0.03, -0.04, -0.05, -0.06, -0.07, -0.08):
        moved = {key: (x, y + offset) for key, (x, y) in landmarks.items()}
        result = recognizer.recognize(moved)

    assert result["gesture"] == "HAND_MOVING_UP"
