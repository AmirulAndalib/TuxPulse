from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QLabel, QPushButton, QProgressBar, QTextEdit, QVBoxLayout, QWidget


class MaintenanceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.title = QLabel()
        self.title.setObjectName("SectionTitle")

        self.actions_title = QLabel()
        self.actions_title.setObjectName("SectionTitle")

        self.actions_hint = QLabel()
        self.actions_hint.setObjectName("Subtitle")
        self.actions_hint.setWordWrap(True)

        self.actions_widget = QWidget()
        self.actions_layout = QGridLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setHorizontalSpacing(10)
        self.actions_layout.setVerticalSpacing(10)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        self.output_title = QLabel()
        self.output_title.setObjectName("SectionTitle")

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
        layout.addWidget(self.actions_title)
        layout.addWidget(self.actions_hint)
        layout.addWidget(self.actions_widget)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.step_label)
        layout.addWidget(self.eta_label)
        layout.addWidget(self.output_title)
        layout.addWidget(self.log_box, 1)
