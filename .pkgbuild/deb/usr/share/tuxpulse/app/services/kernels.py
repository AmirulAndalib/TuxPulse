import platform
import shutil
import subprocess
from typing import Dict, List


def _run_output(command: List[str]) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""


def _list_debian_kernels() -> List[str]:
    output = _run_output(["dpkg-query", "-W", "-f=${Package}\n"])
    kernels: List[str] = []
    for line in output.splitlines():
        if line.startswith("linux-image-"):
            kernels.append(line.replace("linux-image-", ""))
    return kernels


def _list_arch_kernels() -> List[str]:
    output = _run_output(["pacman", "-Q"])
    kernels: List[str] = []

    known_kernel_pkgs = {
        "linux",
        "linux-lts",
        "linux-zen",
        "linux-hardened",
    }

    for line in output.splitlines():
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        if name in known_kernel_pkgs:
            kernels.append(name)

    return kernels


def _list_rpm_kernels() -> List[str]:
    output = _run_output(["rpm", "-qa", "--qf", "%{NAME}\n"])
    kernels: List[str] = []

    for line in output.splitlines():
        if line.startswith(("kernel-core", "kernel-default", "kernel-default-base", "kernel-rt")):
            kernels.append(line)

    return kernels


def get_kernel_report() -> Dict[str, List[str] | str]:
    current = platform.release()
    installed: List[str] = []

    if shutil.which("dpkg-query"):
        installed = _list_debian_kernels()
    elif shutil.which("pacman"):
        installed = _list_arch_kernels()
    elif shutil.which("rpm"):
        installed = _list_rpm_kernels()

    if not installed:
        installed = [current]

    suggested: List[str] = []
    for item in installed:
        if current not in item:
            suggested.append(item)

    return {
        "current": current,
        "installed": installed,
        "suggested": suggested,
    }


def removal_commands_for_suggested():
    report = get_kernel_report()
    cmds = []

    if shutil.which("apt"):
        for kernel in report["suggested"]:
            pkg = kernel if kernel.startswith("linux-image-") else f"linux-image-{kernel}"
            cmds.append(["apt", "purge", "-y", pkg])

    elif shutil.which("pacman"):
        for kernel in report["suggested"]:
            cmds.append(["pacman", "-Rns", "--noconfirm", kernel])

    elif shutil.which("dnf"):
        for kernel in report["suggested"]:
            cmds.append(["dnf", "remove", "-y", kernel])

    elif shutil.which("zypper"):
        for kernel in report["suggested"]:
            cmds.append(["zypper", "--non-interactive", "remove", kernel])

    return cmds