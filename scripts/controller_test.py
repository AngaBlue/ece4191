import pygame
import time
import commands
from ui.arcade_mix import arcade_mix, shape

# --- Settings ---
SAMPLE_RATE = 0.01

BRIGHTNESS_STEP = 1
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 6

PAN_MIN = 0
PAN_MAX = 270
PAN_HOME = 135
TILT_MIN = 80
TILT_HOME = 135
TILT_MAX = 220
SERVO_RATE = 200 * SAMPLE_RATE  # deg/s


def clamp(minimum, maximum, value):
    return min(max(value, minimum), maximum)


def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No controllers found")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Detected controller: {joystick.get_name()}")
    print("Press Ctrl+C to exit...\n")

    num_buttons = joystick.get_numbuttons()
    button_state = [False] * num_buttons

    brightness = 0  # 0–6
    pan = PAN_HOME
    tilt = TILT_HOME
    prev_brightness = brightness

    last_sample = 0

    try:
        while True:
            now = time.time()
            if now - last_sample < SAMPLE_RATE:
                continue

            last_sample = now
            pygame.event.pump()

            # --- Buttons ---
            for b in range(num_buttons):
                curr = joystick.get_button(b)
                prev = button_state[b]
                button_state[b] = curr
                if not curr or prev:
                    continue

                match b:
                    case 0:
                        print("Screenshot request queued")
                    case 8:  # Reset angle
                        pan = 135
                        tilt = 135
                        commands.camera(pan, tilt)
                        print("Camera reset to center")
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
                    case 10:  # Increase brightness
                        brightness = min(
                            BRIGHTNESS_MAX, brightness + BRIGHTNESS_STEP)
                    case _:
                        print(f"Unknown Button Press {b}")

                if brightness != prev_brightness:
                    print(f"Brightness: {brightness}")
                    commands.set_brightness(brightness)
                    prev_brightness = brightness

            # Movement Control
            left_x = -joystick.get_axis(0)
            left_y = -joystick.get_axis(1)

            left, right = arcade_mix(left_x, left_y)
            commands.move(left, right)

            # Camera Control
            right_x = -joystick.get_axis(2)
            right_y = -joystick.get_axis(3)

            raw_pan, raw_tilt = shape(right_x), shape(right_y)

            if raw_pan != 0 or raw_tilt != 0:
                pan = clamp(PAN_MIN, PAN_MAX, pan + raw_pan * SERVO_RATE)
                tilt = clamp(TILT_MIN, TILT_MAX, tilt + raw_tilt * SERVO_RATE)
                print(f"Pan: {pan:.0f}, Tilt: {tilt:.0f}")
                commands.camera(int(pan), int(tilt))

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        joystick.quit()
        pygame.quit()


if __name__ == "__main__":
    main()
