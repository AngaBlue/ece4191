import requests
from datetime import datetime

ESP32_IP = "192.168.4.1"  # Use plain IP, port 80 by default for HTTP

def take_photo():
    try:
        url = f"http://{ESP32_IP}/jpg"
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Photo saved as {filename}")
        else:
            print("❌ Failed to capture photo:", r.status_code)
    except Exception as e:
        print("⚠️ Error:", e)