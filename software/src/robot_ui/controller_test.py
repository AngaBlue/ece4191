import pygame
import time
import commands

# from print_message import send_message_to_esp32

# --- Settings ---
DEADZONE = 0.15        # Ignore small noise
SAMPLE_RATE = 0.05      # ~20 Hz
BRIGHTNESS_STEP = 1

BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 6

PAN_MIN = 0
PAN_MAX = 270
TILT_MIN = 0
TILT_MAX = 270
PAN_STEP = 2
TILT_STEP = 2

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
    prev_buttons = [None] * num_buttons

    brightness = 0  # 0–6
    pan = 0.0
    tilt = 0.0
    prev_brightness = brightness

    last_sample = 0

    try:
        while True:
            now = time.time()
            if now - last_sample >= SAMPLE_RATE:
                last_sample = now
                pygame.event.pump()

                # --- Buttons ---
                for b in range(num_buttons):
                    pressed = joystick.get_button(b)
                    if prev_buttons[b] is None or pressed != prev_buttons[b]:
                        prev_buttons[b] = pressed

                        if pressed:
                            if b == 2:  # Screenshot
                                print("Screenshot request queued")
                            elif b == 0:  # Reset angle
                                pan = 0.0
                                tilt = 0.0
                                print("Camera reset to center")
                            elif b == 9:  # Decrease brightness
                                # send_message_to_esp32("Decreased brightness!")
                                brightness = max(BRIGHTNESS_MIN, brightness - BRIGHTNESS_STEP)
                            elif b == 10:  # Increase brightness
                                brightness = min(BRIGHTNESS_MAX, brightness + BRIGHTNESS_STEP)
                                # send_message_to_esp32("Increased brightness!")    

                            if brightness != prev_brightness:
                                print(f"Brightness: {brightness}")
                                commands.set_brightness(brightness)
                                prev_brightness = brightness


                # --- Left stick robot control ---
                raw_x = joystick.get_axis(0)  # left stick horizontal
                raw_y = joystick.get_axis(1)  # left stick vertical

                # Apply deadzone
                left_x = 0.0 if abs(raw_x) < DEADZONE else raw_x
                left_y = 0.0 if abs(raw_y) < DEADZONE else raw_y

                # Convert to robot motion
                # Forward/backward: negative Y (up is -1 in pygame)
                translation = -left_y   # forward/backward
                rotation = left_x       # left/right turn

                # Only print if there is meaningful motion
                if translation != 0.0 or rotation != 0.0:
                    print(f"Robot move -> Translation: {translation:.3f}, Rotation: {rotation:.3f}")

                commands.move(translation, rotation)

                # --- Right stick camera control only ---
                raw_pan = joystick.get_axis(2)   # right stick horizontal
                raw_tilt = joystick.get_axis(3)  # right stick vertical

                # Deadzone
                right_x = 0.0 if abs(raw_pan) < DEADZONE else raw_pan
                right_y = 0.0 if abs(raw_tilt) < DEADZONE else raw_tilt

                # Update pan/tilt if meaningful movement
                if right_x != 0.0 or right_y != 0.0:
                    new_pan = int(pan + right_x * PAN_STEP)
                    new_pan = max(PAN_MIN, min(PAN_MAX, new_pan))

                    new_tilt = int(tilt + -right_y * TILT_STEP)  # invert Y axis
                    new_tilt = max(TILT_MIN, min(TILT_MAX, new_tilt))

                    # Only print if changed
                    if new_pan != pan or new_tilt != tilt:
                        pan = new_pan
                        tilt = new_tilt
                        print(f"Pan: {pan:d}, Tilt: {tilt:d}")
                        commands.camera(pan, tilt)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        joystick.quit()
        pygame.quit()

if __name__ == "__main__":
    main()
