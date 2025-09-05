import requests
ESP32_IP = "192.168.4.1"
try:
    r = requests.get(f"http://{ESP32_IP}/stream", timeout=5)
    print("Connected, status:", r.status_code)
except Exception as e:
    print("Failed to connect:", e)