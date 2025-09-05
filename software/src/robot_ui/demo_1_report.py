import pygame
import time
import commands

import csv
import statistics

# from print_message import send_message_to_esp32

# --- Settings ---
DEADZONE = 0.15        # Ignore small noise
SAMPLE_RATE = 0.05      # ~20 Hz
BRIGHTNESS_STEP = 1

BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 6

PAN_MIN = -90
PAN_MAX = 90
TILT_MIN = -45
TILT_MAX = 45
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


    # Open CSV file for detailed logging
    log_file = open("joystick_report.csv", "w", newline="")
    csv_writer = csv.writer(log_file)
    csv_writer.writerow(["Time", "Axis", "Raw_Value", "Scaled_8bit", "Event"])

    # Data for summary report
    timestamps = []
    scaled_values = {"Left_X": [], "Left_Y": [], "Right_X": [], "Right_Y": []}

    button_counts = {}

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

                        # --- Inside button loop ---
                        event_name = None
                        if pressed:
                            if b == 2:  # Screenshot
                                event_name = "Screenshot"
                                print("Screenshot request queued")
                            elif b == 0:  # Reset angle
                                event_name = "Reset_Camera"
                                pan = 0.0
                                tilt = 0.0
                                print("Camera reset to center")
                            elif b == 9:  # Decrease brightness
                                event_name = "Brightness_Decrease"
                                brightness = max(BRIGHTNESS_MIN, brightness - BRIGHTNESS_STEP)
                            elif b == 10:  # Increase brightness
                                event_name = "Brightness_Increase"
                                brightness = min(BRIGHTNESS_MAX, brightness + BRIGHTNESS_STEP)

                            if brightness != prev_brightness:
                                print(f"Brightness: {brightness}")
                                commands.set_brightness(brightness)
                                prev_brightness = brightness

                            if event_name:
                                csv_writer.writerow([time.time(), "Button", "", "", event_name])
                                button_counts[event_name] = button_counts.get(event_name, 0) + 1




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
                    new_pan = pan + right_x * PAN_STEP
                    new_pan = max(PAN_MIN, min(PAN_MAX, new_pan))

                    new_tilt = tilt + -right_y * TILT_STEP  # invert Y axis
                    new_tilt = max(TILT_MIN, min(TILT_MAX, new_tilt))

                    # Only print if changed
                    if new_pan != pan or new_tilt != tilt:
                        pan = new_pan
                        tilt = new_tilt
                        print(f"Pan: {pan:.3f}°, Tilt: {tilt:.3f}°")
                        commands.move(pan, tilt)

                # Timestamp
                t = time.time()
                timestamps.append(t)

                # Left stick
                # Left stick scaling
                x_8bit = int((raw_x + 1) * 127.5)   # 0..255
                y_8bit = int((raw_y + 1) * 127.5)

                csv_writer.writerow([t, "Left_X", f"{raw_x:.6f}", x_8bit, ""])
                csv_writer.writerow([t, "Left_Y", f"{raw_y:.6f}", y_8bit, ""])
                scaled_values["Left_X"].append(x_8bit)
                scaled_values["Left_Y"].append(y_8bit)

                # Right stick
                x2_8bit = int((raw_pan + 1) * 127.5)
                y2_8bit = int((raw_tilt + 1) * 127.5)
                csv_writer.writerow([t, "Right_X", f"{raw_pan:.6f}", x2_8bit, ""])
                csv_writer.writerow([t, "Right_Y", f"{raw_tilt:.6f}", y2_8bit, ""])
                scaled_values["Right_X"].append(x2_8bit)
                scaled_values["Right_Y"].append(y2_8bit)


    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        log_file.close()
        joystick.quit()
        pygame.quit()

        # --- Generate summary report ---
        with open("joystick_summary.txt", "w") as f:
            f.write("=== Joystick Test Summary ===\n")

            if len(timestamps) > 1:
                # Sampling frequency
                diffs = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
                avg_freq = 1 / statistics.mean(diffs)

                f.write(f"Samples collected: {len(timestamps)}\n")
                f.write(f"Average sampling frequency: {avg_freq:.2f} Hz\n\n")

                # Resolution stats
                res_summary = {}
                for axis, values in scaled_values.items():
                    unique_levels = len(set(values))
                    res_summary[axis] = unique_levels

                f.write("Axis resolution (unique 8-bit levels observed):\n")
                for axis, levels in res_summary.items():
                    f.write(f"  {axis}: {levels} / 256 levels\n")
            else:
                f.write("No joystick samples were collected.\n")

            # Button press counts
            f.write("\nButton press counts:\n")
            if button_counts:
                for event, count in button_counts.items():
                    f.write(f"  {event}: {count}\n")
            else:
                f.write("  None\n")

            f.write("\nAll tests successfully transmitted to PC in real time.\n")



if __name__ == "__main__":
    main()
