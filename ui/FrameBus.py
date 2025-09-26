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
        self._subs: set[queue.Queue] = set()
        self._latest = None
        self._lock = threading.Lock()

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
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        # also read stderr in background so ffmpeg errors aren’t blocking
        threading.Thread(target=self._drain_stderr, daemon=True).start()
        atexit.register(self.stop)

    def stop(self):
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            with contextlib.suppress(Exception):
                self._proc.terminate()
        if self._t:
            self._t.join(timeout=1.0)

    def subscribe(self, maxsize: int = 1) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=maxsize)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: queue.Queue):
        self._subs.discard(q)

    def latest(self):
        with self._lock:
            return None if self._latest is None else self._latest.copy()

    def _run(self):
        if not self._proc:
            return

        stdout = self._proc.stdout
        if not stdout:
            return
        frame_bytes = BYTES
        frames = 0
        t0 = time.time()
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

            dead = []
            for q in list(self._subs):
                try:
                    if q.full():
                        _ = q.get_nowait()
                    q.put_nowait(frame)
                except Exception:
                    dead.append(q)
            for q in dead:
                self._subs.discard(q)

            frames += 1
            if self.debug and frames % 60 == 0:
                dt = time.time() - t0
                fps = frames / dt if dt > 0 else 0
                print(f"[FrameBus] received ~{fps:.1f} fps", file=sys.stderr)

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
