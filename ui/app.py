import os
import time
import threading
import pygame
import numpy as np
from FrameBus import FrameBus, W as CAM_W, H as CAM_H
from ip import get_ip
from control import control_loop
from config import DRAW_FPS, PAN_HOME, SCREENSHOT_DIR, TILT_HOME, WINDOW_SCALE
from yolo import draw_detections, yolo_loop
from audio import audio_loop

ip = get_ip()
if ip is None:
    print("Could not find ESP32 IP")
    exit(1)

rtsp_url = f"rtsp://{ip}/"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def draw_text(surface, text, pos, font, color=(255, 255, 255), bg=None):
    img = font.render(text, True, color, bg)
    surface.blit(img, pos)


def draw_overlay(surface, font, info):
    height = (font.get_height() + 4) * len(info) + 8
    banner = pygame.Surface((surface.get_width(), height), pygame.SRCALPHA)
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

    # Find Controller
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
        "visual_inferences": False,
        "det": None,
        "infer_hz": 0.0,
        "play_audio": True
    }

    # Start FrameBus
    fb = FrameBus(rtsp_url)
    fb.start()

    # Start control thread
    stop_event = threading.Event()
    ctrl = threading.Thread(target=control_loop, args=(
        joystick, state, stop_event), daemon=True)
    ctrl.start()

    # Start YOLO inference thread
    yolo_thr = threading.Thread(target=yolo_loop, args=(
        fb, state, stop_event), daemon=True)
    yolo_thr.start()

    # Start audio thread
    audio_thr = threading.Thread(target=audio_loop, args=(
        rtsp_url, state, stop_event), daemon=True)
    audio_thr.start()

    clock = pygame.time.Clock()
    last_rgb = None

    try:
        while True:
            # Main thread handles window events only (drawing thread)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

            # Get latest frame (non-blocking snapshot)
            bgr = fb.latest()
            if bgr is not None:
                rgb = bgr[:, :, ::-1]
                last_rgb = rgb

                # Screenshot
                if state["screenshot_pending"]:
                    save_screenshot(last_rgb)
                    state["screenshot_pending"] = False

                # Safe surface creation (copy) to avoid buffer lifetime issues
                surf = pygame.surfarray.make_surface(
                    np.transpose(rgb, (1, 0, 2)))
                if WINDOW_SCALE != 1.0:
                    surf = pygame.transform.smoothscale(surf, (win_w, win_h))
                screen.blit(surf, (0, 0))
            else:
                if last_rgb is None:
                    screen.fill((0, 0, 0))
                else:
                    # redraw last frame so screen never goes black between frames
                    surf = pygame.surfarray.make_surface(
                        np.transpose(last_rgb, (1, 0, 2)))
                    if WINDOW_SCALE != 1.0:
                        surf = pygame.transform.smoothscale(
                            surf, (win_w, win_h))
                    screen.blit(surf, (0, 0))

            # Draw detections (latest published; may lag behind the video)
            if state.get("visual_inferences", False):
                draw_detections(screen, state.get("det"), font)

            # Overlay info
            cam_fps = fb.fps()
            info = [
                f"IP {ip}",
                f"Cam FPS {cam_fps:4.1f} | Draw FPS {clock.get_fps():4.1f} | Control Rate {state['control_hz']:4.1f} | Infer FPS {state.get('infer_hz', 0.0):4.1f}",
                f"Pan {int(state['pan']):3d}° | Tilt {int(state['tilt']):3d}° | IR Brightness {state['brightness']}",
                f"Visual Inferences {'On' if state.get('visual_inferences') else 'Off'} | Playing Audio {'On' if state.get('play_audio') else 'Off'}",
            ]
            draw_overlay(screen, font, info)

            pygame.display.flip()
            clock.tick(DRAW_FPS)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        stop_event.set()
        try:
            ctrl.join(timeout=1.0)
        except Exception:
            pass
        try:
            yolo_thr.join(timeout=1.0)
        except Exception:
            pass
        try:
            joystick.quit()
        except Exception:
            pass
        pygame.quit()


if __name__ == "__main__":
    main()
