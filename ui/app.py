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

#==============================================================================================
def draw_yolo_slider(surface, state):
    """Draws a horizontal slider to control YOLO confidence threshold."""
    w, h = surface.get_size()
    slider_w, slider_h = 200, 8
    x, y = w // 2 - slider_w // 2, h - 60

    # Background bar
    pygame.draw.rect(surface, (80, 80, 80), (x, y, slider_w, slider_h), border_radius=4)

    # Handle position based on confidence
    conf = state.get("yolo_conf", 0.3)
    handle_x = int(x + conf * slider_w)
    pygame.draw.rect(surface, (0, 255, 128), (handle_x, y + slider_h // 2 - 5, 10, 10))
    #pygame.draw.rect(surface, (0, 255, 128), (handle_x, y + slider_h // 2 - 5, 10, 10), width=2)


    # Label
    font = pygame.font.Font(None, 24)
    draw_text(surface, f"YOLO Threshold: {conf:.2f}", (x + 15, y + 15), font)

# def draw_direction_buttons(surface, state):
#     """Draws buttons for drive and camera direction feedback."""
#     w, h = surface.get_size()

#     # Colors
#     inactive = (60, 60, 60)
#     active = (0, 200, 0)
#     arrow_color = (255, 255, 255)

#     font = pygame.font.Font(None, 24)

#     # Drive buttons (bottom left)
#     center_x, center_y = 80, h - 100
#     size = 30

#     directions = {
#         "forward": (center_x, center_y - size),
#         "backward": (center_x, center_y + size),
#         "left": (center_x - size, center_y),
#         "right": (center_x + size, center_y)
#     }

#     drive_dir = state.get("drive_dir", "none")
#     for name, (x, y) in directions.items():
#         color = active if drive_dir == name else inactive
#         pygame.draw.circle(surface, color, (x, y), 15)
#     draw_text(surface, "Drive", (center_x - 20, center_y + 50), pygame.font.Font(None, 24))

#     # Camera buttons (bottom right)
#     center_x, center_y = w - 80, h - 100
#     directions_cam = {
#         "up": (center_x, center_y - size),
#         "down": (center_x, center_y + size),
#         "left": (center_x - size, center_y),
#         "right": (center_x + size, center_y)
#     }

#     cam_dir = state.get("cam_dir", "none")
#     for name, (x, y) in directions_cam.items():
#         color = active if cam_dir == name else inactive
#         pygame.draw.circle(surface, color, (x, y), 15)
#     draw_text(surface, "Camera", (center_x - 30, center_y + 50), pygame.font.Font(None, 24))
def draw_direction_buttons(surface, state):
    """Draw circular buttons with arrow indicators for drive and camera control."""
    w, h = surface.get_size()

    inactive = (60, 60, 60)
    active = (0, 200, 0)
    arrow_color = (255, 255, 255)

    font = pygame.font.Font(None, 24)

    def draw_arrow(center, direction, color):
        cx, cy = center
        size = 10  # arrow size
        if direction == "up":
            points = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
        elif direction == "down":
            points = [(cx, cy + size), (cx - size, cy - size), (cx + size, cy - size)]
        elif direction == "left":
            points = [(cx - size, cy), (cx + size, cy - size), (cx + size, cy + size)]
        elif direction == "right":
            points = [(cx + size, cy), (cx - size, cy - size), (cx - size, cy + size)]
        pygame.draw.polygon(surface, color, points)

    def draw_button_group(center_x, center_y, label, active_dir, group_type):
        size = 35
        directions = {
            "up": (center_x, center_y - size),
            "down": (center_x, center_y + size),
            "left": (center_x - size, center_y),
            "right": (center_x + size, center_y)
        }

        for name, (x, y) in directions.items():
            color = active if active_dir == name else inactive
            #pygame.draw.circle(surface, color, (x, y), 20)
            pygame.draw.rect(surface, color, pygame.Rect(x-20, y-20, 40, 40), border_radius=10)
            pygame.draw.rect(surface, (0, 255, 128), pygame.Rect(x-20, y-20, 40, 40), width=2, border_radius=10)
            draw_arrow((x, y), name, arrow_color)

        draw_text(surface, label, (center_x - 25, center_y + size + 25), font)

    # Drive buttons (bottom left)
    drive_dir = state.get("drive_dir", "none")
    draw_button_group(90, h - 100, "Drive", drive_dir, "drive")

    # Camera buttons (bottom right)
    cam_dir = state.get("cam_dir", "none")
    draw_button_group(w - 90, h - 100, "Camera", cam_dir, "camera")

#==============================================================================================

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

    # Custom window size
    screen = pygame.display.set_mode((win_w, win_h))
    
    # Full screen window -- Hard to Close
    #screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    #win_w, win_h = screen.get_size()


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
        "yolo_conf": 0.3
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

    clock = pygame.time.Clock()
    last_rgb = None

    try:
        while True:
            # Main thread handles window events only (drawing thread)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION and event.buttons[0]:
                    mx, my = pygame.mouse.get_pos()
                    w, h = screen.get_size()
                    slider_w, slider_h = 200, 8
                    sx, sy = w // 2 - slider_w // 2, h - 60

                    # Check if mouse within slider vertical range
                    if sy - 10 <= my <= sy + 20:
                        conf = (mx - sx) / slider_w
                        conf = max(0.0, min(1.0, conf))
                        state["yolo_conf"] = conf


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

            # Draw direction indicators
            draw_direction_buttons(screen, state)

            # Draw YOLO confidence slider
            draw_yolo_slider(screen, state)

            # Draw detections (latest published; may lag behind the video)
            if state.get("visual_inferences", False):
                draw_detections(screen, state.get("det"), font)

            # Overlay info
            cam_fps = fb.fps()
            info = [
                f"IP {ip}",
                f"Cam FPS {cam_fps:4.1f} | Draw FPS {clock.get_fps():4.1f} | Control Rate {state['control_hz']:4.1f} | Infer FPS {state.get('infer_hz', 0.0):4.1f}",
                f"Pan {int(state['pan']):3d}° | Tilt {int(state['tilt']):3d}° | IR Brightness {state['brightness']}",
                f"Visual Inferences {'On' if state.get('visual_inferences') else 'Off'}",
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