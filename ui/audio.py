import subprocess
import threading
import time
from config import SAMPLE_RATE


def audio_loop(url: str,
               state: dict,
               stop_event: threading.Event):
    last_sample = 0.0

    cmd = [
        "ffplay",
        "-nodisp",
        "-rtsp_transport", "udp",
        "-probesize", "32",
        "-analyzeduration", "0",
        "-vn",
        "-acodec", "pcm_s16be",
        "-ar", "48000",
        url,
    ]
    process = None

    while not stop_event.is_set():
        now = time.time()
        if now - last_sample < SAMPLE_RATE:
            time.sleep(0.001)
            continue
        last_sample = now

        if state['play_audio'] and process is None:
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif not state['play_audio'] and process is not None:
            process.terminate()
            process = None

    if process:
      process.terminate()
