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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
import platform

from PyQt5.QtCore import QTimer
import threading

from core.commands import build_actions
from core.i18n import I18N
from core.runner import CommandRunner
from services.cleaner import clean_target, get_cleaner_targets, run_clean_command
from services.disk_analyzer import get_home_largest_files, get_home_top_directories, get_root_usage
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
from version import APP_VERSION


def _get_distribution():
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return platform.system()


class MaintenanceWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    started_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, i18n):
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

    def __init__(self, command):
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

    def __init__(self, selection, mode="install"):
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.i18n = I18N("en")
        self.actions = build_actions()
        self.worker = None
        self.cleaner_worker = None
        self.installer_worker = None
        self.overlay = None
        self.cleaner_overlay = None
        self._blur = None
        self.maintenance_had_error = False
        self.monitor = MonitorService(history=40)
        self.runner = CommandRunner(self.append_log)
        self.startup_rows = []
        self.service_rows = []
        self.package_rows = []
        self._building_startup_table = False
        self._building_services_table = False
        self.package_total_count = 0

        self.setWindowTitle(f"TuxPulse v{APP_VERSION}")
        self.resize(1460, 880)

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

        language_row = QHBoxLayout()
        self.language_label = QLabel()
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Română", "ro")
        self.language_combo.currentIndexChanged.connect(self.change_language)
        language_row.addWidget(self.language_label)
        language_row.addWidget(self.language_combo)

        self.actions_label = QLabel()
        self.actions_label.setObjectName("SectionTitle")
        self.action_list = QListWidget()
        self.action_list.setObjectName("ActionList")

        self.run_btn = QPushButton()
        self.run_btn.clicked.connect(self.run_selected_action)
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh_all)
        self.quick_full_btn = QPushButton()
        self.quick_full_btn.clicked.connect(self.start_full_maintenance)
        self.activity_label = QLabel()
        self.activity_label.setObjectName("Subtitle")
        self.activity_label.setWordWrap(True)
        self.activity_label.setText(f"v{APP_VERSION}")

        sidebar_layout.addWidget(self.title_label)
        sidebar_layout.addWidget(self.subtitle_label)
        sidebar_layout.addWidget(self.distribution_label)
        sidebar_layout.addLayout(language_row)
        sidebar_layout.addWidget(self.actions_label)
        sidebar_layout.addWidget(self.action_list, 1)
        sidebar_layout.addWidget(self.run_btn)
        sidebar_layout.addWidget(self.refresh_btn)
        sidebar_layout.addWidget(self.quick_full_btn)
        sidebar_layout.addWidget(self.activity_label)

        self.panel = QFrame()
        self.panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("Tabs")

        self.dashboard_tab = DashboardTab()
        self.maintenance_tab = MaintenanceTab()
        self.disk_tab = DiskTab()
        self.kernel_tab = KernelTab()
        self.cleaner_tab = CleanerTab()
        self.startup_tab = StartupTab()
        self.services_tab = ServicesTab()
        self.packages_tab = PackagesTab()
        self.installer_tab = InstallerTab()

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
        self.installer_tab.search_changed.connect(self.refresh_installer_catalog)
        self.installer_tab.install_selected_requested.connect(self.install_selected_apps)
        self.installer_tab.remove_selected_requested.connect(self.remove_selected_apps)
        self.installer_tab.update_selected_requested.connect(self.update_selected_apps)
        self.installer_tab.install_one_requested.connect(self.install_one_app)
        self.installer_tab.remove_one_requested.connect(self.remove_one_app)
        self.installer_tab.update_one_requested.connect(self.update_one_app)
        self.installer_tab.source_changed.connect(self.on_installer_source_changed)

        self.tabs.addTab(self.dashboard_tab, "")
        self.tabs.addTab(self.maintenance_tab, "")
        self.tabs.addTab(self.disk_tab, "")
        self.tabs.addTab(self.kernel_tab, "")
        self.tabs.addTab(self.cleaner_tab, "")
        self.tabs.addTab(self.startup_tab, "")
        self.tabs.addTab(self.services_tab, "")
        self.tabs.addTab(self.packages_tab, "")
        self.tabs.addTab(self.installer_tab, "")

        panel_layout.addWidget(self.tabs)
        root.addWidget(self.sidebar, 3)
        root.addWidget(self.panel, 8)

        self.statusBar().showMessage(f"{self.i18n.t('status_prefix')} {self.i18n.t('ready')}")
        self.apply_style()
        self.update_action_list()
        self.retranslate_ui()
        self.refresh_all(initial=True)
        self.append_log(self.i18n.t("info_started"))

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_monitoring)
        self.timer.start(1000)
        self.update_monitoring()

    def apply_style(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #0f172a;
                color: #e5e7eb;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 13px;
            }
            QFrame#Sidebar, QFrame#Panel, QFrame#InstallerCard {
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 14px;
            }
            QLabel#Title {
                font-size: 28px;
                font-weight: bold;
                color: #f8fafc;
            }
            QLabel#Subtitle {
                color: #94a3b8;
            }
            QLabel#SectionTitle {
                font-size: 16px;
                font-weight: bold;
                color: #f8fafc;
            }
            QListWidget, QTextEdit, QTabWidget::pane, QTableWidget, QProgressBar, QLineEdit, QScrollArea {
                background: #0b1220;
                border: 1px solid #243041;
                border-radius: 10px;
                padding: 8px;
            }
            QComboBox {
                background-color: #0b1220;
                color: #e5e7eb;
                border: 1px solid #243041;
                border-radius: 8px;
                padding: 6px 10px;
                min-height: 22px;
            }
            QComboBox QAbstractItemView {
                background-color: #0b1220;
                color: #e5e7eb;
                selection-background-color: #2563eb;
                border: 1px solid #243041;
                outline: 0;
            }
            QListWidget::item {
                padding: 10px;
                margin: 3px 0;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background: #2563eb;
                color: white;
            }
            QTabBar::tab {
                background: #0b1220;
                border: 1px solid #243041;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 14px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #2563eb;
                color: white;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                min-height: 40px;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #334155;
                color: #94a3b8;
            }
            QHeaderView::section {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid #243041;
                padding: 6px;
            }
            QProgressBar::chunk {
                background: #22c55e;
                border-radius: 8px;
            }
            QStatusBar {
                background: #111827;
                color: #cbd5e1;
            }
            """
        )

    def set_status(self, text):
        self.statusBar().showMessage(f"{self.i18n.t('status_prefix')} {text}", 5000)

    def notify(self, text):
        try:
            Toast(self, text)
        except Exception:
            pass
        self.set_status(text)

    def set_activity(self, text, busy=False):
        self.maintenance_tab.status_label.setText(text)
        self.set_status(text)
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def show_busy_overlay(self, message, detail=None, blur=True):
        if blur:
            self._blur = QGraphicsBlurEffect()
            self._blur.setBlurRadius(8)
            self.centralWidget().setGraphicsEffect(self._blur)
        else:
            self._blur = None
        self.overlay = ActivityOverlay(self, message, detail or self.i18n.t("please_wait"))
        self.overlay.sync_to_parent()
        self.overlay.show_overlay()
        QApplication.processEvents()

    def hide_busy_overlay(self):
        if self.overlay is not None:
            self.overlay.hide_overlay()
            self.overlay.deleteLater()
            self.overlay = None
        self.centralWidget().setGraphicsEffect(None)

    def resizeEvent(self, event):
        if self.overlay is not None and self.overlay.isVisible():
            self.overlay.sync_to_parent()
        if self.cleaner_overlay is not None and self.cleaner_overlay.isVisible():
            self.cleaner_overlay.sync_to_parent()
        super().resizeEvent(event)

    def change_language(self):
        lang = self.language_combo.currentData()
        self.show_busy_overlay(self.i18n.t("switching_language"))
        try:
            self.i18n.set_lang(lang)
            self.retranslate_ui()
            self.update_action_list()
            self.refresh_disk_analysis()
            self.refresh_kernel_analysis()
            self.refresh_startup_apps()
            self.refresh_services()
            self.refresh_packages(update_title_only=True)
            self.refresh_cleaner_targets()
            self.refresh_installer_catalog(self.installer_tab.search.text())
            QApplication.processEvents()
        finally:
            self.hide_busy_overlay()

    def retranslate_ui(self):
        self.setWindowTitle(f"TuxPulse v{APP_VERSION}")
        self.title_label.setText(f"{self.i18n.t('app_name')} v{APP_VERSION}")
        self.subtitle_label.setText(self.i18n.t("subtitle"))
        self.distribution_label.setText(f"{self.i18n.t('distribution')}: {_get_distribution()}")
        self.language_label.setText(self.i18n.t("language"))
        self.actions_label.setText(self.i18n.t("system_actions"))
        self.run_btn.setText(self.i18n.t("run_action"))
        self.refresh_btn.setText(self.i18n.t("refresh"))
        self.quick_full_btn.setText(self.i18n.t("full_maintenance"))
        self.activity_label.setText(f"v{APP_VERSION}")
        if not (self.worker and self.worker.isRunning()):
            self.set_status(self.i18n.t("ready"))

        self.dashboard_tab.info_title.setText(self.i18n.t("system_info"))
        self.dashboard_tab.log_title.setText(self.i18n.t("execution_log"))

        self.maintenance_tab.title.setText(self.i18n.t("maintenance"))
        self.maintenance_tab.full_btn.setText(self.i18n.t("full_maintenance"))
        self.maintenance_tab.output_title.setText(self.i18n.t("maintenance_live_output"))
        if not (self.worker and self.worker.isRunning()):
            self.maintenance_tab.status_label.setText(self.i18n.t("maintenance_idle"))
            self.maintenance_tab.step_label.setText(self.i18n.t("step_waiting"))
            self.maintenance_tab.eta_label.setText(self.i18n.t("eta_waiting"))

        self.disk_tab.partition_title.setText(self.i18n.t("disk_partition_usage"))
        self.disk_tab.dirs_title.setText(self.i18n.t("largest_directories"))
        self.disk_tab.files_title.setText(self.i18n.t("largest_files"))
        self.disk_tab.analyze_btn.setText(self.i18n.t("analyze_disk"))

        self.kernel_tab.title.setText(self.i18n.t("kernel_tools"))
        self.kernel_tab.analyze_btn.setText(self.i18n.t("analyze_kernels"))
        self.kernel_tab.remove_btn.setText(self.i18n.t("remove_old_kernels"))

        self.cleaner_tab.title.setText(self.i18n.t("cleaner_title"))
        self.cleaner_tab.clean_btn.setText(self.i18n.t("run_action"))

        self.startup_tab.set_texts({
            "title": self.i18n.t("startup_title"),
            "hint": self.i18n.t("startup_hint"),
            "name": self.i18n.t("startup_name"),
            "exec": self.i18n.t("startup_exec"),
            "enabled": self.i18n.t("startup_enabled"),
            "scope": self.i18n.t("startup_scope"),
        })

        self.services_tab.set_texts({
            "title": self.i18n.t("services_title"),
            "hint": self.i18n.t("services_hint"),
            "service": self.i18n.t("service"),
            "state": self.i18n.t("state"),
        })

        self.packages_tab.set_texts({
            "title": self.i18n.t("installed_packages_count", count=self.package_total_count),
            "search_placeholder": self.i18n.t("packages_search_placeholder"),
            "search": self.i18n.t("search"),
            "installed": self.i18n.t("installed"),
            "upgradable": self.i18n.t("upgradable"),
            "remove": self.i18n.t("remove_selected"),
            "purge": self.i18n.t("purge_selected"),
            "package": self.i18n.t("package"),
            "version": self.i18n.t("version"),
            "status": self.i18n.t("status"),
            "details": self.i18n.t("package_details"),
        }, total_count=self.package_total_count)

        self.installer_tab.set_texts({
            "title": self.i18n.t("installer_title"),
            "subtitle": self.i18n.t("installer_subtitle"),
            "search_placeholder": self.i18n.t("installer_search_placeholder"),
            "install_selected": self.i18n.t("installer_install_selected"),
            "remove_selected": self.i18n.t("installer_remove_selected"),
            "update_selected": self.i18n.t("installer_update_selected"),
            "status": self.i18n.t("installer_status_hint"),
            "install": self.i18n.t("installer_install"),
            "remove": self.i18n.t("installer_remove"),
            "update": self.i18n.t("installer_update"),
            "source": self.i18n.t("installer_source"),
            "native": self.i18n.t("installer_native"),
            "flatpak": self.i18n.t("installer_flatpak"),
            "installed_native": self.i18n.t("installer_installed_native"),
            "installed_flatpak": self.i18n.t("installer_installed_flatpak"),
            "available": self.i18n.t("installer_available"),
            "not_available": self.i18n.t("installer_not_available"),
        })

        self.tabs.setTabText(0, self.i18n.t("dashboard"))
        self.tabs.setTabText(1, self.i18n.t("maintenance"))
        self.tabs.setTabText(2, self.i18n.t("disk_analysis"))
        self.tabs.setTabText(3, self.i18n.t("kernel_tools"))
        self.tabs.setTabText(4, self.i18n.t("cleaner"))
        self.tabs.setTabText(5, self.i18n.t("startup_apps"))
        self.tabs.setTabText(6, self.i18n.t("services"))
        self.tabs.setTabText(7, self.i18n.t("packages"))
        self.tabs.setTabText(8, self.i18n.t("installer_title"))

    def update_action_list(self):
        current_row = self.action_list.currentRow()
        self.action_list.clear()
        for action in self.actions:
            label = action["label_en"] if self.i18n.lang == "en" else action["label_ro"]
            description = action["description_en"] if self.i18n.lang == "en" else action["description_ro"]
            item = QListWidgetItem(label)
            item.setToolTip(description)
            self.action_list.addItem(item)
        if self.action_list.count() > 0:
            self.action_list.setCurrentRow(max(0, current_row))

    def append_log(self, text):
        cursor = self.dashboard_tab.log_box.textCursor()
        cursor.movePosition(cursor.End)
        self.dashboard_tab.log_box.setTextCursor(cursor)
        self.dashboard_tab.log_box.insertPlainText(text + ("\n" if not text.endswith("\n") else ""))

    def append_maintenance_log(self, text):
        cursor = self.maintenance_tab.log_box.textCursor()
        cursor.movePosition(cursor.End)
        self.maintenance_tab.log_box.setTextCursor(cursor)
        self.maintenance_tab.log_box.insertPlainText(text + ("\n" if not text.endswith("\n") else ""))

    def refresh_all(self, initial=False):
        self.dashboard_tab.info_box.setPlainText(build_system_summary())
        self.refresh_disk_analysis()
        self.refresh_kernel_analysis()
        self.refresh_startup_apps()
        self.refresh_services()
        self.refresh_packages(update_title_only=False)
        self.refresh_cleaner_targets()
        self.refresh_installer_catalog(self.installer_tab.search.text())
        self.retranslate_ui()
        if not initial:
            self.append_log(self.i18n.t("info_refreshed"))
            self.set_status(self.i18n.t("information_refreshed_status"))

    def run_selected_action(self):
        row = self.action_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", self.i18n.t("warning_select_action"))
            return
        action = self.actions[row]
        label = action["label_en"] if self.i18n.lang == "en" else action["label_ro"]
        description = action["description_en"] if self.i18n.lang == "en" else action["description_ro"]
        self.set_activity(self.i18n.t("running_label", label=label), busy=True)
        self.append_log(f"\n=== {label} ===")
        self.append_log(description)
        code = self.runner.run(action["commands"], requires_root=action.get("root", True))
        if code != 0:
            QMessageBox.critical(self, "Error", f"{self.i18n.t('action_failed')} {code}")
        self.refresh_all()
        self.set_activity(self.i18n.t("ready"), busy=False)

    def update_monitoring(self):
        data = self.monitor.snapshot()
        self.dashboard_tab.cpu_chart.update_series(data["cpu_history"], self.i18n.t("cpu_usage"))
        self.dashboard_tab.ram_chart.update_series(data["ram_history"], self.i18n.t("ram_usage"))
        self.dashboard_tab.disk_chart.update_series(data["disk_history"], self.i18n.t("disk_usage"))
        self.dashboard_tab.net_chart.update_series(data["net_history"], self.i18n.t("network_usage"))

    def refresh_disk_analysis(self):
        usage = get_root_usage()
        self.disk_tab.disk_pie.update_usage(usage["used_gb"], usage["free_gb"], self.i18n.t("disk_partition_usage"))
        dirs = get_home_top_directories()
        labels = [item["name"] for item in dirs] if dirs else ["N/A"]
        values = [item["size_mb"] for item in dirs] if dirs else [0]
        self.disk_tab.disk_bar.update_bars(labels, values, self.i18n.t("largest_directories"))
        self.disk_tab.files_list.clear()
        for item in get_home_largest_files(limit=20):
            self.disk_tab.files_list.addItem(f"{item['size_mb']:>8.2f} MB  {item['path']}")

    def refresh_kernel_analysis(self):
        report = get_kernel_report()
        lines = [
            f"{self.i18n.t('current_kernel')}: {report['current']}",
            "",
            f"{self.i18n.t('installed_kernels')}:",
        ]
        lines.extend(report["installed"] or ["-"])
        lines += ["", f"{self.i18n.t('suggested_old_kernels')}:"]
        lines.extend(report["suggested"] or ["-"])
        self.kernel_tab.text.setPlainText("\n".join(lines))

    def refresh_startup_apps(self):
        self._building_startup_table = True
        self.startup_rows = list_startup_apps()
        self.startup_tab.populate(
            self.startup_rows,
            yes_text=self.i18n.t("yes"),
            no_text=self.i18n.t("no"),
            scope_map={"user": self.i18n.t("scope_user"), "system": self.i18n.t("scope_system")},
        )
        self._building_startup_table = False

    def refresh_services(self):
        self._building_services_table = True
        self.service_rows = list_services(limit=200)
        self.services_tab.populate(
            self.service_rows,
            state_labels={
                "Running": self.i18n.t("running"),
                "Stopped": self.i18n.t("stopped"),
                "Disabled": self.i18n.t("disabled"),
            },
        )
        self._building_services_table = False

    def refresh_packages(self, update_title_only=False):
        self.package_total_count = count_installed_packages()
        if not update_title_only:
            self.package_rows = list_installed_packages(limit=300, search="")
            self.packages_tab.populate(self.package_rows)
        self.retranslate_ui()
        self.set_activity(self.i18n.t("showing_installed_packages"), busy=False)

    def show_upgradable_packages(self):
        self.package_rows = list_upgradable_packages(limit=300)
        self.packages_tab.populate(self.package_rows)
        self.set_activity(self.i18n.t("showing_upgradable_packages"), busy=False)

    def search_packages(self, query):
        self.package_rows = list_installed_packages(limit=300, search=query)
        self.packages_tab.populate(self.package_rows)
        query_label = query or self.i18n.t("packages")
        self.set_activity(self.i18n.t("search_results_for", query=query_label), busy=False)

    def remove_selected_package(self, package_name):
        answer = QMessageBox.question(
            self,
            "Confirm",
            self.i18n.t("remove_package_confirm", name=package_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.set_activity(self.i18n.t("removing_package", name=package_name), busy=True)
        self.append_log(f"\n=== Remove package: {package_name} ===")
        try:
            output = remove_package(package_name)
            self.append_log(output)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.append_log(f"Error: {exc}")
        self.refresh_packages()
        self.set_activity(self.i18n.t("ready"), busy=False)

    def purge_selected_package(self, package_name):
        answer = QMessageBox.question(
            self,
            "Confirm",
            self.i18n.t("purge_package_confirm", name=package_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.set_activity(self.i18n.t("removing_package", name=package_name), busy=True)
        self.append_log(f"\n=== Purge package: {package_name} ===")
        try:
            output = purge_package(package_name)
            self.append_log(output)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.append_log(f"Error: {exc}")
        self.refresh_packages()
        self.set_activity(self.i18n.t("ready"), busy=False)

    def refresh_cleaner_targets(self):
        self.cleaner_tab.targets.clear()
        for target in get_cleaner_targets():
            self.cleaner_tab.targets.addItem(target["name"])

    def clean_selected_target(self):
        current = self.cleaner_tab.targets.currentItem()
        if current is None:
            QMessageBox.warning(self, "Warning", self.i18n.t("warning_select_action"))
            return
        name = current.text()
        command = clean_target(name)
        self.cleaner_overlay = ActivityOverlay(self, self.i18n.t("cleaning_label", name=name), self.i18n.t("please_wait"))
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
        self.notify(self.i18n.t("toast_cleaner_done"))

    def cleaner_error(self, message):
        if self.cleaner_overlay is not None:
            self.cleaner_overlay.hide_overlay()
            self.cleaner_overlay.deleteLater()
            self.cleaner_overlay = None
        QMessageBox.critical(self, "Error", message)

    def on_startup_enabled_changed(self, path, enabled):
        if self._building_startup_table:
            return
        try:
            set_startup_enabled(path, enabled)
            state = self.i18n.t("yes") if enabled else self.i18n.t("no")
            self.append_log(f"Startup entry {path} {state}.")
            self.set_activity(self.i18n.t("startup_updated", path=path), busy=False)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
        self.refresh_startup_apps()

    def on_service_state_changed(self, service_name, desired_state):
        if self._building_services_table:
            return
        try:
            desired_label = {
                "Running": self.i18n.t("running"),
                "Stopped": self.i18n.t("stopped"),
                "Disabled": self.i18n.t("disabled"),
            }.get(desired_state, desired_state)
            self.set_activity(self.i18n.t("service_changing", name=service_name, state=desired_label), busy=True)
            set_service_state(service_name, desired_state)
            self.append_log(f"Service {service_name} -> {desired_state}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            self.append_log(f"Error: {exc}")
        self.refresh_services()
        self.set_activity(self.i18n.t("ready"), busy=False)

    def start_full_maintenance(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Info", self.i18n.t("maintenance_running"))
            return
        self.maintenance_had_error = False
        self.maintenance_tab.progress.setValue(0)
        self.maintenance_tab.log_box.clear()
        self.maintenance_tab.step_label.setText(self.i18n.t("maintenance_starting"))
        self.maintenance_tab.eta_label.setText(self.i18n.t("eta_waiting"))
        self.quick_full_btn.setEnabled(False)
        self.maintenance_tab.full_btn.setEnabled(False)
        self.set_activity(self.i18n.t("maintenance_starting"), busy=True)
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

    def update_maintenance_progress(self, value):
        self.maintenance_tab.progress.setValue(value)

    def on_maintenance_error(self, message):
        self.maintenance_had_error = True
        self.append_log(f"Error: {message}")
        self.append_maintenance_log(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)

    def maintenance_finished(self):
        if not self.maintenance_had_error:
            self.append_log(self.i18n.t("maintenance_finished"))
            self.append_maintenance_log(self.i18n.t("maintenance_finished"))
            self.maintenance_tab.progress.setValue(100)
            self.notify(self.i18n.t("maintenance_finished"))
            self.set_activity(self.i18n.t("maintenance_finished_success_status"), busy=False)
        else:
            self.append_log(self.i18n.t("maintenance_finished_errors"))
            self.append_maintenance_log(self.i18n.t("maintenance_finished_errors"))
            self.set_activity(self.i18n.t("maintenance_finished_error_status"), busy=False)
        self.quick_full_btn.setEnabled(True)
        self.maintenance_tab.full_btn.setEnabled(True)
        self.refresh_all()

    def refresh_installer_catalog(self, query=""):
        data = apps_for_display(query)
        self.installer_tab.populate(data)
        self.retranslate_ui()

    def on_installer_source_changed(self, app_id, source):
        card = self.installer_tab.cards.get(app_id)
        if card is not None:
            card.app["source"] = source

    def install_selected_apps(self):
        selection = self.installer_tab.selected_apps()
        if not selection:
            self.notify(self.i18n.t("installer_nothing_selected"))
            return
        self._start_installer_job(selection, self.i18n.t("installer_installing_selected"), mode="install")

    def remove_selected_apps(self):
        selection = self.installer_tab.selected_apps()
        if not selection:
            self.notify(self.i18n.t("installer_nothing_selected"))
            return
        self._start_installer_job(selection, self.i18n.t("installer_removing_selected"), mode="remove")

    def update_selected_apps(self):
        selection = self.installer_tab.selected_apps()
        if not selection:
            self.notify(self.i18n.t("installer_nothing_selected"))
            return
        self._start_installer_job(selection, self.i18n.t("installer_updating_selected"), mode="update")

    def install_one_app(self, app_id):
        card = self.installer_tab.cards.get(app_id)
        if card is None:
            return
        app = dict(card.app)
        app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
        self._start_installer_job([app], self.i18n.t("installer_installing_one", name=app["name"]), mode="install")

    def remove_one_app(self, app_id):
        card = self.installer_tab.cards.get(app_id)
        if card is None:
            return
        app = dict(card.app)
        app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
        self._start_installer_job([app], self.i18n.t("installer_removing_one", name=app["name"]), mode="remove")

    def update_one_app(self, app_id):
        card = self.installer_tab.cards.get(app_id)
        if card is None:
            return
        app = dict(card.app)
        app["source"] = "flatpak" if card.flatpak_radio.isChecked() else "native"
        self._start_installer_job([app], self.i18n.t("installer_updating_one", name=app["name"]), mode="update")

    def _start_installer_job(self, selection, overlay_text, mode="install"):
        if self.installer_worker is not None and self.installer_worker.isRunning():
            self.notify(self.i18n.t("maintenance_running"))
            return
        self.show_busy_overlay(overlay_text, self.i18n.t("please_wait"))
        self.installer_worker = InstallerWorker(selection, mode=mode)
        self.installer_worker.output_signal.connect(self.on_installer_output)
        self.installer_worker.error_signal.connect(self.on_installer_error)
        self.installer_worker.finished_signal.connect(self.on_installer_finished)
        self.installer_worker.start()

    def on_installer_output(self, output):
        if output:
            self.append_log("\n=== Installer ===")
            self.append_log(output)

    def on_installer_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.append_log(f"Installer error: {message}")

    def on_installer_finished(self):
        self.hide_busy_overlay()
        self.refresh_installer_catalog(self.installer_tab.search.text())
        self.refresh_packages(update_title_only=False)
        self.refresh_cleaner_targets()
        QApplication.processEvents()
        self.notify(self.i18n.t("installer_done"))

    def remove_old_kernels(self):
        commands = removal_commands_for_suggested()
        if not commands:
            QMessageBox.information(self, "Info", self.i18n.t("no_old_kernels"))
            return
        answer = QMessageBox.question(self, "Confirm", self.i18n.t("confirm_remove_kernels"), QMessageBox.Yes | QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self.set_activity(self.i18n.t("cleaning_kernels"), busy=True)
        self.append_log("\n=== Kernel cleanup ===")
        code = self.runner.run(commands, requires_root=True)
        if code != 0:
            QMessageBox.critical(self, "Error", f"{self.i18n.t('action_failed')} {code}")
        self.refresh_kernel_analysis()
        self.set_activity(self.i18n.t("ready"), busy=False)
