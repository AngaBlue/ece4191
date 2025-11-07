

from config import DEADZONE, EXPO, K_TURN_SPEED, LEFT_GAIN, MIN_DUTY, QUICKTURN_THRESH, RIGHT_GAIN


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


def arcade_mix(raw_x: float, raw_y: float) -> tuple[float, float]:
    """Map joystick (x,y) to (left,right) track commands in [-1,1]."""
    v = shape(raw_y)
    w = shape(raw_x)

    quickturn = abs(v) < QUICKTURN_THRESH
    if not quickturn:
        # reduce turn authority as speed rises
        w *= (1.0 - K_TURN_SPEED * abs(v))

    left = v + w
    right = v - w

    # Normalise
    m = max(1.0, abs(left), abs(right))
    left /= m
    right /= m

    # Per-side gains
    left *= LEFT_GAIN
    right *= RIGHT_GAIN

    # Map into [+/-MIN_DUTY, +/-1]
    left = _apply_min_duty(left)
    right = _apply_min_duty(right)

    return left, right
