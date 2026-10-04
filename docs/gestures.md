# Supported Gestures

## 1. Open Palm

Purpose: activation and safety gate.

Logic:

- the thumb and fingers are spread and not curled inward
- the system measures the relative separation from the palm center
- the open palm must remain visible for roughly 1.5 seconds

## 2. Thumbs Up

Purpose: increase system volume.

Logic:

- thumb tip sits above the thumb base and is lifted relative to the palm
- the user holds a controlled upward thumb position
- confidence threshold ensures robust detection

## 3. Thumbs Down

Purpose: decrease system volume.

Logic:

- thumb tip is pointed downward relative to the thumb base
- the gesture is classified only when the angle and relative position are consistent

## 4. One Finger

Purpose: previous slide.

Logic:

- index finger is extended while the remaining fingers are not dominant
- only one gesture event is triggered per cooldown window

## 5. Two Fingers

Purpose: next slide.

Logic:

- index and middle fingers are extended
- ring and pinky are not treated as active extension states
- action is debounced to prevent repeated triggers

## 6. Pinch

Purpose: simulate a click or select action.

Logic:

- thumb tip and index fingertip are close together
- pinch distance is measured in normalized coordinates
- cooldown prevents repeated click spam

## 7. Index Movement

Purpose: pointer control.

Logic:

- the user moves the index fingertip across the frame
- the pointer position is remapped to screen space
- smoothing reduces jitter and stabilizes control

## Vertical Hand Movement Reading

The recognizer also reports `HAND_MOVING_UP` and `HAND_MOVING_DOWN` when the palm center shifts vertically across a short rolling window. This is a live diagnostic reading; it does not issue a desktop command or change volume. Keep the hand visible and move it deliberately for the reading to appear.

## Geometric approach

The recognition layer favors relative position and geometric consistency rather than raw coordinate dependence. That includes:

- fingertip-to-palm center distances
- relative finger direction
- joint spacing
- pinch distance
- activation hold time
- smoothing for pointer motion

This design keeps the gesture logic more resilient and easier to tune without hard-coded values scattered through the project.
