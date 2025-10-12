import socket
import struct
from ip import get_ip
from config import PORT

ip = get_ip()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_packet(cmd: int, payload: bytes, mid: int = 0):
    header = struct.pack("<BBB", cmd, len(payload), mid & 0xFF)
    chk = (sum(header) + sum(payload)) & 0xFF
    pkt = header + payload + struct.pack("<B", chk)
    try:
        sock.sendto(pkt, (ip, PORT))
    except OSError as e:
        print(f"[Warning] Could not send UDP packet: {e}")


def set_brightness(level: int, mid: int = 0):
    payload = struct.pack("<B", int(level))
    send_packet(0x01, payload, mid)


def move(x: float, y: float, mid: int = 0):
    payload = struct.pack("<ff", float(x), float(y))
    send_packet(0x02, payload, mid)


def camera(pan: int | float, tilt: int | float, mid: int = 0):
    payload = struct.pack("<HH", int(pan), int(tilt))
    send_packet(0x03, payload, mid)


def close_sockets(mid: int = 0):
    send_packet(0x04, bytes(), mid)


def restart(mid: int = 0):
    send_packet(0x05, bytes(), mid)
