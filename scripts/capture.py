import os
import time
import argparse
import cv2
from FrameBus import FrameBus
from discover import discover_esp32_ip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="images", help="Folder to save images")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    ip = discover_esp32_ip()
    if not ip:
        raise RuntimeError("ESP32 not found on hotspot subnet")
    print("ESP32 IP:", ip)

    rtsp_url = f"rtsp://{ip}:554/"

    bus = FrameBus(rtsp_url)
    bus.start()

    print("Press SPACE to capture an image, ESC or Q to exit.")
    win = "RTSP Stream (FrameBus)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    try:
        last_frame = None
        while True:
            frame = bus.latest()  # freshest frame (or None while connecting)
            if frame is not None:
                last_frame = frame
                cv2.imshow(win, frame)
            else:
                # no frame yet; avoid busy loop
                cv2.waitKey(10)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):  # ESC or 'q'
                print("Exiting…")
                break
            if key == 32 and last_frame is not None:  # SPACE
                ts = time.strftime("%Y%m%d_%H%M%S")
                ms = int((time.time() % 1) * 1000)
                path = os.path.join(args.out, f"frame_{ts}_{ms:03d}.jpg")
                cv2.imwrite(path, last_frame)
                print(f"Saved {path}")

    finally:
        bus.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
