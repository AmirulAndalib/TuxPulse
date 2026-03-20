from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class InstallerCard(QFrame):
    toggled = pyqtSignal(str, bool)
    install_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    update_requested = pyqtSignal(str)
    source_changed = pyqtSignal(str, str)

    def __init__(self, app: dict):
        super().__init__()
        self.app = app
        self._texts = {}
        self.setObjectName("InstallerCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(10)

        self.check = QCheckBox()
        self.check.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #e5e7eb; background: #ffffff; } QCheckBox::indicator:checked { background: #86efac; border: 1px solid #86efac; }")
        self.check.toggled.connect(lambda checked: self.toggled.emit(self.app["id"], checked))
        top.addWidget(self.check, 0, Qt.AlignTop)

        icon_label = QLabel()
        icon = QIcon.fromTheme(app.get("icon") or "application-x-executable")
        icon_label.setPixmap(icon.pixmap(28, 28))
        top.addWidget(icon_label, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self.name_label = QLabel(app["name"])
        self.name_label.setObjectName("SectionTitle")
        self.desc_label = QLabel(app.get("description", ""))
        self.desc_label.setWordWrap(True)
        self.meta_label = QLabel()
        self.meta_label.setObjectName("Subtitle")
        text_col.addWidget(self.name_label)
        text_col.addWidget(self.desc_label)
        text_col.addWidget(self.meta_label)
        top.addLayout(text_col, 1)

        actions = QVBoxLayout()
        actions.setSpacing(6)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        btn_row = QHBoxLayout()
        self.install_btn = QPushButton("Install")
        self.remove_btn = QPushButton("Remove")
        self.update_btn = QPushButton("Update")
        self.install_btn.clicked.connect(lambda: self.install_requested.emit(self.app["id"]))
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.app["id"]))
        self.update_btn.clicked.connect(lambda: self.update_requested.emit(self.app["id"]))
        btn_row.addWidget(self.install_btn)
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.update_btn)
        actions.addWidget(self.status_label)
        actions.addLayout(btn_row)
        top.addLayout(actions)
        root.addLayout(top)

        source_row = QHBoxLayout()
        self.source_label = QLabel("Source:")
        source_row.addWidget(self.source_label)
        self.native_radio = QRadioButton("Native")
        self.flatpak_radio = QRadioButton("Flatpak")
        self.source_group = QButtonGroup(self)
        self.source_group.addButton(self.native_radio)
        self.source_group.addButton(self.flatpak_radio)
        self.native_radio.toggled.connect(self._emit_source_changed)
        source_row.addWidget(self.native_radio)
        source_row.addWidget(self.flatpak_radio)
        source_row.addStretch(1)
        root.addLayout(source_row)

        self.update_data(app)

    def set_texts(self, texts: dict):
        self._texts = texts or {}
        self.install_btn.setText(self._texts.get("install", "Install"))
        self.remove_btn.setText(self._texts.get("remove", "Remove"))
        self.update_btn.setText(self._texts.get("update", "Update"))
        self.source_label.setText(self._texts.get("source", "Source:"))
        self.native_radio.setText(self._texts.get("native", "Native"))
        self.flatpak_radio.setText(self._texts.get("flatpak", "Flatpak"))
        self._apply_state_label()

    def _emit_source_changed(self):
        if self.native_radio.isChecked():
            self.source_changed.emit(self.app["id"], "native")
        elif self.flatpak_radio.isChecked():
            self.source_changed.emit(self.app["id"], "flatpak")

    def _apply_state_label(self):
        state = self.app.get("state", "available")
        if state == "installed-native":
            self.status_label.setText(self._texts.get("installed_native", "Installed (native)"))
        elif state == "installed-flatpak":
            self.status_label.setText(self._texts.get("installed_flatpak", "Installed (Flatpak)"))
        else:
            self.status_label.setText(self._texts.get("available", "Available"))

    def update_data(self, app: dict):
        self.app = app
        self.name_label.setText(app["name"])
        self.desc_label.setText(app.get("description", ""))
        native_text = app.get("native_package") if app.get("native_available") else self._texts.get("not_available", "not available")
        flatpak_text = app.get("flatpak") if app.get("flatpak_available") else self._texts.get("not_available", "not available")
        self.meta_label.setText(f"Native: {native_text} | Flatpak: {flatpak_text}")

        native_available = bool(app.get("native_available"))
        flatpak_available = bool(app.get("flatpak_available"))
        self.native_radio.setEnabled(native_available)
        self.flatpak_radio.setEnabled(flatpak_available)

        preferred = app.get("source", "native")
        if preferred == "flatpak" and flatpak_available:
            self.flatpak_radio.setChecked(True)
        elif native_available:
            self.native_radio.setChecked(True)
        elif flatpak_available:
            self.flatpak_radio.setChecked(True)
        else:
            self.native_radio.setAutoExclusive(False)
            self.flatpak_radio.setAutoExclusive(False)
            self.native_radio.setChecked(False)
            self.flatpak_radio.setChecked(False)
            self.native_radio.setAutoExclusive(True)
            self.flatpak_radio.setAutoExclusive(True)

        state = app.get("state", "available")
        self._apply_state_label()
        if state in {"installed-native", "installed-flatpak"}:
            self.install_btn.setEnabled(False)
            self.remove_btn.setEnabled(True)
            self.update_btn.setEnabled(True)
        else:
            can_install = native_available or flatpak_available
            self.install_btn.setEnabled(can_install)
            self.remove_btn.setEnabled(False)
            self.update_btn.setEnabled(False)
        self.check.setEnabled(True)
        self.check.setChecked(False)


