import requests

ESP32_IP = "192.168.4.1"

def send_message_to_esp32(msg: str):
    try:
        url = f"http://{ESP32_IP}/print?msg={msg}"
        r = requests.get(url, timeout=1)
        if r.status_code == 200:
            print(f"Sent to ESP32: {msg}")
        else:
            print(f"❌ ESP32 returned status {r.status_code}")
    except requests.exceptions.RequestException as e:
        print("Could not reach ESP32:", e)
