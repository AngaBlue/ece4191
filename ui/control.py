import threading
import time
import pygame
import commands
from arcade_mix import arcade_mix, shape

# Control Loop Sample Rate
SAMPLE_RATE = 0.01

# Camera & brightness
BRIGHTNESS_STEP = 1
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 6

# Camera servo limits & rates (deg)
PAN_MIN = 0
PAN_MAX = 270
PAN_HOME = 135
TILT_MIN = 80
TILT_HOME = 135
TILT_MAX = 220
SERVO_RATE = 200 * SAMPLE_RATE  # deg per tick


def clamp(minimum, maximum, value):
    return min(max(value, minimum), maximum)


def control_loop(joystick: pygame.joystick.JoystickType,
                 state: dict,
                 stop_event: threading.Event):
    """
    Runs at SAMPLE_RATE in its own thread:
      - polls buttons/axes
      - sends commands.move and commands.camera
      - updates shared state (pan/tilt/brightness, screenshot flag)
    """
    num_buttons = joystick.get_numbuttons()
    button_state = [False] * num_buttons
    last_sample = 0.0

    # Local copies; publish to state as we change them
    brightness = state["brightness"]
    pan = state["pan"]
    tilt = state["tilt"]

    # Control-loop FPS measurement
    ticks = 0
    t0 = time.time()

    while not stop_event.is_set():
        now = time.time()
        if now - last_sample < SAMPLE_RATE:
            time.sleep(0.001)
            continue
        last_sample = now
        pygame.event.pump()

        # Buttons (rising-edge)
        for b in range(num_buttons):
            curr = joystick.get_button(b)
            prev = button_state[b]
            button_state[b] = curr
            if not curr or prev:
                continue

            match b:
                case 0:
                    state['screenshot_pending'] = True
                case 3:
                    state['visual_inferences'] = not state['visual_inferences']
                case 8:  # Reset angle
                    pan = 135
                    tilt = 135
                    commands.camera(pan, tilt)
                case 11:  # Snap up
                    pan = PAN_HOME
                    tilt = TILT_HOME + 45
                    commands.camera(pan, tilt)
                case 13:  # Snap left
                    pan = PAN_HOME + 90
                    tilt = TILT_HOME
                    commands.camera(pan, tilt)
                case 14:  # Snap right
                    pan = PAN_HOME - 90
                    tilt = TILT_HOME
                    commands.camera(pan, tilt)
                case 12:  # Snap down
                    pan = PAN_HOME
                    tilt = TILT_MIN
                    commands.camera(pan, tilt)
                case 9:  # Decrease brightness
                    brightness = max(
                        BRIGHTNESS_MIN, brightness - BRIGHTNESS_STEP)
                    commands.set_brightness(brightness)
                case 10:  # Increase brightness
                    brightness = min(
                        BRIGHTNESS_MAX, brightness + BRIGHTNESS_STEP)
                    commands.set_brightness(brightness)
                case _:
                    print(f"Unknown Button Press {b}")

        #  Drive (left stick)
        left_x = joystick.get_axis(0)
        left_y = -joystick.get_axis(1)
        left, right = arcade_mix(left_x, left_y)
        commands.move(left, right)

        # Camera (right stick)
        right_x = -joystick.get_axis(2)
        right_y = -joystick.get_axis(3)
        raw_pan, raw_tilt = shape(right_x), shape(right_y)
        if raw_pan != 0 or raw_tilt != 0:
            pan = clamp(PAN_MIN, PAN_MAX, pan + raw_pan * SERVO_RATE)
            tilt = clamp(TILT_MIN, TILT_MAX, tilt +
                         raw_tilt * SERVO_RATE)
            commands.camera(pan, tilt)

        # publish state for overlay
        state["brightness"] = brightness
        state["pan"] = pan
        state["tilt"] = tilt

        # control-loop FPS
        ticks += 1
        if now - t0 >= 1.0:
            state["control_hz"] = ticks / (now - t0)
            t0 = now
            ticks = 0
