from collections import deque
import glob
import math
import shutil
import subprocess

import psutil


class MonitorService:
    def __init__(self, history=40):
        self.cpu_history = deque([0.0] * history, maxlen=history)
        self.ram_history = deque([0.0] * history, maxlen=history)
        self.disk_history = deque([0.0] * history, maxlen=history)
        self.gpu_history = deque([0.0] * history, maxlen=history)
        self.battery_history = deque([0.0] * history, maxlen=history)
        self.net_history = deque([0.0] * history, maxlen=history)
        self._last_net = psutil.net_io_counters()

    @staticmethod
    def _clamp_percent(value):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(numeric):
            return 0.0
        return max(0.0, min(100.0, numeric))

    def _read_gpu_percent(self):
        if shutil.which("nvidia-smi"):
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=utilization.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=0.8,
                    check=False,
                )
                if result.returncode == 0:
                    first_line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
                    if first_line:
                        return self._clamp_percent(first_line), True
            except Exception:
                pass

        for candidate in glob.glob("/sys/class/drm/card*/device/gpu_busy_percent"):
            try:
                with open(candidate, "r", encoding="utf-8") as handle:
                    value = handle.read().strip()
                return self._clamp_percent(value), True
            except Exception:
                continue

        return 0.0, False

    def _read_battery_percent(self):
        try:
            battery = psutil.sensors_battery()
        except Exception:
            battery = None
        if battery is None or battery.percent is None:
            return 0.0, False
        return self._clamp_percent(battery.percent), True

    def snapshot(self):
        self.cpu_history.append(self._clamp_percent(psutil.cpu_percent(interval=None)))
        self.ram_history.append(self._clamp_percent(psutil.virtual_memory().percent))
        self.disk_history.append(self._clamp_percent(psutil.disk_usage('/').percent))

        gpu_now, gpu_available = self._read_gpu_percent()
        self.gpu_history.append(gpu_now)

        battery_now, battery_available = self._read_battery_percent()
        self.battery_history.append(battery_now)

        current_net = psutil.net_io_counters()
        delta = (current_net.bytes_sent + current_net.bytes_recv) - (self._last_net.bytes_sent + self._last_net.bytes_recv)
        self._last_net = current_net
        mbps = max(0.0, delta / (1024 * 1024))
        self.net_history.append(mbps)

        return {
            'cpu_history': list(self.cpu_history),
            'ram_history': list(self.ram_history),
            'disk_history': list(self.disk_history),
            'gpu_history': list(self.gpu_history),
            'battery_history': list(self.battery_history),
            'net_history': list(self.net_history),
            'gpu_available': gpu_available,
            'battery_available': battery_available,
        }
