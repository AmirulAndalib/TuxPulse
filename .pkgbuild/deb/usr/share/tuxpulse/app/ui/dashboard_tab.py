from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget, QSplitter, QGridLayout

from ui.widgets import LiveChart


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.info_title = QLabel()
        self.info_title.setObjectName("SectionTitle")
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setMinimumHeight(220)

        self.log_title = QLabel()
        self.log_title.setObjectName("SectionTitle")
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.hide()
        self.log_title.hide()

        self.cpu_chart = LiveChart("", "#3b82f6")
        self.disk_chart = LiveChart("", "#f59e0b")
        self.ram_chart = LiveChart("", "#22c55e")
        self.gpu_chart = LiveChart("", "#8b5cf6")
        self.battery_chart = LiveChart("", "#eab308")
        self.net_chart = LiveChart("", "#ec4899")

        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        info_layout.addWidget(self.info_title)
        info_layout.addWidget(self.info_box)

        graphs_section = QWidget()
        graphs_layout = QVBoxLayout(graphs_section)
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        graphs_layout.setSpacing(8)

        graph_grid = QGridLayout()
        graph_grid.setContentsMargins(0, 0, 0, 0)
        graph_grid.setHorizontalSpacing(10)
        graph_grid.setVerticalSpacing(10)

        graph_grid.addWidget(self.cpu_chart, 0, 0)
        graph_grid.addWidget(self.ram_chart, 0, 1)
        graph_grid.addWidget(self.gpu_chart, 0, 2)
        graph_grid.addWidget(self.disk_chart, 1, 0)
        graph_grid.addWidget(self.net_chart, 1, 1)
        graph_grid.addWidget(self.battery_chart, 1, 2)

        for col in range(3):
            graph_grid.setColumnStretch(col, 1)
        for row in range(2):
            graph_grid.setRowStretch(row, 1)

        graphs_layout.addLayout(graph_grid)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(info_section)
        self.splitter.addWidget(graphs_section)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setSizes([220, 660])

        layout.addWidget(self.splitter)
