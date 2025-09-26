# ---------------- Configurable Constants ----------------
DEADZONE = 0.05             # joystick deadzone (0.0–0.2 typical)
EXPO = 0.8                  # response shaping (0=linear, 1=very soft center)
K_TURN_SPEED = 1.0          # reduce turning at speed (0=none, 1=full)
QUICKTURN_THRESH = 0.10     # allow full spin when |forward| < threshold
LEFT_GAIN = 1.0             # scaling for left track (0.0–1.0)
RIGHT_GAIN = 1.0            # scaling for right track (0.0–1.0)
MIN_DUTY = 0.55             # minimum duty cycle to overcome stiction
TURN_AXIS_INVERT = -1.0     # set to -1.0 if your X axis is reversed, else 1.0
# flip turn when backing up to keep steering intuitive
REVERSE_TURN_WITH_REVERSE = True
# --------------------------------------------------------


def _apply_deadzone(x: float) -> float:
    if abs(x) < DEADZONE:
        return 0.0
    s = 1.0 if x > 0 else -1.0
    return (abs(x) - DEADZONE) / (1.0 - DEADZONE) * s


def _shape(x: float) -> float:
    x = _apply_deadzone(x)
    return (1.0 - EXPO) * x + EXPO * (x ** 3)


def _apply_min_duty(x: float) -> float:
    if x == 0.0:
        return 0.0
    s = 1.0 if x > 0 else -1.0
    return s * (MIN_DUTY + (1.0 - MIN_DUTY) * abs(x))


def arcade_mix(raw_x: float, raw_y: float) -> tuple[float, float]:
    """Map joystick (x,y) to (left,right) track commands in [-1,1]."""
    v = _shape(raw_y)                          # forward/back
    w = _shape(raw_x * TURN_AXIS_INVERT)       # turning

    quickturn = abs(v) < QUICKTURN_THRESH
    if not quickturn:
        # reduce turn authority as speed rises
        w *= (1.0 - K_TURN_SPEED * abs(v))
        # keep steering intuitive while reversing
        if REVERSE_TURN_WITH_REVERSE and v < 0.0:
            w = -w

    left = v + w
    right = v - w

    # Normalize
    m = max(1.0, abs(left), abs(right))
    left /= m
    right /= m

    # Per-side gains
    left *= LEFT_GAIN
    right *= RIGHT_GAIN

    # Map into [±MIN_DUTY, ±1]
    left = _apply_min_duty(left)
    right = _apply_min_duty(right)

    return left, right
