from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget, QSplitter, QHBoxLayout

from ui.widgets import LiveChart


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.info_title = QLabel()
        self.info_title.setObjectName('SectionTitle')
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)

        self.log_title = QLabel()
        self.log_title.setObjectName('SectionTitle')
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.cpu_chart = LiveChart('', '#3b82f6')
        self.ram_chart = LiveChart('', '#22c55e')
        self.disk_chart = LiveChart('', '#f59e0b')
        self.net_chart = LiveChart('', '#ec4899')

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
        graph_row_1 = QHBoxLayout()
        graph_row_2 = QHBoxLayout()
        graph_row_1.addWidget(self.cpu_chart)
        graph_row_1.addWidget(self.ram_chart)
        graph_row_2.addWidget(self.disk_chart)
        graph_row_2.addWidget(self.net_chart)
        graphs_layout.addLayout(graph_row_1)
        graphs_layout.addLayout(graph_row_2)

        log_section = QWidget()
        log_layout = QVBoxLayout(log_section)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(8)
        log_layout.addWidget(self.log_title)
        log_layout.addWidget(self.log_box)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(info_section)
        self.splitter.addWidget(graphs_section)
        self.splitter.addWidget(log_section)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 4)
        self.splitter.setStretchFactor(2, 2)

        layout.addWidget(self.splitter)
