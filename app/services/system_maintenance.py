import subprocess
import shutil
import tempfile
import os


def detect_package_manager():

    if shutil.which("apt"):
        return "apt"

    if shutil.which("dnf"):
        return "dnf"

    if shutil.which("pacman"):
        return "pacman"

    if shutil.which("zypper"):
        return "zypper"

    return None


def build_commands():

    manager = detect_package_manager()

    cmds = []

    if manager == "apt":

        cmds = [
            "apt update",
            "apt full-upgrade -y",
            "apt autoremove -y",
            "apt autoclean"
        ]

    elif manager == "dnf":

        cmds = [
            "dnf upgrade -y",
            "dnf autoremove -y",
            "dnf clean all"
        ]

    elif manager == "pacman":

        cmds = [
            "pacman -Syu --noconfirm",
            "pacman -Sc --noconfirm"
        ]

    elif manager == "zypper":

        cmds = [
            "zypper --non-interactive update",
            "zypper clean"
        ]

    if shutil.which("flatpak"):
        cmds.append("flatpak update -y")

    return cmds


def run_full_maintenance(log_callback, progress_callback):

    commands = build_commands()

    total = len(commands)

    script = "#!/bin/bash\nset -e\n\n"

    for cmd in commands:

        script += f'echo ">>> {cmd}"\n'
        script += cmd + "\n\n"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sh")

    tmp.write(script.encode())
    tmp.close()

    os.chmod(tmp.name, 0o755)

    try:

        log_callback("Requesting administrator privileges...")

        process = subprocess.Popen(
            ["pkexec", tmp.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        step = 0

        for line in process.stdout:

            line = line.rstrip()

            log_callback(line)

            if line.startswith(">>>"):
                step += 1
                progress = int(step / total * 100)
                progress_callback(progress)

        process.wait()

        if process.returncode != 0:
            raise Exception("Maintenance script failed")

    finally:

        os.remove(tmp.name)