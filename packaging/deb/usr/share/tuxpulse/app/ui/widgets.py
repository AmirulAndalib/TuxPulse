from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class LiveChart(FigureCanvas):
    def __init__(self, title, color):
        self.fig = Figure(facecolor='#0f172a')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#0f172a')
        self.title = title
        self.color = color
        super().__init__(self.fig)

    def update_series(self, values, title=None):
        if title:
            self.title = title
        self.ax.clear()
        self.ax.set_facecolor('#0f172a')
        self.ax.plot(values, linewidth=2.4, color=self.color)
        self.ax.fill_between(range(len(values)), values, color=self.color, alpha=0.28)
        self.ax.set_title(self.title, color='white', fontsize=11)
        self.ax.tick_params(colors='#cbd5e1')
        for spine in self.ax.spines.values():
            spine.set_color('#334155')
        self.ax.grid(True, alpha=0.15)
        self.fig.tight_layout()
        self.draw()


class PieChart(FigureCanvas):
    def __init__(self, title):
        self.fig = Figure(facecolor='#0f172a')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#0f172a')
        self.title = title
        super().__init__(self.fig)

    def update_usage(self, used_gb, free_gb, title=None):
        if title:
            self.title = title
        self.ax.clear()
        self.ax.set_facecolor('#0f172a')
        _, texts, autotexts = self.ax.pie(
            [used_gb, free_gb],
            labels=['Used', 'Free'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#ef4444', '#22c55e'],
            wedgeprops={'linewidth': 1, 'edgecolor': '#0f172a'},
        )
        for t in texts + autotexts:
            t.set_color('white')
        self.ax.set_title(self.title, color='white', fontsize=11)
        self.fig.tight_layout()
        self.draw()


class BarChart(FigureCanvas):
    def __init__(self, title):
        self.fig = Figure(facecolor='#0f172a')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#0f172a')
        self.title = title
        super().__init__(self.fig)

    def update_bars(self, labels, values, title=None):
        if title:
            self.title = title
        self.ax.clear()
        self.ax.set_facecolor('#0f172a')
        self.ax.bar(labels, values, color='#8b5cf6')
        self.ax.set_title(self.title, color='white', fontsize=11)
        self.ax.tick_params(axis='x', colors='#cbd5e1', rotation=25)
        self.ax.tick_params(axis='y', colors='#cbd5e1')
        for spine in self.ax.spines.values():
            spine.set_color('#334155')
        self.ax.grid(True, axis='y', alpha=0.15)
        self.fig.tight_layout()
        self.draw()
