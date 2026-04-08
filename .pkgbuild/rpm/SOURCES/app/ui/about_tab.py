from html import escape

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget


class AboutTab(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._texts = {}
        self._release_info = None
        self._current_version = ""

        root = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        container = QWidget()
        self.content = QVBoxLayout(container)
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(12)

        self.header_title = QLabel()
        self.header_title.setObjectName("SectionTitle")

        self.header_subtitle = QLabel()
        self.header_subtitle.setObjectName("Subtitle")
        self.header_subtitle.setWordWrap(True)

        self.version_card = QFrame()
        self.version_card.setObjectName("Panel")
        version_layout = QVBoxLayout(self.version_card)
        version_layout.setContentsMargins(14, 14, 14, 14)
        version_layout.setSpacing(8)

        self.version_title = QLabel()
        self.version_title.setObjectName("SectionTitle")

        self.current_version_label = QLabel()
        self.current_version_label.setObjectName("Subtitle")
        self.current_version_label.setWordWrap(True)

        self.latest_version_label = QLabel()
        self.latest_version_label.setObjectName("Subtitle")
        self.latest_version_label.setWordWrap(True)
        self.latest_version_label.setOpenExternalLinks(True)

        self.update_status_label = QLabel()
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setStyleSheet(
            """
            QLabel {
                background: #0b1220;
                border: 1px solid #243041;
                border-radius: 10px;
                padding: 10px 12px;
                color: #e5e7eb;
                font-weight: bold;
            }
            """
        )

        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)

        version_layout.addWidget(self.version_title)
        version_layout.addWidget(self.current_version_label)
        version_layout.addWidget(self.latest_version_label)
        version_layout.addWidget(self.update_status_label)
        version_layout.addWidget(self.refresh_btn)

        self.project_card = QFrame()
        self.project_card.setObjectName("Panel")
        project_layout = QVBoxLayout(self.project_card)
        project_layout.setContentsMargins(14, 14, 14, 14)
        project_layout.setSpacing(8)

        self.project_title = QLabel()
        self.project_title.setObjectName("SectionTitle")

        self.project_links_label = QLabel()
        self.project_links_label.setObjectName("Subtitle")
        self.project_links_label.setWordWrap(True)
        self.project_links_label.setOpenExternalLinks(True)

        project_layout.addWidget(self.project_title)
        project_layout.addWidget(self.project_links_label)

        self.developer_card = QFrame()
        self.developer_card.setObjectName("Panel")
        developer_layout = QVBoxLayout(self.developer_card)
        developer_layout.setContentsMargins(14, 14, 14, 14)
        developer_layout.setSpacing(8)

        self.developer_title = QLabel()
        self.developer_title.setObjectName("SectionTitle")

        self.developer_links_label = QLabel()
        self.developer_links_label.setObjectName("Subtitle")
        self.developer_links_label.setWordWrap(True)
        self.developer_links_label.setOpenExternalLinks(True)

        developer_layout.addWidget(self.developer_title)
        developer_layout.addWidget(self.developer_links_label)

        self.content.addWidget(self.header_title)
        self.content.addWidget(self.header_subtitle)
        self.content.addWidget(self.version_card)
        self.content.addWidget(self.project_card)
        self.content.addWidget(self.developer_card)
        self.content.addStretch(1)

        self.scroll.setWidget(container)
        root.addWidget(self.scroll)

    def set_texts(self, texts: dict):
        self._texts = texts or {}

        self.header_title.setText(self._texts.get("title", "About TuxPulse"))
        self.header_subtitle.setText(
            self._texts.get(
                "subtitle",
                "Project information, download links and update availability.",
            )
        )
        self.version_title.setText(self._texts.get("version_title", "Version information"))
        self.project_title.setText(self._texts.get("project_title", "Project links"))
        self.developer_title.setText(self._texts.get("developer_title", "Developer"))
        self.refresh_btn.setText(self._texts.get("check_updates", "Check again"))

        self.project_links_label.setText(self._texts.get("project_links_html", ""))
        self.developer_links_label.setText(self._texts.get("developer_links_html", ""))

        if self._current_version:
            self.set_current_version(self._current_version)

        if self._release_info is None:
            self.set_checking()
        else:
            self.set_release_info(self._release_info)

    def set_current_version(self, version: str):
        self._current_version = version or ""
        label = self._texts.get("current_version", "Installed version")
        self.current_version_label.setText(f"{label}: <b>{escape(self._current_version)}</b>")

    def set_checking(self):
        latest_label = self._texts.get("latest_version", "Latest GitHub release")
        checking_text = self._texts.get("checking", "Checking GitHub releases...")
        self.latest_version_label.setText(f"{latest_label}: {escape(checking_text)}")
        self.update_status_label.setText(checking_text)

    def set_error(self, message: str):
        latest_label = self._texts.get("latest_version", "Latest GitHub release")
        unavailable_text = self._texts.get(
            "unavailable",
            "Could not check GitHub releases right now.",
        )
        details = escape(message.strip()) if message else ""

        self.latest_version_label.setText(f"{latest_label}: {escape(unavailable_text)}")
        self.update_status_label.setText(
            f"{unavailable_text}\n{details}" if details else unavailable_text
        )

        self._release_info = {
            "latest_version": "",
            "has_update": False,
            "release_url": "",
            "published_at": "",
            "error": message or unavailable_text,
        }

    def set_release_info(self, info: dict):
        self._release_info = info or {}

        latest_label = self._texts.get("latest_version", "Latest GitHub release")
        version = str((info or {}).get("latest_version") or self._texts.get("unknown", "unknown"))
        published_at = str((info or {}).get("published_at") or "")[:10]
        release_url = str((info or {}).get("release_url") or "")

        display = escape(version)
        if published_at:
            display = (
                f"{display} "
                f"({escape(self._texts.get('published_on', 'published on'))} "
                f"{escape(published_at)})"
            )

        if release_url:
            display = f'<a href="{escape(release_url)}">{display}</a>'

        self.latest_version_label.setText(f"{latest_label}: {display}")

        if info.get("has_update"):
            self.update_status_label.setText(
                self._texts.get(
                    "update_available",
                    "A newer version is available: {version}.",
                ).format(version=version)
            )
        else:
            self.update_status_label.setText(
                self._texts.get(
                    "up_to_date",
                    "You are using the latest available version.",
                )
            )