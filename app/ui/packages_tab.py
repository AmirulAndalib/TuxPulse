from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class PackagesTab(QWidget):
    search_requested = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    upgradable_requested = pyqtSignal()
    remove_requested = pyqtSignal(str)
    purge_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._rows = []
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName('SectionTitle')

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search_btn = QPushButton()
        self.refresh_btn = QPushButton()
        self.upgradable_btn = QPushButton()
        self.remove_btn = QPushButton()
        self.purge_btn = QPushButton()
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.search_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.upgradable_btn)
        toolbar.addWidget(self.remove_btn)
        toolbar.addWidget(self.purge_btn)

        self.table = QTableWidget(0, 3)
        self.details_title = QLabel()
        self.details_title.setObjectName('SectionTitle')
        self.details = QTextEdit()
        self.details.setReadOnly(True)

        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details, 1)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(details_container)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(self.title)
        layout.addLayout(toolbar)
        layout.addWidget(splitter, 1)

        self.search_btn.clicked.connect(lambda: self.search_requested.emit(self.search.text().strip()))
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.upgradable_btn.clicked.connect(self.upgradable_requested.emit)
        self.remove_btn.clicked.connect(self._emit_remove_selected)
        self.purge_btn.clicked.connect(self._emit_purge_selected)
        self.table.itemSelectionChanged.connect(self.update_details)

    def set_texts(self, texts, total_count=0):
        self.title.setText(texts['title'].format(count=total_count))
        self.search.setPlaceholderText(texts['search_placeholder'])
        self.search_btn.setText(texts['search'])
        self.refresh_btn.setText(texts['installed'])
        self.upgradable_btn.setText(texts['upgradable'])
        self.remove_btn.setText(texts['remove'])
        self.purge_btn.setText(texts['purge'])
        self.table.setHorizontalHeaderLabels([texts['package'], texts['version'], texts['status']])
        self.details_title.setText(texts['details'])
        if not self._rows:
            self.details.clear()

    def _emit_remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is not None:
            self.remove_requested.emit(item.text())

    def _emit_purge_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item is not None:
            self.purge_requested.emit(item.text())

    def populate(self, rows):
        self._rows = rows
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(row['name']))
            self.table.setItem(r, 1, QTableWidgetItem(row['version']))
            self.table.setItem(r, 2, QTableWidgetItem(row.get('status', 'installed')))
        self.table.resizeColumnsToContents()
        if rows:
            self.table.setCurrentCell(0, 0)
        else:
            self.details.clear()

    def update_details(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._rows):
            self.details.clear()
            return
        item = self._rows[row]
        lines = [
            f"Package: {item['name']}",
            f"Version: {item['version']}",
            f"Status: {item.get('status', 'installed')}",
        ]
        self.details.setPlainText('\n'.join(lines))
