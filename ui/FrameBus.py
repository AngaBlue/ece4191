import subprocess
import threading
import queue
import numpy as np
import atexit
import contextlib
import time
import sys

W, H = 640, 480
BYTES = W * H * 3  # bgr24


class FrameBus:
    def __init__(self, url: str, debug: bool = False):
        self.url = url
        self.debug = debug
        self._proc = None
        self._t = None
        self._stop = threading.Event()
        self._latest = None
        self._lock = threading.Lock()

        self._fps = 0.0
        self._fps_counter = 0
        self._fps_window_start = None
        self._fps_lock = threading.Lock()

    def start(self):
        if self._t and self._t.is_alive():
            return

        cmd = [
            "ffmpeg",
            "-nostdin", "-hide_banner",
            "-loglevel", "error",
            "-nostats",
            # INPUT opts
            "-rtsp_transport", "udp",
            "-probesize", "32",
            "-analyzeduration", "0",
            "-fflags", "nobuffer",
            "-fflags", "discardcorrupt",
            "-avioflags", "direct",
            # INPUT
            "-i", self.url,
            # OUTPUT/filter opts
            "-vf", "setpts=0",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-fps_mode", "passthrough",
            "pipe:1",
        ]

        if self.debug:
            print("[FrameBus] starting ffmpeg:",
                  " ".join(cmd), file=sys.stderr)
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**7,
        )
        self._stop.clear()

        # reset FPS window
        with self._fps_lock:
            self._fps = 0.0
            self._fps_counter = 0
            self._fps_window_start = time.time()

        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()
        atexit.register(self.stop)

    def stop(self):
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            with contextlib.suppress(Exception):
                self._proc.terminate()
        if self._t:
            self._t.join(timeout=1.0)
        with self._fps_lock:
            self._fps = 0.0

    def latest(self):
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    def fps(self) -> float:
        with self._fps_lock:
            now = time.time()
            if now - (self._fps_window_start or 0.0) >= 2.0:
                self._fps = 0.0
            return self._fps

    def _run(self):
        if not self._proc:
            return

        stdout = self._proc.stdout
        if not stdout:
            return

        frame_bytes = BYTES

        while not self._stop.is_set():
            buf = stdout.read(frame_bytes)
            if not buf:
                if self.debug:
                    print("[FrameBus] stdout closed (no data).", file=sys.stderr)
                break
            if len(buf) != frame_bytes:
                if self.debug:
                    print(
                        f"[FrameBus] short read {len(buf)} bytes (expected {frame_bytes}).", file=sys.stderr)
                break

            frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()

            with self._lock:
                self._latest = frame

            # --- FPS accounting (1-second windows) ---
            now = time.time()
            with self._fps_lock:
                # initialize window start if needed (e.g., after start)
                if self._fps_window_start is None:
                    self._fps_window_start = now
                self._fps_counter += 1
                elapsed = now - self._fps_window_start
                if elapsed >= 1.0:
                    self._fps = self._fps_counter / elapsed
                    self._fps_counter = 0
                    self._fps_window_start = now
                    if self.debug:
                        print(
                            f"[FrameBus] fps ~{self._fps:.1f}", file=sys.stderr)

        rc = self._proc.poll()
        if self.debug:
            print(
                f"[FrameBus] reader loop end, ffmpeg rc={rc}", file=sys.stderr)

    def _drain_stderr(self):
        # print ffmpeg lines; helpful if URL/path wrong (e.g., need /mjpeg/1)
        while not self._stop.is_set() and self._proc and self._proc.stderr:
            line = self._proc.stderr.readline()
            if not line:
                break
            sys.stderr.write("[ffmpeg] " + line.decode(errors="ignore"))
