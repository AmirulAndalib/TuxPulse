import json
import os
import socket
from typing import Any, Dict

SOCKET_PATH = "/run/tuxpulse.sock"
DEFAULT_TIMEOUT = 15.0


class HelperError(RuntimeError):
    pass


def _roundtrip(payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    if not os.path.exists(SOCKET_PATH):
        raise HelperError(f"TuxPulse helper socket not found: {SOCKET_PATH}")

    data = json.dumps(payload).encode("utf-8")

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(SOCKET_PATH)
        client.sendall(data)
        client.shutdown(socket.SHUT_WR)

        chunks = []
        while True:
            try:
                chunk = client.recv(65536)
            except socket.timeout as exc:
                raise HelperError("Timed out waiting for TuxPulse helper response") from exc
            if not chunk:
                break
            chunks.append(chunk)

    if not chunks:
        raise HelperError("Empty response from TuxPulse helper")

    try:
        return json.loads(b"".join(chunks).decode("utf-8"))
    except Exception as exc:
        raise HelperError("Invalid JSON response from TuxPulse helper") from exc


def helper_available(timeout: float = 2.0) -> bool:
    try:
        response = _roundtrip({"action": "ping"}, timeout=timeout)
        return response.get("code") == 0
    except Exception:
        return False


def send_request(payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    try:
        return _roundtrip(payload, timeout=timeout)
    except Exception as exc:
        return {"code": 1, "output": f"Unable to reach TuxPulse helper: {exc}"}
