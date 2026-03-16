from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QVBoxLayout, QWidget, QLineEdit
)


class SchedulerTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')
        self.subtitle = QLabel()

        self.task_list = QListWidget()
        self.task_name = QLineEdit()

        form = QFormLayout()
        self.task_label = QLabel()
        self.profile_combo = QComboBox()
        self.profile_combo.addItem('', 'quick')
        self.profile_combo.addItem('', 'full')
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem('', 'daily')
        self.frequency_combo.addItem('', 'weekly')
        self.frequency_combo.addItem('', 'monthly')
        self.notify_check = QCheckBox()
        self.profile_label = QLabel()
        self.frequency_label = QLabel()
        form.addRow(self.task_label, self.task_name)
        form.addRow(self.profile_label, self.profile_combo)
        form.addRow(self.frequency_label, self.frequency_combo)
        form.addRow('', self.notify_check)

        actions = QHBoxLayout()
        self.install_btn = QPushButton()
        self.remove_btn = QPushButton()
        self.new_btn = QPushButton()
        actions.addWidget(self.install_btn)
        actions.addWidget(self.remove_btn)
        actions.addWidget(self.new_btn)

        self.info = QTextEdit()
        self.info.setReadOnly(True)

        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.task_list, 1)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.info, 1)
