import threading
import time
import pygame
import commands
from config import BRIGHTNESS_MAX, BRIGHTNESS_MIN, BRIGHTNESS_STEP, PAN_HOME, PAN_MAX, PAN_MIN, SAMPLE_RATE, SERVO_RATE, TILT_HOME, TILT_MAX, TILT_MIN
from tank_mix import tank_mix, shape


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
                case 0: # Take screenshot (x)
                    state['screenshot_pending'] = True
                case 2: # Toggle audio (square)
                    state['play_audio'] = not state['play_audio']
                case 3: # Toggle visual inferences (triangle)
                    state['visual_inferences'] = not state['visual_inferences']
                case 8:  # Reset angle (right stick in)
                    pan = 135
                    tilt = 135
                    commands.camera(pan, tilt)
                case 11:  # Snap up (up)
                    pan = PAN_HOME
                    tilt = TILT_HOME + 45
                    commands.camera(pan, tilt)
                case 13:  # Snap left (left)
                    pan = PAN_HOME + 90
                    tilt = TILT_HOME
                    commands.camera(pan, tilt)
                case 14:  # Snap right (right)
                    pan = PAN_HOME - 90
                    tilt = TILT_HOME
                    commands.camera(pan, tilt)
                case 12:  # Snap down (down)
                    pan = PAN_HOME
                    tilt = TILT_MIN
                    commands.camera(pan, tilt)
                case 9:  # Decrease brightness (left bumper)
                    brightness = max(
                        BRIGHTNESS_MIN, brightness - BRIGHTNESS_STEP)
                    commands.set_brightness(brightness)
                case 10:  # Increase brightness (right bumper)
                    brightness = min(
                        BRIGHTNESS_MAX, brightness + BRIGHTNESS_STEP)
                    commands.set_brightness(brightness)
                case _:
                    print(f"Unknown Button Press {b}")

        #  Drive (left stick)
        left_y = -joystick.get_axis(1)
        right_y = -joystick.get_axis(3)
        left, right = tank_mix(left_y, right_y)
        commands.move(left, right)

        # # Camera (right stick)
        # right_x = -joystick.get_axis(2)
        # right_y = -joystick.get_axis(3)
        # raw_pan, raw_tilt = shape(right_x), shape(right_y)
        # if raw_pan != 0 or raw_tilt != 0:
        #     pan = clamp(PAN_MIN, PAN_MAX, pan + raw_pan * SERVO_RATE)
        #     tilt = clamp(TILT_MIN, TILT_MAX, tilt +
        #                  raw_tilt * SERVO_RATE)
        #     commands.camera(pan, tilt)

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
