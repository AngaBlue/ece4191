from __future__ import annotations

import os
import time
import threading
import pygame
import numpy as np
from FrameBus import FrameBus, W as CAM_W, H as CAM_H
from ip import get_ip
from control import PAN_HOME, TILT_HOME, control_loop

# --- Settings ---
WINDOW_SCALE = 2.0    # scale camera view in window (1.0 = 640x480)
DRAW_FPS = 60         # target UI refresh rate (Hz)

IP = get_ip()
if IP == None:
    print("Could not find ESP32 IP")
    exit()
RTSP_URL = f"rtsp://{IP}/"
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def draw_text(surface, text, pos, font, color=(255, 255, 255), bg=None):
    img = font.render(text, True, color, bg)
    surface.blit(img, pos)


def draw_overlay(surface, font, info):
    banner = pygame.Surface((surface.get_width(), 80), pygame.SRCALPHA)
    banner.fill((0, 0, 0, 140))
    surface.blit(banner, (0, 0))
    x, y = 10, 8
    for line in info:
        draw_text(surface, line, (x, y), font)
        y += font.get_height() + 4


def save_screenshot(rgb_frame):
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"shot-{ts}.png")
    pygame.image.save(pygame.surfarray.make_surface(
        np.transpose(rgb_frame, (1, 0, 2))), path)
    print(f"[Screenshot] saved to {path}")


def main():
    pygame.init()
    pygame.joystick.init()
    pygame.display.set_caption("Robot Controller")

    if pygame.joystick.get_count() == 0:
        print("No controllers found")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Detected controller: {joystick.get_name()}")
    print("Press Ctrl+C or close window to exit...\n")

    # Video window
    win_w, win_h = int(CAM_W * WINDOW_SCALE), int(CAM_H * WINDOW_SCALE)
    screen = pygame.display.set_mode((win_w, win_h))
    font = pygame.font.Font(None, 24)

    # Shared state between threads
    state = {
        "brightness": 0,
        "pan": PAN_HOME,
        "tilt": TILT_HOME,
        "screenshot_pending": False,
        "control_hz": 0.0,
    }

    # FrameBus with subscription queue (frames received counter is based on q.gets)
    fb = FrameBus(RTSP_URL, debug=False)
    fb.start()

    # Start control thread (decoupled from drawing)
    stop_event = threading.Event()
    ctrl = threading.Thread(target=control_loop, args=(
        joystick, state, stop_event), daemon=True)
    ctrl.start()

    clock = pygame.time.Clock()

    try:
        while True:
            # Main thread handles window events only (drawing thread)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

            bgr = fb.latest()

            if bgr is not None:
                # BGR->RGB
                rgb = bgr[:, :, ::-1]
                last_rgb = rgb

                # Screenshot
                if state["screenshot_pending"]:
                    save_screenshot(last_rgb)
                    state["screenshot_pending"] = False

                # Blit
                surf = pygame.image.frombuffer(
                    rgb.tobytes(), (CAM_W, CAM_H), 'RGB')
                if WINDOW_SCALE != 1.0:
                    surf = pygame.transform.smoothscale(surf, (win_w, win_h))
                screen.blit(surf, (0, 0))

            cam_fps = fb.fps()

            # Overlay info
            info = [
                f"IP: {IP}",
                f"Cam FPS {cam_fps:4.1f} | Draw {clock.get_fps():4.1f} | Ctrl {state['control_hz']:4.1f}",
                f"Pan {int(state['pan']):3d}°  Tilt {int(state['tilt']):3d}°  Brightness {state['brightness']}",
            ]
            draw_overlay(screen, font, info)

            pygame.display.flip()
            clock.tick(DRAW_FPS)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        try:
            ctrl.join(timeout=1.0)
        except Exception:
            pass
        try:
            joystick.quit()
        except Exception:
            pass
        pygame.quit()


if __name__ == "__main__":
    main()
