from __future__ import annotations

import json
import platform
import re
import textwrap
from html import escape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.commands import build_actions
from core.i18n import I18N
from core.runner import CommandRunner
from services.cleaner import clean_target, get_cleaner_targets, run_clean_command
from services.disk_analyzer import build_disk_analysis
from services.installer import apps_for_display, install_apps, remove_apps, update_apps
from services.kernels import get_kernel_report, removal_commands_for_suggested
from services.monitor import MonitorService
from services.packages import (
    count_installed_packages,
    list_installed_packages,
    list_upgradable_packages,
    purge_package,
    remove_package,
)
from services.services_manager import list_services, set_service_state
from services.startup import list_startup_apps, set_startup_enabled
from services.system_maintenance import run_full_maintenance
from services.systeminfo import build_system_summary
from ui.cleaner_tab import CleanerTab
from ui.dashboard_tab import DashboardTab
from ui.disk_tab import DiskTab
from ui.installer_tab import InstallerTab
from ui.kernel_tab import KernelTab
from ui.maintenance_tab import MaintenanceTab
from ui.overlays import ActivityOverlay, Toast
from ui.packages_tab import PackagesTab
from ui.services_tab import ServicesTab
from ui.startup_tab import StartupTab
from version import APP_VERSION, GITHUB_REPO


PROJECT_URL = f"https://github.com/{GITHUB_REPO}"
PROJECT_RELEASES_URL = f"{PROJECT_URL}/releases"
PROJECT_ISSUES_URL = f"{PROJECT_URL}/issues"
LATEST_RELEASE_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
DEVELOPER_LINKS = [
    ("GitHub", "https://github.com/eoliann"),
    ("Linktree", "https://linktr.ee/eoliam"),
]


def _get_distribution() -> str:
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return platform.system()


def _normalize_version(value: str) -> str:
    value = (value or "").strip()
    if value.lower().startswith("v"):
        return value[1:]
    return value


def _version_key(value: str) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", _normalize_version(value))]
    return tuple(parts or [0])


def _is_newer_version(remote_version: str, local_version: str) -> bool:
    remote_key = list(_version_key(remote_version))
    local_key = list(_version_key(local_version))
    max_len = max(len(remote_key), len(local_key))
    remote_key.extend([0] * (max_len - len(remote_key)))
    local_key.extend([0] * (max_len - len(local_key)))
    return tuple(remote_key) > tuple(local_key)


def _safe_html_links(links: list[tuple[str, str]], color: str | None = None) -> str:
    rows = []
    style = f' style="color:{escape(color)}; text-decoration:none;"' if color else ''
    for label, url in links:
        rows.append(f'• <a href="{escape(url)}"{style}>{escape(label)}</a>')
    return "<br>".join(rows)


class MaintenanceWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    started_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, i18n: I18N):
        super().__init__()
        self.i18n = i18n

    def run(self):
        try:
            self.started_signal.emit(self.i18n.t("maintenance_background"))
            run_full_maintenance(self.log_signal.emit, self.progress_signal.emit)
        except Exception as exc:
            self.error_signal.emit(str(exc))
        finally:
            self.finished_signal.emit()


class CleanerWorker(QThread):
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def run(self):
        try:
            if self.command:
                run_clean_command(self.command)
        except Exception as exc:
            self.error_signal.emit(str(exc))
        finally:
            self.finished_signal.emit()


class InstallerWorker(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, selection: list[dict], mode: str = "install"):
        super().__init__()
        self.selection = selection
        self.mode = mode

    def run(self):
        try:
            if self.mode == "remove":
                output = remove_apps(self.selection)
            elif self.mode == "update":
                output = update_apps(self.selection)
            else:
                output = install_apps(self.selection)
            self.output_signal.emit(output or "")
        except Exception as exc:
            self.error_signal.emit(str(exc))
        finally:
            self.finished_signal.emit()


class InstallerCatalogWorker(QThread):
    result_signal = pyqtSignal(dict, str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, query: str = ""):
        super().__init__()
        self.query = query

    def run(self):
        try:
            data = apps_for_display(self.query)
            self.result_signal.emit(data or {}, self.query)
        except Exception as exc:
            self.error_signal.emit(str(exc))
        finally:
            self.finished_signal.emit()


class ReleaseCheckWorker(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, api_url: str, local_version: str):
        super().__init__()
        self.api_url = api_url
        self.local_version = local_version

    def run(self):
        request = Request(
            self.api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "TuxPulse",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        try:
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))

            latest_version = str(payload.get("tag_name") or payload.get("name") or "").strip()
            if not latest_version:
                raise RuntimeError("GitHub did not return a release tag.")

            self.result_signal.emit(
                {
                    "latest_version": latest_version,
                    "release_url": str(payload.get("html_url") or PROJECT_RELEASES_URL).strip(),
                    "published_at": str(payload.get("published_at") or "").strip(),
                    "name": str(payload.get("name") or "").strip(),
                    "has_update": _is_newer_version(latest_version, self.local_version),
                }
            )
        except HTTPError as exc:
            self.error_signal.emit(f"GitHub HTTP error: {exc.code}")
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            self.error_signal.emit(f"GitHub connection error: {reason}")
        except Exception as exc:
            self.error_signal.emit(str(exc))


class DiskAnalysisWorker(QThread):
    progress_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def run(self):
        try:
            result = build_disk_analysis(limit_dirs=8, limit_files=20, progress_cb=self.progress_signal.emit)
            self.result_signal.emit(result)
        except Exception as exc:
            self.error_signal.emit(str(exc))
        finally:
            self.finished_signal.emit()


