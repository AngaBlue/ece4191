import threading
import time
import pygame
from ultralytics import YOLO
from FrameBus import FrameBus
from config import CLASS_NAMES, WINDOW_SCALE, YOLO_CONF, YOLO_IOU, YOLO_MODEL


def _color_for_class(cid: int) -> tuple[int, int, int]:
    rng = (37 * (cid + 1)) % 255
    return (50 + (rng * 3) % 205, 50 + (rng * 5) % 205, 50 + (rng * 7) % 205)


def draw_detections(surface: pygame.Surface, det: dict | None, font: pygame.font.Font):
    if not det:
        return
    boxes = det.get("boxes")
    clss = det.get("cls")
    confs = det.get("conf")
    if boxes is None:
        return
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box  # coords at camera resolution
        sx1, sy1 = int(x1 * WINDOW_SCALE), int(y1 * WINDOW_SCALE)
        sx2, sy2 = int(x2 * WINDOW_SCALE), int(y2 * WINDOW_SCALE)
        w, h = sx2 - sx1, sy2 - sy1
        cid = int(clss[i]) if clss is not None and len(clss) > i else -1
        conf = float(confs[i]) if confs is not None and len(confs) > i else 0.0
        name = CLASS_NAMES[cid]
        color = _color_for_class(cid if cid >= 0 else 0)
        pygame.draw.rect(surface, color, pygame.Rect(sx1, sy1, w, h), width=2)
        label = f"{name} {conf:.2f}"
        # Draw label box
        text_img = font.render(label, True, (255, 255, 255))
        pad = 2
        bg = pygame.Surface((text_img.get_width() + pad*2,
                            text_img.get_height() + pad*2))
        bg.fill(color)
        surface.blit(bg, (sx1, max(0, sy1 - bg.get_height())))
        surface.blit(
            text_img, (sx1 + pad, max(0, sy1 - bg.get_height()) + pad))


def yolo_loop(fb: FrameBus, state: dict, stop_event: threading.Event):
    try:
        model = YOLO(YOLO_MODEL)
        state["visual_inferences"] = True
    except Exception as e:
        print(f"[YOLO] failed to load model '{YOLO_MODEL}': {e}")
        state["visual_inferences"] = False
        return

    frames = 0
    t0 = time.time()

    while not stop_event.is_set():
        if not state["visual_inferences"]:
            time.sleep(0.01)
            continue

        frame = fb.latest()

        if frame is None:
            continue

        try:
            results = model.predict(
                source=frame,
                verbose=False,
                conf=YOLO_CONF,
                iou=YOLO_IOU
            )
            r = results[0]

            if r.boxes is None:
                continue

            # Extract boxes, classes, confidences
            xyxy = r.boxes.xyxy.cpu().numpy()  # type: ignore
            clss = r.boxes.cls.cpu().numpy()  # type: ignore
            conf = r.boxes.conf.cpu().numpy()  # type: ignore

            state["det"] = {
                "boxes": xyxy.tolist(),
                "cls":   clss.tolist(),
                "conf":  conf.tolist(),
                "t":     time.time(),
            }

            # inference fps (1s windows)
            frames += 1
            now = time.time()
            if now - t0 >= 1.0:
                state["infer_hz"] = frames / (now - t0)
                frames = 0
                t0 = now

        except Exception as e:
            print(f"[YOLO] inference error: {e}")
            time.sleep(0.01)
