from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QLabel, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class ServicesTab(QWidget):
    state_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')
        self.hint = QLabel()
        self.table = QTableWidget(0, 2)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addWidget(self.table)

    def set_texts(self, texts):
        self.title.setText(texts['title'])
        self.hint.setText(texts['hint'])
        self.table.setHorizontalHeaderLabels([texts['service'], texts['state']])

    def populate(self, rows, state_labels=None):
        state_labels = state_labels or {'Running': 'Running', 'Stopped': 'Stopped', 'Disabled': 'Disabled'}
        options = [('Running', state_labels.get('Running', 'Running')), ('Stopped', state_labels.get('Stopped', 'Stopped')), ('Disabled', state_labels.get('Disabled', 'Disabled'))]
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(row['name']))
            combo = QComboBox()
            for code, label in options:
                combo.addItem(label, code)
            current_index = next((idx for idx, (code, _label) in enumerate(options) if code == row['state']), 1)
            combo.setCurrentIndex(current_index)
            combo.currentIndexChanged.connect(lambda _idx, cb=combo, name=row['name']: self.state_changed.emit(name, str(cb.currentData())))
            self.table.setCellWidget(r, 1, combo)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
