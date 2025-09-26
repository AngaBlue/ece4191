import re
import subprocess
from typing import Optional

# Window Mobile Hotspot
HOTSPOT_IF_IP = "192.168.137.1"


def get_ip() -> Optional[str]:
    """
    Returns IP of the first device found in the ARP table under the hotspot interface.
    """
    arp = subprocess.check_output(["arp", "-a"], text=True, encoding="utf-8")

    # Find the block for our hotspot interface
    blocks = re.split(r"\r?\n\r?\n", arp)
    for b in blocks:
        if f"Interface: {HOTSPOT_IF_IP}" not in b:
            continue
        for line in b.splitlines():
            # Typical line: "  192.168.137.3    30-ed-a0-ba-0a-ac   dynamic"
            m = re.match(r"\s*(192\.168\.137\.\d+)\s+([0-9A-Fa-f-]{17})", line)
            if m:
                ip, mac = m.groups()
                if ip != HOTSPOT_IF_IP and mac.lower() != "ff-ff-ff-ff-ff-ff":
                    return ip
    return None


if __name__ == "__main__":
    ip = get_ip()
    if ip:
        print("Client IP :", ip)
    else:
        print("No hotspot client found in ARP table.")
