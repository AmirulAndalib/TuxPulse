#!/usr/bin/env python3
import datetime
import json
import os
import pwd
import re
import shutil
import socket
import subprocess
from typing import Any, Dict, List, Tuple

SOCKET_PATH = "/run/tuxpulse.sock"
LOG_FILE = "/var/log/tuxpulse-helper.log"

SAFE_ARG = re.compile(r"^[A-Za-z0-9.+_:@/=-]+$")
SAFE_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")

ALLOWED_BASE = {"env", "apt", "pacman", "dnf", "zypper", "flatpak", "journalctl", "systemctl", "bash"}
ALLOWED_PREFIXES = (
    ["apt", "install", "-y"],
    ["apt", "remove", "-y"],
    ["apt", "purge", "-y"],
    ["apt", "autoremove", "-y"],
    ["pacman", "-S", "--noconfirm"],
    ["pacman", "-R", "--noconfirm"],
    ["pacman", "-Rns", "--noconfirm"],
    ["pacman", "-Syu", "--noconfirm"],
    ["dnf", "install", "-y"],
    ["dnf", "remove", "-y"],
    ["dnf", "upgrade", "-y"],
    ["dnf", "autoremove", "-y"],
    ["zypper", "--non-interactive", "install"],
    ["zypper", "--non-interactive", "remove"],
    ["zypper", "--non-interactive", "update"],
    ["flatpak", "install", "-y", "flathub"],
    ["flatpak", "uninstall", "-y"],
    ["flatpak", "update", "-y"],
    ["journalctl", "--vacuum-time=7d"],
    ["systemctl", "daemon-reload"],
    ["systemctl", "restart", "tuxpulse-helper.service"],
    ["bash", "-lc"],
)
ALLOWED_ACTIONS = {"ping", "run", "install", "maintenance", "remove", "update", "cleanup"}


def _log(user: str, action: str, cmd: List[str], output: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"{datetime.datetime.now().isoformat()} | {user} | {action} | {' '.join(cmd)}\n")
            if output:
                handle.write(output.rstrip() + "\n")
            handle.write("\n")
    except Exception:
        pass


def _peer_user(conn: socket.socket) -> str:
    try:
        creds = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        uid = int.from_bytes(creds[4:8], "little")
        return pwd.getpwuid(uid).pw_name
    except Exception:
        return "unknown"


def _unwrap_env(cmd: List[str]) -> Tuple[List[str], bool]:
    if not cmd:
        return [], False
    if cmd[0] != "env":
        return cmd, True

    idx = 1
    while idx < len(cmd) and SAFE_ENV.fullmatch(cmd[idx]):
        idx += 1

    if idx >= len(cmd):
        return [], False

    return cmd[idx:], True


def _safe_args(args: List[str]) -> bool:
    return bool(args) and all(SAFE_ARG.fullmatch(arg or "") for arg in args)


def _validate(cmd: List[str]) -> bool:
    if not isinstance(cmd, list) or not cmd:
        return False
    if cmd[0] not in ALLOWED_BASE:
        return False

    real_cmd, ok = _unwrap_env(cmd)
    if not ok or not real_cmd:
        return False

    if real_cmd[0] == "flatpak" and shutil.which("flatpak") is None:
        return False

    for prefix in ALLOWED_PREFIXES:
        if real_cmd[: len(prefix)] == prefix:
            extra = real_cmd[len(prefix):]
            if prefix[:2] == ["systemctl", "daemon-reload"]:
                return len(real_cmd) == len(prefix)
            if prefix[:3] == ["systemctl", "restart", "tuxpulse-helper.service"]:
                return len(real_cmd) == len(prefix)
            if prefix[:2] == ["journalctl", "--vacuum-time=7d"]:
                return len(real_cmd) == len(prefix)
            if prefix[:2] == ["bash", "-lc"]:
                return len(real_cmd) == 3
            return _safe_args(extra)

    return False


def _run(cmd: List[str]) -> Tuple[int, str]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def _handle(conn: socket.socket, payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action")
    cmd = payload.get("cmd") or []
    user = _peer_user(conn)

    if action not in ALLOWED_ACTIONS:
        return {"code": 1, "output": "Invalid action"}

    if action == "ping":
        return {"code": 0, "output": "pong"}

    if not _validate(cmd):
        return {"code": 1, "output": f"Blocked command: {' '.join(cmd) if isinstance(cmd, list) else cmd}"}

    code, output = _run(cmd)
    _log(user, action, cmd, output)
    return {"code": code, "output": output}


def main() -> None:
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    server.listen(10)

    while True:
        conn, _ = server.accept()
        try:
            data = conn.recv(1024 * 1024)
            payload = json.loads(data.decode("utf-8")) if data else {"action": "ping"}
            response = _handle(conn, payload)
        except Exception as exc:
            response = {"code": 1, "output": str(exc)}
        try:
            conn.sendall(json.dumps(response).encode("utf-8"))
        except Exception:
            pass
        finally:
            conn.close()


if __name__ == "__main__":
    main()
