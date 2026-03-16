from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class ActivityOverlay(QWidget):
    def __init__(self, parent, text, detail=""):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(0,0,0,145);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.card = QWidget(self)
        self.card.setObjectName("OverlayCard")
        self.card.setStyleSheet(
            "QWidget#OverlayCard { background:#111827; border:1px solid #243041; border-radius:14px; padding:20px; }"
        )

        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(10)

        self.spinner = QLabel("⟳", self.card)
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setStyleSheet("font-size:32px; color:#60a5fa; background: transparent;")

        self.label = QLabel(text, self.card)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size:16px; font-weight:bold; color:white; background: transparent;")

        self.detail = QLabel(detail, self.card)
        self.detail.setAlignment(Qt.AlignCenter)
        self.detail.setWordWrap(True)
        self.detail.setStyleSheet("font-size:13px; color:#cbd5e1; background: transparent;")

        card_layout.addWidget(self.spinner)
        card_layout.addWidget(self.label)
        card_layout.addWidget(self.detail)
        layout.addWidget(self.card, 0, Qt.AlignCenter)

    def sync_to_parent(self):
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
            width = min(420, max(280, self.width() - 80))
            self.card.setFixedWidth(width)

    def set_text(self, text, detail=None):
        self.label.setText(text)
        if detail is not None:
            self.detail.setText(detail)
        self.label.repaint()
        self.detail.repaint()

    def show_overlay(self):
        self.sync_to_parent()
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_overlay(self):
        self.hide()


class Toast(QLabel):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.setText(text)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            "background:#111827; color:white; border:1px solid #243041; border-radius:10px; padding:10px 14px;"
        )
        self.adjustSize()
        self.move(max(16, parent.width() - self.width() - 20), max(16, parent.height() - self.height() - 48))
        self.show()
        self.raise_()
        QTimer.singleShot(3000, self.close)