class InstallerTab(QWidget):
    search_changed = pyqtSignal(str)
    install_selected_requested = pyqtSignal()
    remove_selected_requested = pyqtSignal()
    update_selected_requested = pyqtSignal()
    install_one_requested = pyqtSignal(str)
    remove_one_requested = pyqtSignal(str)
    update_one_requested = pyqtSignal(str)
    source_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.cards = {}
        self._card_texts = {}

        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName("SectionTitle")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("Subtitle")
        self.subtitle.setWordWrap(True)
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.install_selected_btn = QPushButton()
        self.remove_selected_btn = QPushButton()
        self.update_selected_btn = QPushButton()
        toolbar.addWidget(self.search, 1)
        toolbar.addWidget(self.install_selected_btn)
        toolbar.addWidget(self.remove_selected_btn)
        toolbar.addWidget(self.update_selected_btn)

        self.status_label = QLabel()
        self.status_label.setObjectName("Subtitle")
        self.status_label.setWordWrap(True)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch(1)
        self.scroll.setWidget(self.container)

        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addLayout(toolbar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.scroll, 1)

        self.search.textChanged.connect(self.search_changed.emit)
        self.install_selected_btn.clicked.connect(self.install_selected_requested.emit)
        self.remove_selected_btn.clicked.connect(self.remove_selected_requested.emit)
        self.update_selected_btn.clicked.connect(self.update_selected_requested.emit)

    def set_texts(self, texts: dict):
        self.title.setText(texts.get("title", "Installer"))
        self.subtitle.setText(texts.get("subtitle", "Install software from native repositories or Flatpak."))
        self.search.setPlaceholderText(texts.get("search_placeholder", "Search applications..."))
        self.install_selected_btn.setText(texts.get("install_selected", "Install selected"))
        self.remove_selected_btn.setText(texts.get("remove_selected", "Remove selected"))
        self.update_selected_btn.setText(texts.get("update_selected", "Update selected"))
        if texts.get("status") is not None:
            self.status_label.setText(texts.get("status"))
        self._card_texts = {
            "install": texts.get("install", "Install"),
            "remove": texts.get("remove", "Remove"),
            "update": texts.get("update", "Update"),
            "source": texts.get("source", "Source:"),
            "native": texts.get("native", "Native"),
            "flatpak": texts.get("flatpak", "Flatpak"),
            "installed_native": texts.get("installed_native", "Installed (native)"),
            "installed_flatpak": texts.get("installed_flatpak", "Installed (Flatpak)"),
            "available": texts.get("available", "Available"),
            "not_available": texts.get("not_available", "not available"),
        }
        for card in self.cards.values():
            card.set_texts(self._card_texts)
            card.update_data(card.app)

    def populate(self, grouped_apps: dict):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.cards = {}
        for category, apps in grouped_apps.items():
            section = QLabel(category)
            section.setObjectName("SectionTitle")
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, section)
            for app in apps:
                card = InstallerCard(app)
                card.set_texts(self._card_texts)
                card.toggled.connect(self._on_card_toggled)
                card.install_requested.connect(self.install_one_requested.emit)
                card.remove_requested.connect(self.remove_one_requested.emit)
                card.update_requested.connect(self.update_one_requested.emit)
                card.source_changed.connect(self.source_changed.emit)
                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
                self.cards[app["id"]] = card

    def _on_card_toggled(self, app_id: str, checked: bool):
        if app_id in self.cards:
            self.cards[app_id].app["selected"] = checked

    def selected_apps(self):
        apps = []
        for card in self.cards.values():
            if card.check.isChecked():
                app = dict(card.app)
                app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
                apps.append(app)
        return apps
