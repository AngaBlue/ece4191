from __future__ import annotations

import os
import time
import threading
import queue
import pygame
import numpy as np
from FrameBus import FrameBus, W as CAM_W, H as CAM_H
from ip import get_ip
from control import PAN_HOME, TILT_HOME, control_loop

# --- Settings ---
WINDOW_SCALE = 2.0    # scale camera view in window (1.0 = 640x480)
DRAW_FPS = 60         # target UI refresh rate (Hz)
SHOW_GRID = False

IP = get_ip()
RTSP_URL = os.environ.get("RTSP_URL", f"rtsp://{IP}/")
SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "screenshots")
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


def draw_grid(surface, step=40):
    w, h = surface.get_size()
    for x in range(0, w, step):
        pygame.draw.line(surface, (80, 80, 80), (x, 0), (x, h), 1)
    for y in range(0, h, step):
        pygame.draw.line(surface, (80, 80, 80), (0, y), (w, y), 1)


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
    q: queue.Queue = fb.subscribe(maxsize=2)  # drop old frames if UI lags

    # Camera FPS tracking (frames actually received)
    cam_frames = 0
    cam_t0 = time.time()
    cam_fps = 0.0

    # Last drawn frame (for screenshots)
    last_rgb = None

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

            # Try to get the newest frame without blocking UI
            frame = None
            while True:
                try:
                    f = q.get_nowait()
                    cam_frames += 1
                    frame = f
                except queue.Empty:
                    break

            if frame is not None:
                # BGR->RGB
                rgb = frame[:, :, ::-1]
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
            else:
                # No new frame this tick: keep previous pixels
                if last_rgb is None:
                    screen.fill((0, 0, 0))

            if SHOW_GRID:
                draw_grid(screen, step=40)

            # Update camera FPS from frames RECEIVED
            now = time.time()
            if now - cam_t0 >= 1.0:
                cam_fps = cam_frames / (now - cam_t0)
                cam_frames = 0
                cam_t0 = now

            # Overlay info
            info = [
                f"IP: {IP}",
                f"Cam FPS {cam_fps:4.1f} | Draw {clock.get_fps():4.1f} | Ctrl {state['control_hz']:4.1f}",
                f"Pan {int(state['pan']):3d}°  Tilt {int(state['tilt']):3d}°  Bright {state['brightness']}",
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
