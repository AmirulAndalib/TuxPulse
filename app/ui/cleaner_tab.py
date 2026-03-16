from PyQt5.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget


class CleanerTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')
        self.targets = QListWidget()
        self.clean_btn = QPushButton()
        self.journal_btn = QPushButton()
        layout.addWidget(self.title)
        layout.addWidget(self.targets, 1)
        layout.addWidget(self.clean_btn)
        layout.addWidget(self.journal_btn)
