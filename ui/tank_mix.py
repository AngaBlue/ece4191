from config import DEADZONE, EXPO, LEFT_GAIN, MIN_DUTY, RIGHT_GAIN


def apply_deadzone(x: float) -> float:
    if abs(x) < DEADZONE:
        return 0.0
    s = 1.0 if x > 0 else -1.0
    return (abs(x) - DEADZONE) / (1.0 - DEADZONE) * s


def shape(x: float) -> float:
    x = apply_deadzone(x)
    return (1.0 - EXPO) * x + EXPO * (x ** 3)


def _apply_min_duty(x: float) -> float:
    if x == 0.0:
        return 0.0
    s = 1.0 if x > 0 else -1.0
    return s * (MIN_DUTY + (1.0 - MIN_DUTY) * abs(x))


def tank_mix(raw_left_y: float, raw_right_y: float) -> tuple[float, float]:
    """
    Map two joystick Y axes (left_y, right_y) directly to (left, right) track commands in [-1, 1].
    Positive Y = forward. If your device reports forward as negative, just pass -raw_y.
    """
    # Shape each stick independently
    left = shape(raw_left_y)
    right = shape(raw_right_y)

    # Per-side gains
    left *= LEFT_GAIN
    right *= RIGHT_GAIN

    # Clip to [-1, 1] before duty mapping
    left = max(-1.0, min(1.0, left))
    right = max(-1.0, min(1.0, right))

    # Map into [±MIN_DUTY, ±1] (preserve zero)
    left = _apply_min_duty(left)
    right = _apply_min_duty(right)

    return left, right
