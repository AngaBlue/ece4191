import requests

ESP32_IP = "192.168.4.1"

DEADZONE = 0.1

def send_motion(translation: float, rotation: float):
    """
    translation: forward/backward [-1.0 .. 1.0]
    rotation: left/right turn [-1.0 .. 1.0]
    """
    try:
        url = f"http://{ESP32_IP}/move?translation={translation:.2f}&rotation={rotation:.2f}"
        r = requests.get(url, timeout=0.05)
        if r.ok:
            print(f"Sent: T={translation:.2f} R={rotation:.2f}")
    except requests.exceptions.RequestException as e:
        print("ESP32 unreachable:", e)
