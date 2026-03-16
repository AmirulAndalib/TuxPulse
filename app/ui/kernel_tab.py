from PyQt5.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


class KernelTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.analyze_btn = QPushButton()
        self.remove_btn = QPushButton()
        layout.addWidget(self.title)
        layout.addWidget(self.text, 1)
        layout.addWidget(self.analyze_btn)
        layout.addWidget(self.remove_btn)
