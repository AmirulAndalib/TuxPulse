from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import math


DARK_THEME = {
    "figure_bg": "#0f172a",
    "axis_bg": "#0f172a",
    "title": "white",
    "ticks": "#cbd5e1",
    "spine": "#334155",
    "grid_alpha": 0.15,
    "pie_edge": "#0f172a",
    "bar": "#2563eb",
}

LIGHT_THEME = {
    "figure_bg": "#ffffff",
    "axis_bg": "#ffffff",
    "title": "#0f172a",
    "ticks": "#475569",
    "spine": "#cbd5e1",
    "grid_alpha": 0.22,
    "pie_edge": "#ffffff",
    "bar": "#2563eb",
}


class LiveChart(FigureCanvas):
    def __init__(self, title, color):
        self.theme = dict(DARK_THEME)
        self.fig = Figure(facecolor=self.theme["figure_bg"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.title = title
        self.color = color
        self._values = []
        self._y_min = None
        self._y_max = None
        self._y_suffix = ""
        self._x_label = ""
        self._y_label = ""
        super().__init__(self.fig)

    def set_theme(self, mode: str):
        self.theme = dict(LIGHT_THEME if mode == "light" else DARK_THEME)
        self.fig.set_facecolor(self.theme["figure_bg"])
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.update_series(
            self._values,
            self.title,
            y_min=self._y_min,
            y_max=self._y_max,
            y_suffix=self._y_suffix,
            x_label=self._x_label,
            y_label=self._y_label,
        )

    def update_series(self, values, title=None, y_min=None, y_max=None, y_suffix="", x_label="", y_label=""):
        if title is not None:
            self.title = title
        self._values = [float(v) for v in (values or [])]
        self._y_min = y_min
        self._y_max = y_max
        self._y_suffix = y_suffix or ""
        self._x_label = x_label or ""
        self._y_label = y_label or ""

        self.ax.clear()
        self.ax.set_facecolor(self.theme["axis_bg"])

        if self._values:
            xs = range(len(self._values))
            self.ax.plot(xs, self._values, linewidth=2.0, color=self.color)
            self.ax.fill_between(xs, self._values, color=self.color, alpha=0.24)
        else:
            self.ax.plot([], [], linewidth=2.0, color=self.color)

        self.ax.set_title(self.title, color=self.theme["title"], fontsize=10)
        self.ax.tick_params(colors=self.theme["ticks"], labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(self.theme["spine"])
        self.ax.grid(True, alpha=self.theme["grid_alpha"])

        if self._x_label:
            self.ax.set_xlabel(self._x_label, color=self.theme["ticks"], fontsize=8)
        if self._y_label:
            self.ax.set_ylabel(self._y_label, color=self.theme["ticks"], fontsize=8)

        if self._y_suffix:
            self.ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:.0f}{self._y_suffix}"))

        if self._y_min is not None or self._y_max is not None:
            low = self._y_min if self._y_min is not None else self.ax.get_ylim()[0]
            high = self._y_max if self._y_max is not None else self.ax.get_ylim()[1]
            if math.isfinite(low) and math.isfinite(high) and low != high:
                self.ax.set_ylim(low, high)

        self.fig.tight_layout()
        self.draw()


class PieChart(FigureCanvas):
    def __init__(self, title):
        self.theme = dict(DARK_THEME)
        self.fig = Figure(facecolor=self.theme["figure_bg"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.title = title
        self._used_gb = 0.0
        self._free_gb = 0.0
        super().__init__(self.fig)

    def set_theme(self, mode: str):
        self.theme = dict(LIGHT_THEME if mode == "light" else DARK_THEME)
        self.fig.set_facecolor(self.theme["figure_bg"])
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.update_usage(self._used_gb, self._free_gb, self.title)

    def update_usage(self, used_gb, free_gb, title=None):
        if title is not None:
            self.title = title

        def sanitize(value):
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return 0.0
            if not math.isfinite(numeric) or numeric < 0:
                return 0.0
            return numeric

        self._used_gb = sanitize(used_gb)
        self._free_gb = sanitize(free_gb)
        total = self._used_gb + self._free_gb

        self.ax.clear()
        self.ax.set_facecolor(self.theme["axis_bg"])

        if total <= 0:
            self.ax.text(0.5, 0.5, "No data", ha="center", va="center", color=self.theme["title"], fontsize=11)
            self.ax.set_title(self.title, color=self.theme["title"], fontsize=11)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.fig.tight_layout()
            self.draw()
            return

        _, texts, autotexts = self.ax.pie(
            [self._used_gb, self._free_gb],
            labels=["Used", "Free"],
            autopct="%1.1f%%",
            startangle=90,
            colors=["#ef4444", "#22c55e"],
            wedgeprops={"linewidth": 1, "edgecolor": self.theme["pie_edge"]},
        )
        for t in texts + autotexts:
            t.set_color(self.theme["title"])
        self.ax.set_title(self.title, color=self.theme["title"], fontsize=11)
        self.fig.tight_layout()
        self.draw()


class BarChart(FigureCanvas):
    def __init__(self, title):
        self.theme = dict(DARK_THEME)
        self.fig = Figure(facecolor=self.theme["figure_bg"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.title = title
        self._labels = []
        self._values = []
        super().__init__(self.fig)

    def set_theme(self, mode: str):
        self.theme = dict(LIGHT_THEME if mode == "light" else DARK_THEME)
        self.fig.set_facecolor(self.theme["figure_bg"])
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.update_bars(self._labels, self._values, self.title)

    def update_bars(self, labels, values, title=None):
        if title:
            self.title = title
        self._labels = list(labels or [])
        self._values = list(values or [])
        self.ax.clear()
        self.ax.set_facecolor(self.theme["axis_bg"])
        self.ax.bar(self._labels, self._values, color=self.theme["bar"])
        self.ax.set_title(self.title, color=self.theme["title"], fontsize=11)
        self.ax.tick_params(axis="x", colors=self.theme["ticks"], rotation=25)
        self.ax.tick_params(axis="y", colors=self.theme["ticks"])
        for spine in self.ax.spines.values():
            spine.set_color(self.theme["spine"])
        self.ax.grid(True, axis="y", alpha=self.theme["grid_alpha"])
        self.fig.tight_layout()
        self.draw()
