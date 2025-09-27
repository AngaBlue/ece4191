import subprocess
import threading
import numpy as np
import atexit
import contextlib
import time
import sys
from config import H, W

BYTES = W * H * 3  # bgr24


class FrameBus:
    def __init__(self, url: str, debug: bool = False, stall_timeout: float = 3.0):
        self.url = url
        self.debug = debug
        self.stall_timeout = stall_timeout

        self._proc: subprocess.Popen | None = None
        self._reader_t: threading.Thread | None = None
        self._stderr_t: threading.Thread | None = None
        self._watch_t: threading.Thread | None = None
        self._stop = threading.Event()

        self._latest: np.ndarray | None = None
        self._last_frame_ts: float | None = None
        self._lock = threading.Lock()

        # simple fps window
        self._fps = 0.0
        self._fps_n = 0
        self._fps_t0 = 0.0
        self._fps_lock = threading.Lock()

    def start(self):
        if self._reader_t and self._reader_t.is_alive():
            return
        self._stop.clear()
        self._spawn()

        # reader
        self._reader_t = threading.Thread(
            target=self._reader_loop, daemon=True)
        self._reader_t.start()

        # watchdog
        self._watch_t = threading.Thread(target=self._watchdog, daemon=True)
        self._watch_t.start()

        atexit.register(self.stop)

    def stop(self):
        self._stop.set()
        self._kill()
        if self._reader_t:
            self._reader_t.join(timeout=1.0)
        if self._stderr_t:
            self._stderr_t.join(timeout=0.5)
        if self._watch_t:
            self._watch_t.join(timeout=0.5)
        with self._fps_lock:
            self._fps = 0.0

    def latest(self):
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    def fps(self) -> float:
        with self._fps_lock:
            if time.time() - self._fps_t0 >= 2.0:
                return 0.0
            return self._fps

    def _spawn(self):
        with self._fps_lock:
            self._fps = 0.0
            self._fps_n = 0
            self._fps_t0 = time.time()
        self._last_frame_ts = None

        cmd = [
            "ffmpeg",
            "-nostdin", "-hide_banner",
            "-loglevel", "error",
            "-nostats",
            "-rtsp_transport", "udp",
            "-probesize", "32",
            "-analyzeduration", "0",
            "-fflags", "nobuffer",
            "-fflags", "discardcorrupt",
            "-avioflags", "direct",
            "-i", self.url,
            "-vf", "setpts=0",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-fps_mode", "passthrough",
            "pipe:1",
        ]
        if self.debug:
            print("[FrameBus] spawn:", " ".join(cmd), file=sys.stderr)

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=(subprocess.PIPE if self.debug else subprocess.DEVNULL),
            bufsize=10**7,
        )

        if self.debug and self._proc.stderr:
            self._stderr_t = threading.Thread(
                target=self._drain_stderr, args=(
                    self._proc.stderr,), daemon=True
            )
            self._stderr_t.start()

    def _kill(self):
        if self._proc and self._proc.poll() is None:
            with contextlib.suppress(Exception):
                self._proc.terminate()
            try:
                self._proc.wait(timeout=0.8)
            except Exception:
                with contextlib.suppress(Exception):
                    self._proc.kill()
        self._proc = None

    def _reader_loop(self):
        fb = BYTES
        while not self._stop.is_set():
            p = self._proc
            if not p or p.poll() is not None or not p.stdout:
                time.sleep(0.05)
                continue

            buf = p.stdout.read(fb)  # blocking
            if not buf or len(buf) != fb:
                continue

            frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            with self._lock:
                self._latest = frame

            now = time.time()
            self._last_frame_ts = now

            # fps window (1s)
            with self._fps_lock:
                self._fps_n += 1
                dt = now - self._fps_t0
                if dt >= 1.0:
                    self._fps = self._fps_n / dt
                    self._fps_n = 0
                    self._fps_t0 = now
                    if self.debug:
                        print(
                            f"[FrameBus] fps ~{self._fps:.1f}", file=sys.stderr)

    def _watchdog(self):
        # Restart on process death OR no frames for stall_timeout.
        while not self._stop.is_set():
            now = time.time()
            dead = (self._proc is None) or (self._proc.poll() is not None)
            stalled = (self._last_frame_ts is not None) and (
                (now - self._last_frame_ts) > self.stall_timeout)

            if dead or stalled:
                if self.debug:
                    why = "dead" if dead else f"stalled ({now - (self._last_frame_ts or now):.1f}s)"
                    print(f"[FrameBus] restart: {why}", file=sys.stderr)
                self._kill()
                for _ in range(int(self.stall_timeout / 0.1)):
                    if self._stop.is_set():
                        break
                    time.sleep(0.1)
                if self._stop.is_set():
                    break
                self._spawn()
            time.sleep(0.1)

    @staticmethod
    def _drain_stderr(pipe):
        for line in iter(pipe.readline, b""):
            sys.stderr.write("[ffmpeg] " + line.decode(errors="ignore"))
