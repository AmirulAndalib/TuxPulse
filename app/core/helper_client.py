import json
import os
import socket

SOCKET_PATH = "/run/tuxpulse.sock"


def helper_available() -> bool:
    return os.path.exists(SOCKET_PATH)


def send_request(payload: dict) -> dict:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.sendall(json.dumps(payload).encode("utf-8"))
    chunks = []
    while True:
        chunk = client.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
    client.close()
    raw = b"".join(chunks).decode("utf-8") if chunks else "{}"
    return json.loads(raw or "{}")
