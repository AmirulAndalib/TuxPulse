from collections import deque

import psutil


class MonitorService:
    def __init__(self, history=40):
        self.cpu_history = deque([0.0] * history, maxlen=history)
        self.ram_history = deque([0.0] * history, maxlen=history)
        self.disk_history = deque([0.0] * history, maxlen=history)
        self.net_history = deque([0.0] * history, maxlen=history)
        self._last_net = psutil.net_io_counters()

    def snapshot(self):
        self.cpu_history.append(psutil.cpu_percent(interval=None))
        self.ram_history.append(psutil.virtual_memory().percent)
        self.disk_history.append(psutil.disk_usage('/').percent)
        current_net = psutil.net_io_counters()
        delta = (current_net.bytes_sent + current_net.bytes_recv) - (self._last_net.bytes_sent + self._last_net.bytes_recv)
        self._last_net = current_net
        mbps = max(0.0, delta / (1024 * 1024))
        self.net_history.append(mbps)
        return {
            'cpu_history': list(self.cpu_history),
            'ram_history': list(self.ram_history),
            'disk_history': list(self.disk_history),
            'net_history': list(self.net_history),
        }
