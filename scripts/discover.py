import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

ICS_SUBNET = "192.168.137.0/24"   # Windows hotspot default
GATEWAY_IP = "192.168.137.1"      # Windows hotspot gateway


def _local_ip_for_subnet(gateway_ip: str, fallback_prefix: str = "192.168.137.") -> Optional[str]:
    """Find the laptop's local IP on the hotspot interface (best effort)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect((gateway_ip, 9))  # no traffic actually sent
        ip = s.getsockname()[0]
        s.close()
        if ip.startswith(fallback_prefix):
            return ip
    except Exception:
        pass
    # Fallback: None (we’ll still scan the /24)
    return None


def _check_host(ip: str, port: int, timeout: float = 0.25) -> bool:
    """Return True if host answers on port (TCP) and looks like RTSP (or at least open)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, port))
            # Minimal RTSP OPTIONS (many servers respond 200 OK)
            req = f"RTSP/1.0 OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            # Some stacks expect the RFC order; send a more standard one:
            req = f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            try:
                sock.sendall(req.encode("ascii", "ignore"))
                resp = sock.recv(256)
                if b"RTSP/1.0" in resp:   # good enough
                    return True
            except Exception:
                # Even if no response, the connect itself succeeded; likely our ESP32.
                return True
    except Exception:
        return False
    return False


def discover_esp32_ip(subnet: str = ICS_SUBNET,
                      ports: Tuple[int, ...] = (554, 8554),
                      per_host_timeout: float = 0.25,
                      max_workers: int = 128) -> Optional[str]:
    """
    Scan the Windows hotspot subnet and return the IP of the ESP32.
    Assumes the ESP32 is the only client on the hotspot.
    """
    net = ipaddress.ip_network(subnet, strict=False)
    local_ip = _local_ip_for_subnet(GATEWAY_IP)
    candidates = [str(ip) for ip in net.hosts()
                  if str(ip) != GATEWAY_IP and str(ip) != local_ip]

    for port in ports:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_check_host, ip, port,
                                 per_host_timeout): ip for ip in candidates}
            for fut in as_completed(futures):
                ip = futures[fut]
                try:
                    ok = fut.result()
                except Exception:
                    ok = False
                if ok:
                    return ip
    return None
