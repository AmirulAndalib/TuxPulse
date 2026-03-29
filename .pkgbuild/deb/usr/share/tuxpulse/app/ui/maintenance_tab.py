from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QPushButton, QProgressBar, QTextEdit, QVBoxLayout, QWidget


class MaintenanceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')
        self.status_label = QLabel()
        self.output_title = QLabel()
        self.output_title.setObjectName('SectionTitle')
        self.full_btn = QPushButton()
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setAlignment(Qt.AlignCenter)
        self.step_label = QLabel()
        self.eta_label = QLabel()
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.step_label)
        layout.addWidget(self.eta_label)
        layout.addWidget(self.full_btn)
        layout.addWidget(self.output_title)
        layout.addWidget(self.log_box, 1)