class AboutTab(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._texts = {}
        self._current_version = ""
        self._release_info = None
        self._release_error = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        container = QWidget()
        self.content = QVBoxLayout(container)
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(12)

        self.title = QLabel()
        self.title.setObjectName("SectionTitle")

        self.subtitle = QLabel()
        self.subtitle.setObjectName("Subtitle")
        self.subtitle.setWordWrap(True)

        self.version_card = self._build_card()
        self.version_title = QLabel()
        self.version_title.setObjectName("SectionTitle")
        self.current_version_label = QLabel()
        self.current_version_label.setWordWrap(True)
        self.latest_version_label = QLabel()
        self.latest_version_label.setWordWrap(True)
        self.latest_version_label.setOpenExternalLinks(True)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "QLabel { background:#0b1220; border:1px solid #243041; border-radius:10px; padding:10px 12px; font-weight:bold; }"
        )
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.version_card.layout().addWidget(self.version_title)
        self.version_card.layout().addWidget(self.current_version_label)
        self.version_card.layout().addWidget(self.latest_version_label)
        self.version_card.layout().addWidget(self.status_label)
        self.version_card.layout().addWidget(self.refresh_btn)

        self.project_card = self._build_card()
        self.project_title = QLabel()
        self.project_title.setObjectName("SectionTitle")
        self.project_links = QLabel()
        self.project_links.setObjectName("Subtitle")
        self.project_links.setWordWrap(True)
        self.project_links.setOpenExternalLinks(True)
        self.project_card.layout().addWidget(self.project_title)
        self.project_card.layout().addWidget(self.project_links)

        self.developer_card = self._build_card()
        self.developer_title = QLabel()
        self.developer_title.setObjectName("SectionTitle")
        self.developer_links = QLabel()
        self.developer_links.setObjectName("Subtitle")
        self.developer_links.setWordWrap(True)
        self.developer_links.setOpenExternalLinks(True)
        self.developer_card.layout().addWidget(self.developer_title)
        self.developer_card.layout().addWidget(self.developer_links)

        self.content.addWidget(self.title)
        self.content.addWidget(self.subtitle)
        self.content.addWidget(self.version_card)
        self.content.addWidget(self.project_card)
        self.content.addWidget(self.developer_card)
        self.content.addStretch(1)

        self.scroll.setWidget(container)
        root.addWidget(self.scroll)

    @staticmethod
    def _build_card() -> QFrame:
        card = QFrame()
        card.setObjectName("Panel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        return card

    def set_texts(self, texts: dict):
        self._texts = texts or {}
        self.title.setText(self._texts.get("title", "About TuxPulse"))
        self.subtitle.setText(self._texts.get("subtitle", "Project information and update availability."))
        self.version_title.setText(self._texts.get("version_title", "Version"))
        self.project_title.setText(self._texts.get("project_title", "Project links"))
        self.developer_title.setText(self._texts.get("developer_title", "Developer"))
        self.project_links.setText(self._texts.get("project_links_html", ""))
        self.developer_links.setText(self._texts.get("developer_links_html", ""))
        self.refresh_btn.setText(self._texts.get("check_updates", "Check again"))

        if self._current_version:
            self.set_current_version(self._current_version)

        if self._release_error:
            self.set_error(self._release_error)
        elif self._release_info is not None:
            self.set_release_info(self._release_info)
        else:
            self.set_checking()

    def set_current_version(self, version: str):
        self._current_version = version or ""
        prefix = self._texts.get("current_version", "Installed version")
        self.current_version_label.setText(f"{escape(prefix)}: <b>{escape(self._current_version)}</b>")

    def set_checking(self):
        self._release_error = ""
        latest_prefix = self._texts.get("latest_version", "Latest GitHub release")
        checking = self._texts.get("checking", "Checking GitHub releases...")
        self.latest_version_label.setText(f"{escape(latest_prefix)}: {escape(checking)}")
        self.status_label.setText(checking)

    def set_error(self, message: str):
        self._release_info = None
        self._release_error = message or self._texts.get("unavailable", "Could not check GitHub releases right now.")
        latest_prefix = self._texts.get("latest_version", "Latest GitHub release")
        unavailable = self._texts.get("unavailable", "Could not check GitHub releases right now.")
        self.latest_version_label.setText(f"{escape(latest_prefix)}: {escape(unavailable)}")
        self.status_label.setText(self._release_error)

    def set_release_info(self, info: dict):
        self._release_info = info or {}
        self._release_error = ""

        latest_prefix = self._texts.get("latest_version", "Latest GitHub release")
        published_on = self._texts.get("published_on", "published on")
        release_url = str(self._release_info.get("release_url") or "").strip()
        latest_version = str(self._release_info.get("latest_version") or self._texts.get("unknown", "unknown")).strip()
        published_at = str(self._release_info.get("published_at") or "").strip()
        published_date = published_at[:10] if published_at else ""

        label = escape(latest_version)
        if published_date:
            label = f"{label} ({escape(published_on)} {escape(published_date)})"
        if release_url:
            label = f'<a href="{escape(release_url)}" style="color:{escape(self._texts.get("link_color", "#2563eb"))}; text-decoration:none;">{label}</a>'
        self.latest_version_label.setText(f"{escape(latest_prefix)}: {label}")

        if self._release_info.get("has_update"):
            self.status_label.setText(
                self._texts.get("update_available", "A newer version is available: {version}.").format(
                    version=latest_version
                )
            )
        else:
            self.status_label.setText(
                self._texts.get("up_to_date", "You are using the latest available version.")
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.i18n = I18N("en")
        self.actions = build_actions()
        self.runner = CommandRunner(self.append_log)
        self.monitor = MonitorService(history=40)

        self.worker = None
        self.cleaner_worker = None
        self.installer_worker = None
        self.release_worker = None

        self.overlay = None
        self.cleaner_overlay = None
        self.disk_overlay = None
        self.installer_overlay = None
        self.disk_worker = None
        self.installer_catalog_worker = None
        self._disk_refresh_requested = False
        self._installer_refresh_requested = False
        self._installer_pending_query = ""
        self._installer_active_query = ""
        self._installer_search_timer = QTimer(self)
        self._installer_search_timer.setSingleShot(True)
        self._installer_search_timer.setInterval(260)
        self._installer_search_timer.timeout.connect(self._run_pending_installer_refresh)
        self._blur = None

        self.maintenance_had_error = False
        self.release_info = None
        self.release_error = ""
        self._update_notified_version = ""
        self.theme_mode = "dark"

        self.startup_rows = []
        self.service_rows = []
        self.package_rows = []
        self.package_total_count = 0
        self._building_startup_table = False
        self._building_services_table = False

        self._loaded_sections = {
            "dashboard": False,
            "disk": False,
            "kernel": False,
            "cleaner": False,
            "startup": False,
            "services": False,
            "packages": False,
            "installer": False,
            "about": False,
        }

        self._setup_window()
        self._setup_layout()
        self._connect_signals()
        self.apply_style()
        self.update_section_list()
        self.retranslate_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_monitoring)
        self.timer.start(1000)
        self.update_monitoring()

        QTimer.singleShot(0, self.initial_load)
        QTimer.singleShot(1200, self.check_latest_release)

    def _setup_window(self):
        self.setWindowTitle(f"TuxPulse v{APP_VERSION}")
        self.resize(1460, 880)

    def _setup_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("Title")

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("Subtitle")
        self.subtitle_label.setWordWrap(True)

        self.distribution_label = QLabel()
        self.distribution_label.setObjectName("SectionTitle")
        self.distribution_label.setWordWrap(True)

        language_row = QHBoxLayout()
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Română", "ro")
        language_row.addWidget(self.language_label)
        language_row.addWidget(self.language_combo)

        self.sections_label = QLabel()
        self.sections_label.setObjectName("SectionTitle")
        self.section_list = QListWidget()
        self.section_list.setObjectName("SectionList")

        self.refresh_btn = QPushButton()

        self.activity_label = QLabel()
        self.activity_label.setObjectName("Subtitle")
        self.activity_label.setWordWrap(True)
        self.activity_label.setText(f"v{APP_VERSION}")

        sidebar_layout.addWidget(self.title_label)
        sidebar_layout.addWidget(self.subtitle_label)
        sidebar_layout.addWidget(self.distribution_label)
        sidebar_layout.addLayout(language_row)
        sidebar_layout.addWidget(self.sections_label)
        sidebar_layout.addWidget(self.section_list, 1)
        sidebar_layout.addWidget(self.refresh_btn)
        sidebar_layout.addWidget(self.activity_label)

        self.panel = QFrame()
        self.panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("Tabs")
        self.tabs.tabBar().hide()

        self.dashboard_tab = DashboardTab()
        self.maintenance_tab = MaintenanceTab()
        self.disk_tab = DiskTab()
        self.kernel_tab = KernelTab()
        self.cleaner_tab = CleanerTab()
        self.startup_tab = StartupTab()
        self.services_tab = ServicesTab()
        self.packages_tab = PackagesTab()
        self.installer_tab = InstallerTab()
        self.about_tab = AboutTab()

        for tab in (
            self.dashboard_tab,
            self.maintenance_tab,
            self.disk_tab,
            self.kernel_tab,
            self.cleaner_tab,
            self.startup_tab,
            self.services_tab,
            self.packages_tab,
            self.installer_tab,
            self.about_tab,
        ):
            self.tabs.addTab(tab, "")

        panel_layout.addWidget(self.tabs)

        root.addWidget(self.sidebar, 3)
        root.addWidget(self.panel, 8)

        self.statusBar().showMessage(f"{self._tr('status_prefix', 'Status:')} {self._tr('ready', 'Ready')}")

    def _connect_signals(self):
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self.section_list.currentRowChanged.connect(self.on_section_changed)
        self.refresh_btn.clicked.connect(self.toggle_theme)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.maintenance_tab.full_btn.clicked.connect(self.start_full_maintenance)
        self.disk_tab.analyze_btn.clicked.connect(self.refresh_disk_analysis)
        self.kernel_tab.analyze_btn.clicked.connect(self.refresh_kernel_analysis)
        self.kernel_tab.remove_btn.clicked.connect(self.remove_old_kernels)
        self.cleaner_tab.clean_btn.clicked.connect(self.clean_selected_target)
        self.startup_tab.enabled_changed.connect(self.on_startup_enabled_changed)
        self.services_tab.state_changed.connect(self.on_service_state_changed)
        self.packages_tab.refresh_requested.connect(self.refresh_packages)
        self.packages_tab.upgradable_requested.connect(self.show_upgradable_packages)
        self.packages_tab.search_requested.connect(self.search_packages)
        self.packages_tab.remove_requested.connect(self.remove_selected_package)
        self.packages_tab.purge_requested.connect(self.purge_selected_package)
        self.installer_tab.search_changed.connect(self.schedule_installer_catalog_refresh)
        self.installer_tab.install_selected_requested.connect(self.install_selected_apps)
        self.installer_tab.remove_selected_requested.connect(self.remove_selected_apps)
        self.installer_tab.update_selected_requested.connect(self.update_selected_apps)
        self.installer_tab.install_one_requested.connect(self.install_one_app)
        self.installer_tab.remove_one_requested.connect(self.remove_one_app)
        self.installer_tab.update_one_requested.connect(self.update_one_app)
        self.installer_tab.source_changed.connect(self.on_installer_source_changed)
        self.about_tab.refresh_requested.connect(self.check_latest_release)

    def _tr(self, key: str, fallback_en: str, fallback_ro: str | None = None, **kwargs) -> str:
        text = self.i18n.t(key, **kwargs)
        if text == key:
            fallback = fallback_ro if self.i18n.lang == "ro" and fallback_ro is not None else fallback_en
            try:
                return fallback.format(**kwargs)
            except Exception:
                return fallback
        return text

    def _about_link_color(self) -> str:
        return "#facc15" if self.theme_mode == "dark" else "#2563eb"

    def _about_texts(self) -> dict:
        link_color = self._about_link_color()
        return {
            "title": self._tr("about_title", "About TuxPulse", "Despre TuxPulse"),
            "subtitle": self._tr(
                "about_subtitle",
                "Project information, download links and update availability.",
                "Informații despre proiect, link-uri utile și disponibilitatea unei versiuni noi.",
            ),
            "version_title": self._tr("about_version_title", "Version information", "Informații versiune"),
            "current_version": self._tr("about_current_version", "Installed version", "Versiune instalată"),
            "latest_version": self._tr("about_latest_version", "Latest GitHub release", "Ultimul release GitHub"),
            "checking": self._tr(
                "about_checking",
                "Checking GitHub releases...",
                "Se verifică release-urile GitHub...",
            ),
            "unavailable": self._tr(
                "about_unavailable",
                "Could not check GitHub releases right now.",
                "Release-urile GitHub nu pot fi verificate acum.",
            ),
            "unknown": self._tr("about_unknown", "unknown", "necunoscut"),
            "published_on": self._tr("about_published_on", "published on", "publicat la"),
            "update_available": self._tr(
                "about_update_available",
                "A newer version is available: {version}.",
                "Este disponibilă o versiune mai nouă: {version}.",
                version="{version}",
            ),
            "up_to_date": self._tr(
                "about_up_to_date",
                "You are using the latest available version.",
                "Folosești deja cea mai nouă versiune disponibilă.",
            ),
            "check_updates": self._tr("about_check_updates", "Check again", "Verifică din nou"),
            "project_title": self._tr("about_project_links", "Project links", "Link-uri proiect"),
            "developer_title": self._tr("about_developer_links", "Developer", "Dezvoltator"),
            "link_color": link_color,
            "project_links_html": _safe_html_links(
                [
                    (self._tr("about_link_repo", "GitHub repository", "Repository GitHub"), PROJECT_URL),
                    (self._tr("about_link_releases", "Releases page", "Pagina de releases"), PROJECT_RELEASES_URL),
                    (self._tr("about_link_issues", "Issues / bug reports", "Issues / raportare bug-uri"), PROJECT_ISSUES_URL),
                ],
                color=link_color,
            ),
            "developer_links_html": _safe_html_links(
                [
                    (
                        self._tr("about_link_github_profile", "GitHub profile", "Profil GitHub"),
                        DEVELOPER_LINKS[0][1],
                    ),
                    (
                        self._tr("about_link_linktree", "Linktree", "Linktree"),
                        DEVELOPER_LINKS[1][1],
                    ),
                ],
                color=link_color,
            ),
        }

    def _theme_button_text(self) -> str:
        if self.theme_mode == "dark":
            return self._tr("theme_light", "Light mode", "Mod Light")
        return self._tr("theme_dark", "Dark mode", "Mod Dark")

    def apply_chart_theme(self):
        for widget in (
            getattr(self.dashboard_tab, "cpu_chart", None),
            getattr(self.dashboard_tab, "ram_chart", None),
            getattr(self.dashboard_tab, "disk_chart", None),
            getattr(self.dashboard_tab, "gpu_chart", None),
            getattr(self.dashboard_tab, "battery_chart", None),
            getattr(self.dashboard_tab, "net_chart", None),
            getattr(self.disk_tab, "disk_pie", None),
            getattr(self.disk_tab, "disk_bar", None),
            getattr(self.disk_tab, "files_bar", None),
        ):
            if widget is not None and hasattr(widget, "set_theme"):
                widget.set_theme(self.theme_mode)

    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.apply_style()
        self.apply_chart_theme()
        self.refresh_about_tab()
        self.retranslate_ui()

    def apply_style(self):
        dark = {
            "window_bg": "#0f172a",
            "panel_bg": "#111827",
            "panel_border": "#1f2937",
            "title": "#f8fafc",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "input_bg": "#0b1220",
            "input_border": "#243041",
            "selection": "#2563eb",
            "selection_hover": "#1d4ed8",
            "disabled_bg": "#334155",
            "disabled_text": "#94a3b8",
            "header_bg": "#111827",
            "status_bg": "#0b1220",
        }
        light = {
            "window_bg": "#eef2f7",
            "panel_bg": "#ffffff",
            "panel_border": "#cbd5e1",
            "title": "#0f172a",
            "text": "#0f172a",
            "muted": "#475569",
            "input_bg": "#ffffff",
            "input_border": "#cbd5e1",
            "selection": "#2563eb",
            "selection_hover": "#1d4ed8",
            "disabled_bg": "#cbd5e1",
            "disabled_text": "#64748b",
            "header_bg": "#f8fafc",
            "status_bg": "#f8fafc",
        }
        p = light if self.theme_mode == "light" else dark
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {p['window_bg']};
                color: {p['text']};
                font-family: Arial, Helvetica, sans-serif;
                font-size: 13px;
            }}
            QFrame#Sidebar, QFrame#Panel, QFrame#InstallerCard {{
                background: {p['panel_bg']};
                border: 1px solid {p['panel_border']};
                border-radius: 14px;
            }}
            QLabel#Title {{
                font-size: 28px;
                font-weight: bold;
                color: {p['title']};
                background: transparent;
                border: none;
            }}
            QLabel#Subtitle, QLabel#SectionTitle {{
                background: transparent;
                border: none;
            }}
            QLabel#Subtitle {{
                color: {p['muted']};
            }}
            QLabel#SectionTitle {{
                font-size: 16px;
                font-weight: bold;
                color: {p['title']};
            }}
            QListWidget, QTextEdit, QTabWidget::pane, QTableWidget, QProgressBar, QLineEdit, QScrollArea {{
                background: {p['input_bg']};
                border: 1px solid {p['input_border']};
                border-radius: 10px;
                padding: 8px;
            }}
            QComboBox {{
                background-color: {p['input_bg']};
                color: {p['text']};
                border: 1px solid {p['input_border']};
                border-radius: 8px;
                padding: 4px 10px;
                min-height: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {p['input_bg']};
                color: {p['text']};
                selection-background-color: {p['selection']};
                border: 1px solid {p['input_border']};
                outline: 0;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                margin: 3px 0;
                border-radius: 8px;
            }}
            QListWidget::item:selected {{
                background: {p['selection']};
                color: white;
            }}
            QListWidget#SectionList::item {{
                padding: 10px 10px;
                margin: 4px 0;
                border-radius: 10px;
                border: 1px solid {p['input_border']};
                background: transparent;
            }}
            QListWidget#SectionList::item:selected {{
                background: {p['selection']};
                color: white;
                font-weight: bold;
                border: 1px solid {p['selection']};
            }}
            QListWidget#CleanerTargets::item {{
                padding: 8px 10px;
                margin: 3px 0;
                border-radius: 8px;
                border: 1px solid {p['input_border']};
                background: transparent;
            }}
            QListWidget#CleanerTargets::item:selected {{
                background: {p['selection']};
                color: white;
                border: 1px solid {p['selection']};
            }}
            QTabBar::tab {{
                background: {p['input_bg']};
                border: 1px solid {p['input_border']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 12px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {p['selection']};
                color: white;
            }}
            QPushButton {{
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                min-height: 34px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background: {p['selection_hover']};
            }}
            QPushButton:disabled {{
                background: {p['disabled_bg']};
                color: {p['disabled_text']};
            }}
            QPushButton#MaintenanceActionButton {{
                min-height: 42px;
                padding: 4px 10px;
            }}
            QHeaderView::section {{
                background: {p['header_bg']};
                color: {p['text']};
                border: 1px solid {p['input_border']};
                padding: 6px;
            }}
            QProgressBar::chunk {{
                background: #22c55e;
                border-radius: 8px;
            }}
            QStatusBar {{
                background: {p['panel_bg']};
                color: {p['muted']};
            }}
            """
        )
        self.about_tab.status_label.setStyleSheet(
            f"QLabel {{ background:{p['status_bg']}; border:1px solid {p['input_border']}; border-radius:10px; padding:10px 12px; font-weight:bold; color:{p['text']}; }}"
        )

    def set_status(self, text: str):
        self.statusBar().showMessage(f"{self._tr('status_prefix', 'Status:')} {text}", 5000)

    def notify(self, text: str):
        try:
            Toast(self, text)
        except Exception:
            pass
        self.set_status(text)

    def set_activity(self, text: str, busy: bool = False):
        self.maintenance_tab.status_label.setText(text)
        self.set_status(text)
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def show_busy_overlay(self, message: str, detail: str | None = None, blur: bool = True):
        if blur:
            self._blur = QGraphicsBlurEffect()
            self._blur.setBlurRadius(8)
            self.centralWidget().setGraphicsEffect(self._blur)
        else:
            self._blur = None
        self.overlay = ActivityOverlay(self, message, detail or self._tr("please_wait", "Please wait...", "Te rog așteaptă..."))
        self.overlay.sync_to_parent()
        self.overlay.show_overlay()
        QApplication.processEvents()

    def hide_busy_overlay(self):
        if self.overlay is not None:
            self.overlay.hide_overlay()
            self.overlay.deleteLater()
            self.overlay = None
        self.centralWidget().setGraphicsEffect(None)
        self._blur = None

    def resizeEvent(self, event):
        if self.overlay is not None and self.overlay.isVisible():
            self.overlay.sync_to_parent()
        if self.cleaner_overlay is not None and self.cleaner_overlay.isVisible():
            self.cleaner_overlay.sync_to_parent()
        if self.disk_overlay is not None and self.disk_overlay.isVisible():
            self.disk_overlay.sync_to_parent()
        if self.installer_overlay is not None and self.installer_overlay.isVisible():
            self.installer_overlay.sync_to_parent()
        super().resizeEvent(event)

    def initial_load(self):
        self.dashboard_tab.info_box.setPlainText(build_system_summary())
        self.refresh_cleaner_targets()
        self.refresh_about_tab()

        self._loaded_sections["dashboard"] = True
        self._loaded_sections["cleaner"] = True
        self._loaded_sections["about"] = True

        self.append_log(self._tr("info_started", "Application started."))
        self.set_status(self._tr("ready", "Ready"))

    def on_tab_changed(self, index: int):
        self.sync_section_selection(index)
        self._ensure_tab_loaded(index)

    def _ensure_tab_loaded(self, index: int):
        widget = self.tabs.widget(index)

        if widget is self.disk_tab and not self._loaded_sections["disk"]:
            self.refresh_disk_analysis()
            return

        if widget is self.kernel_tab and not self._loaded_sections["kernel"]:
            self.refresh_kernel_analysis()
            return

        if widget is self.startup_tab and not self._loaded_sections["startup"]:
            self.refresh_startup_apps()
            return

        if widget is self.services_tab and not self._loaded_sections["services"]:
            self.refresh_services()
            return

        if widget is self.packages_tab and not self._loaded_sections["packages"]:
            self.refresh_packages(update_title_only=False)
            return

        if widget is self.installer_tab and not self._loaded_sections["installer"]:
            self.refresh_installer_catalog(self.installer_tab.search.text())
            return

        if widget is self.about_tab and not self._loaded_sections["about"]:
            self.refresh_about_tab()

    def change_language(self, *_args):
        self.show_busy_overlay(self._tr("switching_language", "Switching language...", "Se schimbă limba..."))
        try:
            self.i18n.set_lang(self.language_combo.currentData())
            self.retranslate_ui()
            self.update_section_list()

            if self._loaded_sections["dashboard"]:
                self.dashboard_tab.info_box.setPlainText(build_system_summary())
            if self._loaded_sections["disk"]:
                self.refresh_disk_analysis()
            if self._loaded_sections["kernel"]:
                self.refresh_kernel_analysis()
            if self._loaded_sections["startup"]:
                self.refresh_startup_apps()
            if self._loaded_sections["services"]:
                self.refresh_services()
            if self._loaded_sections["packages"]:
                self.refresh_packages(update_title_only=False)

            self.refresh_cleaner_targets()
            self._loaded_sections["cleaner"] = True

            if self._loaded_sections["installer"]:
                self.refresh_installer_catalog(self.installer_tab.search.text())

            self.refresh_about_tab()
            QApplication.processEvents()
        finally:
            self.hide_busy_overlay()

    def retranslate_ui(self):
        self.setWindowTitle(f"TuxPulse v{APP_VERSION}")
        self.title_label.setText(f"{self._tr('app_name', 'TuxPulse')} v{APP_VERSION}")
        self.subtitle_label.setText(self._tr("subtitle", "Linux maintenance toolkit", "Trusă de mentenanță pentru Linux"))
        self.distribution_label.setText(f"{self._tr('distribution', 'Distribution', 'Distribuție')}: {_get_distribution()}")
        self.language_label.setText(self._tr("language", "Language", "Limbă"))
        self.sections_label.setText(self._tr("sections", "Sections", "Secțiuni"))
        self.refresh_btn.setText(self._theme_button_text())
        self.activity_label.setText(f"v{APP_VERSION}")

        if not (self.worker and self.worker.isRunning()):
            self.set_status(self._tr("ready", "Ready", "Gata"))

        self.dashboard_tab.info_title.setText(self._tr("system_info", "System information", "Informații sistem"))
        self.dashboard_tab.log_title.setText(self._tr("execution_log", "Execution log", "Jurnal execuție"))

        self.maintenance_tab.title.setText(self._tr("maintenance", "Maintenance", "Mentenanță"))
        self.maintenance_tab.actions_title.setText(self._tr("system_actions", "Quick actions", "Acțiuni rapide"))
        self.maintenance_tab.actions_hint.setText(
            self._tr(
                "maintenance_actions_hint",
                "Run maintenance tasks directly from here.",
                "Rulează direct de aici acțiunile de mentenanță.",
            )
        )
        self.maintenance_tab.full_btn.setText(self._wrap_button_label(self._tr("full_maintenance", "Full maintenance", "Mentenanță completă")))
        self.maintenance_tab.full_btn.setToolTip(self._tr("full_maintenance", "Full maintenance", "Mentenanță completă"))
        self.maintenance_tab.output_title.setText(
            self._tr("maintenance_live_output", "Live output", "Output în timp real")
        )
        self.rebuild_maintenance_actions()
        if not (self.worker and self.worker.isRunning()):
            self.maintenance_tab.status_label.setText(self._tr("maintenance_idle", "Idle", "Inactiv"))
            self.maintenance_tab.step_label.setText(self._tr("step_waiting", "Waiting...", "În așteptare..."))
            self.maintenance_tab.eta_label.setText(self._tr("eta_waiting", "ETA: waiting", "ETA: în așteptare"))

        self.disk_tab.partition_title.setText(self._tr("disk_partition_usage", "Disk partition usage", "Utilizare partiție disc"))
        self.disk_tab.dirs_title.setText(self._tr("largest_directories", "Largest directories", "Cele mai mari directoare"))
        self.disk_tab.files_title.setText(self._tr("largest_files", "Largest files", "Cele mai mari fișiere"))
        self.disk_tab.analyze_btn.setText(self._tr("analyze_disk", "Analyze disk", "Analizează discul"))

        self.kernel_tab.title.setText(self._tr("kernel_tools", "Kernel tools", "Instrumente kernel"))
        self.kernel_tab.analyze_btn.setText(self._tr("analyze_kernels", "Analyze kernels", "Analizează kernel-urile"))
        self.kernel_tab.remove_btn.setText(self._tr("remove_old_kernels", "Remove old kernels", "Elimină kernel-urile vechi"))

        self.cleaner_tab.title.setText(self._tr("cleaner_title", "Cleaner", "Curățare"))
        self.cleaner_tab.clean_btn.setText(self._tr("run_action", "Run action", "Rulează acțiunea"))

        self.startup_tab.set_texts(
            {
                "title": self._tr("startup_title", "Startup applications", "Aplicații la pornire"),
                "hint": self._tr("startup_hint", "Enable or disable startup entries.", "Activează sau dezactivează intrările de pornire."),
                "name": self._tr("startup_name", "Name", "Nume"),
                "exec": self._tr("startup_exec", "Command", "Comandă"),
                "enabled": self._tr("startup_enabled", "Enabled", "Activat"),
                "scope": self._tr("startup_scope", "Scope", "Domeniu"),
            }
        )

        self.services_tab.set_texts(
            {
                "title": self._tr("services_title", "Services", "Servicii"),
                "hint": self._tr("services_hint", "Start, stop or disable services.", "Pornește, oprește sau dezactivează servicii."),
                "service": self._tr("service", "Service", "Serviciu"),
                "state": self._tr("state", "State", "Stare"),
            }
        )

        self.packages_tab.set_texts(
            {
                "title": self._tr(
                    "installed_packages_count",
                    "Installed packages: {count}",
                    "Pachete instalate: {count}",
                    count=self.package_total_count,
                ),
                "search_placeholder": self._tr("packages_search_placeholder", "Search installed packages...", "Caută pachete instalate..."),
                "search": self._tr("search", "Search", "Caută"),
                "installed": self._tr("installed", "Installed", "Instalat"),
                "upgradable": self._tr("upgradable", "Upgradable", "Actualizabil"),
                "remove": self._tr("remove_selected", "Remove selected", "Elimină selectatul"),
                "purge": self._tr("purge_selected", "Purge selected", "Elimină complet selectatul"),
                "package": self._tr("package", "Package", "Pachet"),
                "version": self._tr("version", "Version", "Versiune"),
                "status": self._tr("status", "Status", "Stare"),
                "details": self._tr("package_details", "Details", "Detalii"),
            },
            total_count=self.package_total_count,
        )

        self.installer_tab.set_texts(
            {
                "title": self._tr("installer_title", "Install", "Install"),
                "subtitle": self._tr(
                    "installer_subtitle",
                    "Install software from native repositories or Flatpak.",
                    "Instalează software din repository-urile native sau din Flatpak.",
                ),
                "search_placeholder": self._tr(
                    "installer_search_placeholder",
                    "Search applications...",
                    "Caută aplicații...",
                ),
                "install_selected": self._tr(
                    "installer_install_selected",
                    "Install selected",
                    "Instalează selecția",
                ),
                "remove_selected": self._tr(
                    "installer_remove_selected",
                    "Remove selected",
                    "Elimină selecția",
                ),
                "update_selected": self._tr(
                    "installer_update_selected",
                    "Update selected",
                    "Actualizează selecția",
                ),
                "status": self._tr(
                    "installer_status_hint",
                    "Choose apps and an installation source.",
                    "Alege aplicațiile și sursa de instalare.",
                ),
                "install": self._tr("installer_install", "Install", "Instalează"),
                "remove": self._tr("installer_remove", "Remove", "Elimină"),
                "update": self._tr("installer_update", "Update", "Actualizează"),
                "source": self._tr("installer_source", "Source:", "Sursă:"),
                "native": self._tr("installer_native", "Native", "Nativ"),
                "flatpak": self._tr("installer_flatpak", "Flatpak", "Flatpak"),
                "installed_native": self._tr(
                    "installer_installed_native",
                    "Installed (native)",
                    "Instalat (nativ)",
                ),
                "installed_flatpak": self._tr(
                    "installer_installed_flatpak",
                    "Installed (Flatpak)",
                    "Instalat (Flatpak)",
                ),
                "available": self._tr("installer_available", "Available", "Disponibil"),
                "not_available": self._tr("installer_not_available", "not available", "indisponibil"),
                "available_flatpak": self._tr(
                    "installer_available_flatpak",
                    "Available via Flatpak",
                    "Disponibil prin Flatpak",
                ),
                "unavailable": self._tr("installer_unavailable", "Unavailable", "Indisponibil"),
                "update_available": self._tr(
                    "installer_update_available",
                    "Update available",
                    "Actualizare disponibilă",
                ),
                "repo_missing": self._tr(
                    "installer_repo_missing",
                    "External repo missing",
                    "Lipsește repository-ul extern",
                ),
                "meta_native": self._tr("installer_meta_native", "Native", "Nativ"),
                "meta_flatpak": self._tr("installer_meta_flatpak", "Flatpak", "Flatpak"),
                "stats_total": self._tr("installer_stats_total", "Total", "Total"),
                "stats_installed": self._tr("installer_stats_installed", "Installed", "Instalate"),
                "stats_not_installed": self._tr("installer_stats_not_installed", "Not installed", "Neinstalate"),
                "stats_selected": self._tr("installer_stats_selected", "Selected", "Selectate"),
            }
        )

        self.refresh_about_tab()

        self.tabs.setTabText(0, self._tr("dashboard", "Dashboard", "Panou"))
        self.tabs.setTabText(1, self._tr("maintenance", "Maintenance", "Mentenanță"))
        self.tabs.setTabText(2, self._tr("disk_analysis", "Disk", "Disc"))
        self.tabs.setTabText(3, self._tr("kernel_tools", "Kernel", "Kernel"))
        self.tabs.setTabText(4, self._tr("cleaner", "Cleaner", "Curățare"))
        self.tabs.setTabText(5, self._tr("startup_apps", "Startup", "Pornire"))
        self.tabs.setTabText(6, self._tr("services", "Services", "Servicii"))
        self.tabs.setTabText(7, self._tr("packages", "Packages", "Pachete"))
        self.tabs.setTabText(8, self._tr("installer_title", "Install", "Install"))
        self.tabs.setTabText(9, self._tr("about_tab", "About", "Despre"))
        self.update_section_list()
        self.sync_section_selection(self.tabs.currentIndex())

    def _section_titles(self) -> list[str]:
        return [
            self._tr("dashboard", "Dashboard", "Panou"),
            self._tr("maintenance", "Maintenance", "Mentenanță"),
            self._tr("disk_analysis", "Disk", "Disc"),
            self._tr("kernel_tools", "Kernel", "Kernel"),
            self._tr("cleaner", "Cleaner", "Curățare"),
            self._tr("startup_apps", "Startup", "Pornire"),
            self._tr("services", "Services", "Servicii"),
            self._tr("packages", "Packages", "Pachete"),
            self._tr("installer_title", "Install", "Install"),
            self._tr("about_tab", "About", "Despre"),
        ]

    def _section_icons(self):
        style = self.style()
        return [
            style.standardIcon(QStyle.SP_ComputerIcon),
            style.standardIcon(QStyle.SP_BrowserReload),
            style.standardIcon(QStyle.SP_DriveHDIcon),
            style.standardIcon(QStyle.SP_FileDialogDetailedView),
            style.standardIcon(QStyle.SP_TrashIcon),
            style.standardIcon(QStyle.SP_MediaPlay),
            style.standardIcon(QStyle.SP_CommandLink),
            style.standardIcon(QStyle.SP_FileDialogListView),
            style.standardIcon(QStyle.SP_DialogOpenButton),
            style.standardIcon(QStyle.SP_MessageBoxInformation),
        ]

    def _wrap_button_label(self, text: str, width: int = 18) -> str:
        cleaned = " ".join(str(text or "").split())
        if len(cleaned) <= width:
            return cleaned
        return "\n".join(textwrap.wrap(cleaned, width=width, break_long_words=False, break_on_hyphens=False))

    def update_section_list(self):
        current_row = self.section_list.currentRow()
        self.section_list.blockSignals(True)
        self.section_list.clear()
        for title, icon in zip(self._section_titles(), self._section_icons()):
            self.section_list.addItem(QListWidgetItem(icon, title))
        target_row = self.tabs.currentIndex() if self.tabs.count() else current_row
        if self.section_list.count() > 0:
            self.section_list.setCurrentRow(max(0, target_row))
        self.section_list.blockSignals(False)

    def sync_section_selection(self, index: int):
        if 0 <= index < self.section_list.count() and self.section_list.currentRow() != index:
            self.section_list.blockSignals(True)
            self.section_list.setCurrentRow(index)
            self.section_list.blockSignals(False)

    def on_section_changed(self, index: int):
        if 0 <= index < self.tabs.count() and self.tabs.currentIndex() != index:
            self.tabs.setCurrentIndex(index)

    def rebuild_maintenance_actions(self):
        layout = self.maintenance_tab.actions_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                if widget is not self.maintenance_tab.full_btn:
                    widget.deleteLater()

        max_columns = max(1, min(6, len(self.actions) + 1))
        for column in range(max_columns):
            layout.setColumnStretch(column, 1)

        for index, action in enumerate(self.actions):
            label = action["label_en"] if self.i18n.lang == "en" else action["label_ro"]
            button = QPushButton(self._wrap_button_label(label))
            button.setToolTip(label)
            button.setObjectName("MaintenanceActionButton")
            button.setMinimumHeight(42)
            button.clicked.connect(lambda _checked=False, idx=index: self.run_action_by_index(idx))
            row, column = divmod(index, max_columns)
            layout.addWidget(button, row, column)

        full_index = len(self.actions)
        self.maintenance_tab.full_btn.setObjectName("MaintenanceActionButton")
        self.maintenance_tab.full_btn.setText(self._wrap_button_label(self._tr("full_maintenance", "Full maintenance", "Mentenanță completă")))
        self.maintenance_tab.full_btn.setToolTip(self._tr("full_maintenance", "Full maintenance", "Mentenanță completă"))
        self.maintenance_tab.full_btn.setMinimumHeight(42)
        row, column = divmod(full_index, max_columns)
        layout.addWidget(self.maintenance_tab.full_btn, row, column)

    def append_log(self, text: str):
        cursor = self.dashboard_tab.log_box.textCursor()
        cursor.movePosition(cursor.End)
        self.dashboard_tab.log_box.setTextCursor(cursor)
        self.dashboard_tab.log_box.insertPlainText(text + ("\n" if not text.endswith("\n") else ""))

    def append_maintenance_log(self, text: str):
        cursor = self.maintenance_tab.log_box.textCursor()
        cursor.movePosition(cursor.End)
        self.maintenance_tab.log_box.setTextCursor(cursor)
        self.maintenance_tab.log_box.insertPlainText(text + ("\n" if not text.endswith("\n") else ""))

    def refresh_all(self, initial: bool = False):
        self.dashboard_tab.info_box.setPlainText(build_system_summary())
        self._loaded_sections["dashboard"] = True

        if self._loaded_sections["disk"]:
            self.refresh_disk_analysis()
        if self._loaded_sections["kernel"]:
            self.refresh_kernel_analysis()
        if self._loaded_sections["startup"]:
            self.refresh_startup_apps()
        if self._loaded_sections["services"]:
            self.refresh_services()
        if self._loaded_sections["packages"]:
            self.refresh_packages(update_title_only=False)

        self.refresh_cleaner_targets()
        self._loaded_sections["cleaner"] = True

        if self._loaded_sections["installer"]:
            self.refresh_installer_catalog(self.installer_tab.search.text())

        self.refresh_about_tab()
        self.retranslate_ui()

        if not initial:
            self.append_log(self._tr("info_refreshed", "Information refreshed."))
            self.set_status(self._tr("information_refreshed_status", "Information refreshed", "Informațiile au fost reîmprospătate"))

    def run_action_by_index(self, index: int):
        if not 0 <= index < len(self.actions):
            QMessageBox.warning(
                self,
                "Warning",
                self._tr("warning_select_action", "Please select an action first.", "Selectează mai întâi o acțiune."),
            )
            return

        action = self.actions[index]
        label = action["label_en"] if self.i18n.lang == "en" else action["label_ro"]
        description = action["description_en"] if self.i18n.lang == "en" else action["description_ro"]

        self.set_activity(self._tr("running_label", "Running: {label}", "Se rulează: {label}", label=label), busy=True)
        self.append_log(f"\n=== {label} ===")
        self.append_log(description)
        self.append_maintenance_log(f"\n=== {label} ===")
        self.append_maintenance_log(description)

        code = self.runner.run(action["commands"], requires_root=action.get("root", True))
        if code != 0:
            QMessageBox.critical(self, "Error", f"{self._tr('action_failed', 'Action failed with exit code:')} {code}")

        self.refresh_all()
        self.set_activity(self._tr("ready", "Ready", "Gata"), busy=False)

    def update_monitoring(self):
        data = self.monitor.snapshot()

        cpu_now = float(data["cpu_history"][-1]) if data["cpu_history"] else 0.0
        ram_now = float(data["ram_history"][-1]) if data["ram_history"] else 0.0
        disk_now = float(data["disk_history"][-1]) if data["disk_history"] else 0.0
        gpu_now = float(data["gpu_history"][-1]) if data["gpu_history"] else 0.0
        battery_now = float(data["battery_history"][-1]) if data["battery_history"] else 0.0
        net_now = float(data["net_history"][-1]) if data["net_history"] else 0.0

        time_label = self._tr("time_axis_seconds", "Time (s)", "Timp (s)")
        percent_axis_label = self._tr("usage_axis_percent", "Usage (%)", "Utilizare (%)")
        throughput_axis_label = self._tr("throughput_axis", "Throughput (MB/s)", "Transfer (MB/s)")

        gpu_title_value = f"{gpu_now:.1f}%" if data.get("gpu_available") else "N/A"
        battery_title_value = f"{battery_now:.1f}%" if data.get("battery_available") else "N/A"

        self.dashboard_tab.cpu_chart.update_series(
            data["cpu_history"],
            f"{self._tr('cpu_usage', 'CPU usage', 'Utilizare CPU')} ({cpu_now:.1f}%)",
            y_min=0,
            y_max=100,
            y_suffix="%",
            x_label=time_label,
            y_label=percent_axis_label,
        )
        self.dashboard_tab.ram_chart.update_series(
            data["ram_history"],
            f"{self._tr('ram_usage', 'RAM usage', 'Utilizare RAM')} ({ram_now:.1f}%)",
            y_min=0,
            y_max=100,
            y_suffix="%",
            x_label=time_label,
            y_label=percent_axis_label,
        )
        self.dashboard_tab.battery_chart.update_series(
            data["battery_history"],
            f"{self._tr('battery_charge', 'Battery charge', 'Nivel baterie')} ({battery_title_value})",
            y_min=0,
            y_max=100,
            y_suffix="%",
            x_label=time_label,
            y_label=percent_axis_label,
        )
        self.dashboard_tab.disk_chart.update_series(
            data["disk_history"],
            f"{self._tr('disk_usage', 'Disk usage', 'Utilizare disc')} ({disk_now:.1f}%)",
            y_min=0,
            y_max=100,
            y_suffix="%",
            x_label=time_label,
            y_label=percent_axis_label,
        )
        self.dashboard_tab.gpu_chart.update_series(
            data["gpu_history"],
            f"{self._tr('gpu_usage', 'GPU usage', 'Utilizare GPU')} ({gpu_title_value})",
            y_min=0,
            y_max=100,
            y_suffix="%",
            x_label=time_label,
            y_label=percent_axis_label,
        )
        self.dashboard_tab.net_chart.update_series(
            data["net_history"],
            f"{self._tr('network_throughput', 'Network throughput', 'Transfer rețea')} ({net_now:.2f} MB/s)",
            x_label=time_label,
            y_label=throughput_axis_label,
        )

    def show_disk_overlay(self, detail: str | None = None):
        message = self._tr("disk_loading_title", "Analyzing disk usage...", "Se analizează utilizarea discului...")
        detail_text = detail or self._tr("disk_loading_detail", "Scanning files and directories in the background.", "Se scanează fișierele și directoarele în fundal.")

        if self.disk_overlay is None:
            self.disk_overlay = ActivityOverlay(self.disk_tab, message, detail_text)
        else:
            self.disk_overlay.set_text(message, detail_text)

        self.disk_overlay.sync_to_parent()
        self.disk_overlay.show_overlay()
        self.disk_tab.analyze_btn.setEnabled(False)

    def update_disk_overlay(self, detail: str):
        if self.disk_overlay is not None:
            self.disk_overlay.set_text(
                self._tr("disk_loading_title", "Analyzing disk usage...", "Se analizează utilizarea discului..."),
                detail,
            )
            self.disk_overlay.sync_to_parent()

    def hide_disk_overlay(self):
        self.disk_tab.analyze_btn.setEnabled(True)
        if self.disk_overlay is not None:
            self.disk_overlay.hide_overlay()
            self.disk_overlay.deleteLater()
            self.disk_overlay = None

    def _apply_disk_analysis_result(self, payload: dict):
        usage = payload.get("usage") or {}
        self.disk_tab.disk_pie.update_usage(
            usage.get("used_gb", 0),
            usage.get("free_gb", 0),
            self._tr("disk_partition_usage", "Disk partition usage", "Utilizare partiție disc"),
        )

        dirs = payload.get("directories") or []
        labels = [item.get("name", "") for item in dirs] if dirs else ["N/A"]
        values = [item.get("size_mb", 0) for item in dirs] if dirs else [0]
        self.disk_tab.disk_bar.update_bars(
            labels,
            values,
            self._tr("largest_directories", "Largest directories", "Cele mai mari directoare"),
        )

        self.disk_tab.files_list.clear()
        for item in payload.get("files") or []:
            self.disk_tab.files_list.addItem(f"{item['size_mb']:>8.2f} MB  {item['path']}")

        self._loaded_sections["disk"] = True

    def _on_disk_analysis_progress(self, detail: str):
        self.update_disk_overlay(detail)
        self.set_status(self._tr("disk_loading_title", "Analyzing disk usage...", "Se analizează utilizarea discului..."))

    def _on_disk_analysis_error(self, message: str):
        QMessageBox.critical(self, "Error", message)

    def _on_disk_analysis_finished(self):
        self.hide_disk_overlay()
        self.disk_worker = None
        self.set_status(self._tr("ready", "Ready", "Gata"))

        if self._disk_refresh_requested:
            self._disk_refresh_requested = False
            QTimer.singleShot(0, self.refresh_disk_analysis)

    def refresh_disk_analysis(self):
        if self.disk_worker is not None and self.disk_worker.isRunning():
            self._disk_refresh_requested = True
            self.update_disk_overlay(
                self._tr(
                    "disk_refresh_queued",
                    "A new disk scan will start as soon as the current one finishes.",
                    "O nouă scanare a discului va porni imediat ce se termină cea curentă.",
                )
            )
            return

        self._disk_refresh_requested = False
        self.show_disk_overlay()
        self.set_status(self._tr("disk_loading_title", "Analyzing disk usage...", "Se analizează utilizarea discului..."))

        self.disk_worker = DiskAnalysisWorker()
        self.disk_worker.progress_signal.connect(self._on_disk_analysis_progress)
        self.disk_worker.result_signal.connect(self._apply_disk_analysis_result)
        self.disk_worker.error_signal.connect(self._on_disk_analysis_error)
        self.disk_worker.finished_signal.connect(self._on_disk_analysis_finished)
        self.disk_worker.start()

    def refresh_kernel_analysis(self):
        report = get_kernel_report()
        lines = [
            f"{self._tr('current_kernel', 'Current kernel', 'Kernel curent')}: {report['current']}",
            "",
            f"{self._tr('installed_kernels', 'Installed kernels', 'Kernel-uri instalate')}:",
        ]
        lines.extend(report["installed"] or ["-"])
        lines += ["", f"{self._tr('suggested_old_kernels', 'Suggested old kernels', 'Kernel-uri vechi sugerate')}:" ]
        lines.extend(report["suggested"] or ["-"])
        self.kernel_tab.text.setPlainText("\n".join(lines))
        self._loaded_sections["kernel"] = True

    def refresh_startup_apps(self):
        self._building_startup_table = True
        try:
            self.startup_rows = list_startup_apps()
            self.startup_tab.populate(
                self.startup_rows,
                yes_text=self._tr("yes", "Yes", "Da"),
                no_text=self._tr("no", "No", "Nu"),
                scope_map={
                    "user": self._tr("scope_user", "User", "Utilizator"),
                    "system": self._tr("scope_system", "System", "Sistem"),
                },
            )
            self._loaded_sections["startup"] = True
        finally:
            self._building_startup_table = False

    def refresh_services(self):
        self._building_services_table = True
        try:
            self.service_rows = list_services(limit=200)
            self.services_tab.populate(
                self.service_rows,
                state_labels={
                    "Running": self._tr("running", "Running", "Pornit"),
                    "Stopped": self._tr("stopped", "Stopped", "Oprit"),
                    "Disabled": self._tr("disabled", "Disabled", "Dezactivat"),
                },
            )
            self._loaded_sections["services"] = True
        finally:
            self._building_services_table = False

    def refresh_packages(self, update_title_only: bool = False):
        self.package_total_count = count_installed_packages()
        if not update_title_only:
            self.package_rows = list_installed_packages(limit=300, search="")
            self.packages_tab.populate(self.package_rows)
            self._loaded_sections["packages"] = True
        self.retranslate_ui()
        self.set_activity(self._tr("showing_installed_packages", "Showing installed packages", "Se afișează pachetele instalate"), busy=False)

    def show_upgradable_packages(self):
        self.package_rows = list_upgradable_packages(limit=300)
        self.packages_tab.populate(self.package_rows)
        self._loaded_sections["packages"] = True
        self.set_activity(self._tr("showing_upgradable_packages", "Showing upgradable packages", "Se afișează pachetele actualizabile"), busy=False)

    def search_packages(self, query: str):
        self.package_rows = list_installed_packages(limit=300, search=query)
        self.packages_tab.populate(self.package_rows)
        self._loaded_sections["packages"] = True
        query_label = query or self._tr("packages", "Packages", "Pachete")
        self.set_activity(self._tr("search_results_for", "Search results for: {query}", "Rezultate pentru: {query}", query=query_label), busy=False)

    def remove_selected_package(self, package_name: str):
        answer = QMessageBox.question(
            self,
            "Confirm",
            self._tr("remove_package_confirm", "Remove package {name}?", "Elimini pachetul {name}?", name=package_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.set_activity(self._tr("removing_package", "Removing package: {name}", "Se elimină pachetul: {name}", name=package_name), busy=True)
        self.append_log(f"\n=== Remove package: {package_name} ===")
        try:
            output = remove_package(package_name)
            self.append_log(output)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.append_log(f"Error: {exc}")
        self.refresh_packages(update_title_only=False)
        self.set_activity(self._tr("ready", "Ready", "Gata"), busy=False)

    def purge_selected_package(self, package_name: str):
        answer = QMessageBox.question(
            self,
            "Confirm",
            self._tr("purge_package_confirm", "Purge package {name}?", "Elimini complet pachetul {name}?", name=package_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.set_activity(self._tr("removing_package", "Removing package: {name}", "Se elimină pachetul: {name}", name=package_name), busy=True)
        self.append_log(f"\n=== Purge package: {package_name} ===")
        try:
            output = purge_package(package_name)
            self.append_log(output)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.append_log(f"Error: {exc}")
        self.refresh_packages(update_title_only=False)
        self.set_activity(self._tr("ready", "Ready", "Gata"), busy=False)

    def refresh_cleaner_targets(self):
        self.cleaner_tab.targets.clear()
        for target in get_cleaner_targets():
            self.cleaner_tab.targets.addItem(target["name"])

    def clean_selected_target(self):
        current = self.cleaner_tab.targets.currentItem()
        if current is None:
            QMessageBox.warning(self, "Warning", self._tr("warning_select_action", "Please select an action first.", "Selectează mai întâi o acțiune."))
            return

        name = current.text()
        command = clean_target(name)
        self.cleaner_overlay = ActivityOverlay(
            self,
            self._tr("cleaning_label", "Cleaning: {name}", "Se curăță: {name}", name=name),
            self._tr("please_wait", "Please wait...", "Te rog așteaptă..."),
        )
        self.cleaner_overlay.sync_to_parent()
        self.cleaner_overlay.show_overlay()
        QApplication.processEvents()

        self.cleaner_worker = CleanerWorker(command)
        self.cleaner_worker.finished_signal.connect(self.cleaner_finished)
        self.cleaner_worker.error_signal.connect(self.cleaner_error)
        self.cleaner_worker.start()

    def cleaner_finished(self):
        if self.cleaner_overlay is not None:
            self.cleaner_overlay.hide_overlay()
            self.cleaner_overlay.deleteLater()
            self.cleaner_overlay = None
        self.refresh_all()
        self.notify(self._tr("toast_cleaner_done", "Cleaner finished.", "Curățarea s-a încheiat."))

    def cleaner_error(self, message: str):
        if self.cleaner_overlay is not None:
            self.cleaner_overlay.hide_overlay()
            self.cleaner_overlay.deleteLater()
            self.cleaner_overlay = None
        QMessageBox.critical(self, "Error", message)

    def on_startup_enabled_changed(self, path: str, enabled: bool):
        if self._building_startup_table:
            return
        try:
            set_startup_enabled(path, enabled)
            state = self._tr("yes", "Yes", "Da") if enabled else self._tr("no", "No", "Nu")
            self.append_log(f"Startup entry {path} {state}.")
            self.set_activity(self._tr("startup_updated", "Startup entry updated: {path}", "Intrare de pornire actualizată: {path}", path=path), busy=False)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
        self.refresh_startup_apps()

    def on_service_state_changed(self, service_name: str, desired_state: str):
        if self._building_services_table:
            return
        try:
            desired_label = {
                "Running": self._tr("running", "Running", "Pornit"),
                "Stopped": self._tr("stopped", "Stopped", "Oprit"),
                "Disabled": self._tr("disabled", "Disabled", "Dezactivat"),
            }.get(desired_state, desired_state)
            self.set_activity(
                self._tr(
                    "service_changing",
                    "Changing service {name} to {state}",
                    "Se schimbă serviciul {name} la {state}",
                    name=service_name,
                    state=desired_label,
                ),
                busy=True,
            )
            set_service_state(service_name, desired_state)
            self.append_log(f"Service {service_name} -> {desired_state}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.append_log(f"Error: {exc}")
        self.refresh_services()
        self.set_activity(self._tr("ready", "Ready", "Gata"), busy=False)

    def start_full_maintenance(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Info", self._tr("maintenance_running", "Maintenance is already running.", "Mentenanța rulează deja."))
            return

        self.maintenance_had_error = False
        self.maintenance_tab.progress.setValue(0)
        self.maintenance_tab.log_box.clear()
        self.maintenance_tab.step_label.setText(self._tr("maintenance_starting", "Starting maintenance...", "Se pornește mentenanța..."))
        self.maintenance_tab.eta_label.setText(self._tr("eta_waiting", "ETA: waiting", "ETA: în așteptare"))
        self.maintenance_tab.full_btn.setEnabled(False)
        self.set_activity(self._tr("maintenance_starting", "Starting maintenance...", "Se pornește mentenanța..."), busy=True)
        self.append_log("\n=== Full system maintenance ===")
        self.append_maintenance_log("=== Full system maintenance ===")

        self.worker = MaintenanceWorker(self.i18n)
        self.worker.log_signal.connect(self.append_log)
        self.worker.log_signal.connect(self.append_maintenance_log)
        self.worker.progress_signal.connect(self.update_maintenance_progress)
        self.worker.error_signal.connect(self.on_maintenance_error)
        self.worker.started_signal.connect(lambda text: self.set_activity(text, busy=True))
        self.worker.finished_signal.connect(self.maintenance_finished)
        self.worker.start()

    def update_maintenance_progress(self, value: int):
        self.maintenance_tab.progress.setValue(value)

    def on_maintenance_error(self, message: str):
        self.maintenance_had_error = True
        self.append_log(f"Error: {message}")
        self.append_maintenance_log(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)

    def maintenance_finished(self):
        if not self.maintenance_had_error:
            self.append_log(self._tr("maintenance_finished", "Maintenance finished.", "Mentenanța s-a încheiat."))
            self.append_maintenance_log(self._tr("maintenance_finished", "Maintenance finished.", "Mentenanța s-a încheiat."))
            self.maintenance_tab.progress.setValue(100)
            self.notify(self._tr("maintenance_finished", "Maintenance finished.", "Mentenanța s-a încheiat."))
            self.set_activity(
                self._tr(
                    "maintenance_finished_success_status",
                    "Maintenance finished successfully",
                    "Mentenanța s-a încheiat cu succes",
                ),
                busy=False,
            )
        else:
            self.append_log(self._tr("maintenance_finished_errors", "Maintenance finished with errors.", "Mentenanța s-a încheiat cu erori."))
            self.append_maintenance_log(self._tr("maintenance_finished_errors", "Maintenance finished with errors.", "Mentenanța s-a încheiat cu erori."))
            self.set_activity(
                self._tr(
                    "maintenance_finished_error_status",
                    "Maintenance finished with errors",
                    "Mentenanța s-a încheiat cu erori",
                ),
                busy=False,
            )
        self.maintenance_tab.full_btn.setEnabled(True)
        self.refresh_all()

    def show_installer_overlay(self, detail: str | None = None):
        message = self._tr("installer_loading_title", "Loading application catalog...", "Se încarcă lista de aplicații...")
        detail_text = detail or self._tr(
            "installer_loading_detail",
            "Checking installed apps and available updates in the background.",
            "Se verifică aplicațiile instalate și actualizările disponibile în fundal.",
        )

        if self.installer_overlay is None:
            self.installer_overlay = ActivityOverlay(self.installer_tab, message, detail_text)
        else:
            self.installer_overlay.set_text(message, detail_text)

        self.installer_overlay.sync_to_parent()
        self.installer_overlay.show_overlay()
        self._set_installer_controls_enabled(False)

    def update_installer_overlay(self, detail: str):
        if self.installer_overlay is not None:
            self.installer_overlay.set_text(
                self._tr("installer_loading_title", "Loading application catalog...", "Se încarcă lista de aplicații..."),
                detail,
            )
            self.installer_overlay.sync_to_parent()

    def hide_installer_overlay(self):
        self._set_installer_controls_enabled(True)
        if self.installer_overlay is not None:
            self.installer_overlay.hide_overlay()
            self.installer_overlay.deleteLater()
            self.installer_overlay = None

    def _set_installer_controls_enabled(self, enabled: bool):
        self.installer_tab.search.setEnabled(enabled)
        self.installer_tab.install_selected_btn.setEnabled(enabled)
        self.installer_tab.remove_selected_btn.setEnabled(enabled)
        self.installer_tab.update_selected_btn.setEnabled(enabled)
        self.installer_tab.scroll.setEnabled(enabled)

    def schedule_installer_catalog_refresh(self, query: str = ""):
        self._installer_pending_query = query
        self._installer_search_timer.start()

    def _run_pending_installer_refresh(self):
        self.refresh_installer_catalog(self._installer_pending_query)

    def _apply_installer_catalog_result(self, data: dict, query: str):
        self._installer_active_query = query
        self.installer_tab.populate(data)
        self._loaded_sections["installer"] = True
        self.retranslate_ui()

    def _on_installer_catalog_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
        self.append_log(f"Installer catalog error: {message}")

    def _on_installer_catalog_finished(self):
        active_query = self._installer_active_query
        pending_query = self._installer_pending_query
        self.hide_installer_overlay()
        self.installer_catalog_worker = None
        self.set_status(self._tr("ready", "Ready", "Gata"))

        if self._installer_refresh_requested or pending_query != active_query:
            self._installer_refresh_requested = False
            self._installer_pending_query = pending_query
            QTimer.singleShot(0, self._run_pending_installer_refresh)

    def refresh_installer_catalog(self, query: str = ""):
        if self._installer_search_timer.isActive():
            self._installer_search_timer.stop()

        self._installer_pending_query = query

        if self.installer_catalog_worker is not None and self.installer_catalog_worker.isRunning():
            self._installer_refresh_requested = True
            self.update_installer_overlay(
                self._tr(
                    "installer_refresh_queued",
                    "A new installer refresh will start as soon as the current one finishes.",
                    "O nouă actualizare a listei Install va porni imediat ce se termină cea curentă.",
                )
            )
            return

        self._installer_refresh_requested = False
        self._installer_active_query = query
        self.show_installer_overlay()
        self.set_status(self._tr("installer_loading_title", "Loading application catalog...", "Se încarcă lista de aplicații..."))

        self.installer_catalog_worker = InstallerCatalogWorker(query)
        self.installer_catalog_worker.result_signal.connect(self._apply_installer_catalog_result)
        self.installer_catalog_worker.error_signal.connect(self._on_installer_catalog_error)
        self.installer_catalog_worker.finished_signal.connect(self._on_installer_catalog_finished)
        self.installer_catalog_worker.start()

    def on_installer_source_changed(self, app_id: str, source: str):
        card = self.installer_tab.cards.get(app_id)
        if card is not None:
            card.app["source"] = source

    def install_selected_apps(self):
        selection = self.installer_tab.selected_apps()
        if not selection:
            self.notify(self._tr("installer_nothing_selected", "No application selected.", "Nu a fost selectată nicio aplicație."))
            return
        self._start_installer_job(selection, self._tr("installer_installing_selected", "Installing selected applications...", "Se instalează aplicațiile selectate..."), mode="install")

    def remove_selected_apps(self):
        selection = self.installer_tab.selected_apps()
        if not selection:
            self.notify(self._tr("installer_nothing_selected", "No application selected.", "Nu a fost selectată nicio aplicație."))
            return
        self._start_installer_job(selection, self._tr("installer_removing_selected", "Removing selected applications...", "Se elimină aplicațiile selectate..."), mode="remove")

    def update_selected_apps(self):
        selection = self.installer_tab.selected_apps()
        if not selection:
            self.notify(self._tr("installer_nothing_selected", "No application selected.", "Nu a fost selectată nicio aplicație."))
            return
        self._start_installer_job(selection, self._tr("installer_updating_selected", "Updating selected applications...", "Se actualizează aplicațiile selectate..."), mode="update")

    def install_one_app(self, app_id: str):
        card = self.installer_tab.cards.get(app_id)
        if card is None:
            return
        app = dict(card.app)
        app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
        self._start_installer_job([app], self._tr("installer_installing_one", "Installing: {name}", "Se instalează: {name}", name=app["name"]), mode="install")

    def remove_one_app(self, app_id: str):
        card = self.installer_tab.cards.get(app_id)
        if card is None:
            return
        app = dict(card.app)
        app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
        self._start_installer_job([app], self._tr("installer_removing_one", "Removing: {name}", "Se elimină: {name}", name=app["name"]), mode="remove")

    def update_one_app(self, app_id: str):
        card = self.installer_tab.cards.get(app_id)
        if card is None:
            return
        app = dict(card.app)
        app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
        self._start_installer_job([app], self._tr("installer_updating_one", "Updating: {name}", "Se actualizează: {name}", name=app["name"]), mode="update")

    def _start_installer_job(self, selection: list[dict], overlay_text: str, mode: str = "install"):
        if self.installer_worker is not None and self.installer_worker.isRunning():
            self.notify(self._tr("maintenance_running", "Another background job is already running.", "O altă operațiune rulează deja."))
            return
        self.show_busy_overlay(overlay_text, self._tr("please_wait", "Please wait...", "Te rog așteaptă..."))
        self.installer_worker = InstallerWorker(selection, mode=mode)
        self.installer_worker.output_signal.connect(self.on_installer_output)
        self.installer_worker.error_signal.connect(self.on_installer_error)
        self.installer_worker.finished_signal.connect(self.on_installer_finished)
        self.installer_worker.start()

    def on_installer_output(self, output: str):
        if output:
            self.append_log("\n=== Installer ===")
            self.append_log(output)

    def on_installer_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
        self.append_log(f"Installer error: {message}")

    def on_installer_finished(self):
        self.installer_worker = None
        self.hide_busy_overlay()
        self.refresh_installer_catalog(self.installer_tab.search.text())
        if self._loaded_sections["packages"]:
            self.refresh_packages(update_title_only=False)
        else:
            self.refresh_packages(update_title_only=True)
        self.refresh_cleaner_targets()
        self._loaded_sections["cleaner"] = True
        QApplication.processEvents()
        self.notify(self._tr("installer_done", "Installer action completed.", "Operațiunea Installer s-a încheiat."))

    def remove_old_kernels(self):
        commands = removal_commands_for_suggested()
        if not commands:
            QMessageBox.information(self, "Info", self._tr("no_old_kernels", "No old kernels found.", "Nu au fost găsite kernel-uri vechi."))
            return

        answer = QMessageBox.question(
            self,
            "Confirm",
            self._tr("confirm_remove_kernels", "Remove suggested old kernels?", "Elimini kernel-urile vechi sugerate?"),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.set_activity(self._tr("cleaning_kernels", "Removing old kernels...", "Se elimină kernel-urile vechi..."), busy=True)
        self.append_log("\n=== Kernel cleanup ===")
        code = self.runner.run(commands, requires_root=True)
        if code != 0:
            QMessageBox.critical(self, "Error", f"{self._tr('action_failed', 'Action failed with exit code:')} {code}")
        self.refresh_kernel_analysis()
        self.set_activity(self._tr("ready", "Ready", "Gata"), busy=False)

    def refresh_about_tab(self):
        self.about_tab.set_current_version(APP_VERSION)
        self.about_tab.set_texts(self._about_texts())

        if self.release_error:
            self.about_tab.set_error(self.release_error)
        elif self.release_info is not None:
            self.about_tab.set_release_info(self.release_info)
        else:
            self.about_tab.set_checking()

        self._loaded_sections["about"] = True

    def check_latest_release(self):
        if self.release_worker is not None and self.release_worker.isRunning():
            return

        self.release_error = ""
        self.about_tab.set_checking()
        self.set_status(self._tr("about_checking", "Checking GitHub releases...", "Se verifică release-urile GitHub..."))

        self.release_worker = ReleaseCheckWorker(LATEST_RELEASE_API_URL, APP_VERSION)
        self.release_worker.result_signal.connect(self.on_release_check_success)
        self.release_worker.error_signal.connect(self.on_release_check_error)
        self.release_worker.finished.connect(self.on_release_check_finished)
        self.release_worker.start()

    def on_release_check_success(self, info: dict):
        self.release_info = info or {}
        self.release_error = ""
        self.refresh_about_tab()

        if self.release_info.get("has_update"):
            latest_version = str(self.release_info.get("latest_version") or "").strip()
            if latest_version and latest_version != self._update_notified_version:
                self.notify(
                    self._tr(
                        "about_update_available",
                        "A newer version is available: {version}.",
                        "Este disponibilă o versiune mai nouă: {version}.",
                        version=latest_version,
                    )
                )
                self._update_notified_version = latest_version
        else:
            self.set_status(self._tr("about_up_to_date", "You are using the latest available version.", "Folosești deja cea mai nouă versiune disponibilă."))

    def on_release_check_error(self, message: str):
        self.release_error = message or self._tr("about_unavailable", "Could not check GitHub releases right now.", "Release-urile GitHub nu pot fi verificate acum.")
        self.refresh_about_tab()
        self.set_status(self.release_error)

    def on_release_check_finished(self):
        self.release_worker = None