from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QLabel, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class StartupTab(QWidget):
    enabled_changed = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')
        self.hint = QLabel()
        self.table = QTableWidget(0, 4)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addWidget(self.table)

    def set_texts(self, texts):
        self.title.setText(texts['title'])
        self.hint.setText(texts['hint'])
        self.table.setHorizontalHeaderLabels([texts['name'], texts['exec'], texts['enabled'], texts['scope']])

    def populate(self, rows, yes_text='Yes', no_text='No', scope_map=None):
        scope_map = scope_map or {}
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(row['name']))
            self.table.setItem(r, 1, QTableWidgetItem(row['exec']))
            combo = QComboBox()
            combo.addItem(yes_text, True)
            combo.addItem(no_text, False)
            combo.setCurrentIndex(0 if row['enabled'] else 1)
            combo.currentIndexChanged.connect(lambda _idx, cb=combo, path=row['path']: self.enabled_changed.emit(path, bool(cb.currentData())))
            self.table.setCellWidget(r, 2, combo)
            self.table.setItem(r, 3, QTableWidgetItem(scope_map.get(row['scope'], row['scope'])))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(1, 260)
