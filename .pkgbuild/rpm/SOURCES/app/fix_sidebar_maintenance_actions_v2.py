from pathlib import Path
import shutil

UI_MAIN = Path('app/ui_main.py')


def must_replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Nu am găsit exact o potrivire pentru {label}. Găsite: {count}")
    return text.replace(old, new, 1)


def must_replace_count(text: str, old: str, new: str, count_expected: int, label: str) -> str:
    count = text.count(old)
    if count != count_expected:
        raise RuntimeError(f"Nu am găsit exact {count_expected} potriviri pentru {label}. Găsite: {count}")
    return text.replace(old, new, count_expected)


def main() -> None:
    if not UI_MAIN.exists():
        raise RuntimeError("Nu există fișierul app/ui_main.py în directorul curent.")

    text = UI_MAIN.read_text(encoding='utf-8')

    text = must_replace_once(
        text,
        "class CleanerWorker(QThread):\n",
        """class ActionWorker(QThread):\n    log_signal = pyqtSignal(str)\n    error_signal = pyqtSignal(str)\n    finished_signal = pyqtSignal(int)\n\n    def __init__(self, commands, requires_root: bool = True):\n        super().__init__()\n        self.commands = commands\n        self.requires_root = requires_root\n\n    def run(self):\n        try:\n            runner = CommandRunner(self.log_signal.emit)\n            code = runner.run(self.commands, requires_root=self.requires_root)\n            self.finished_signal.emit(code)\n        except Exception as exc:\n            self.error_signal.emit(str(exc))\n            self.finished_signal.emit(1)\n\n\nclass CleanerWorker(QThread):\n""",
        "ActionWorker",
    )

    text = must_replace_once(
        text,
        """        self.worker = None\n        self.cleaner_worker = None\n        self.installer_worker = None\n        self.release_worker = None\n""",
        """        self.worker = None\n        self.action_worker = None\n        self.cleaner_worker = None\n        self.installer_worker = None\n        self.release_worker = None\n        self.current_action_label = \"\"\n        self.maintenance_action_buttons = []\n""",
        "worker attributes",
    )

    text = must_replace_once(
        text,
        "    def _theme_button_text(self) -> str:\n",
        """    def _maintenance_busy(self) -> bool:\n        return bool(\n            (self.worker is not None and self.worker.isRunning())\n            or (self.action_worker is not None and self.action_worker.isRunning())\n        )\n\n    def _set_maintenance_controls_enabled(self, enabled: bool):\n        for button in self.maintenance_action_buttons:\n            button.setEnabled(enabled)\n        self.maintenance_tab.full_btn.setEnabled(enabled)\n\n    def _theme_button_text(self) -> str:\n""",
        "maintenance helpers",
    )

    text = must_replace_count(
        text,
        "if not (self.worker and self.worker.isRunning()):",
        "if not self._maintenance_busy():",
        2,
        "maintenance busy checks",
    )

    text = must_replace_once(
        text,
        """        self.rebuild_maintenance_actions()\n        if not self._maintenance_busy():\n""",
        """        self.rebuild_maintenance_actions()\n        self._set_maintenance_controls_enabled(not self._maintenance_busy())\n        if not self._maintenance_busy():\n""",
        "retranslate maintenance controls",
    )

    text = must_replace_once(
        text,
        """    def rebuild_maintenance_actions(self):\n        layout = self.maintenance_tab.actions_layout\n""",
        """    def rebuild_maintenance_actions(self):\n        self.maintenance_action_buttons = []\n        layout = self.maintenance_tab.actions_layout\n""",
        "rebuild maintenance header",
    )

    text = must_replace_once(
        text,
        """            button.clicked.connect(lambda _checked=False, idx=index: self.run_action_by_index(idx))\n            row, column = divmod(index, max_columns)\n            layout.addWidget(button, row, column)\n""",
        """            button.clicked.connect(lambda _checked=False, idx=index: self.run_action_by_index(idx))\n            button.setEnabled(not self._maintenance_busy())\n            self.maintenance_action_buttons.append(button)\n            row, column = divmod(index, max_columns)\n            layout.addWidget(button, row, column)\n""",
        "rebuild maintenance buttons",
    )

    text = must_replace_once(
        text,
        """        self.maintenance_tab.full_btn.setMinimumHeight(42)\n        row, column = divmod(full_index, max_columns)\n""",
        """        self.maintenance_tab.full_btn.setMinimumHeight(42)\n        self.maintenance_tab.full_btn.setEnabled(not self._maintenance_busy())\n        row, column = divmod(full_index, max_columns)\n""",
        "full maintenance button state",
    )

    text = must_replace_once(
        text,
        """    def run_action_by_index(self, index: int):\n        if not 0 <= index < len(self.actions):\n            QMessageBox.warning(\n                self,\n                \"Warning\",\n                self._tr(\"warning_select_action\", \"Please select an action first.\", \"Selectează mai întâi o acțiune.\"),\n            )\n            return\n\n        action = self.actions[index]\n        label = action[\"label_en\"] if self.i18n.lang == \"en\" else action[\"label_ro\"]\n        description = action[\"description_en\"] if self.i18n.lang == \"en\" else action[\"description_ro\"]\n\n        self.set_activity(self._tr(\"running_label\", \"Running: {label}\", \"Se rulează: {label}\", label=label), busy=True)\n        self.append_log(f\"\\n=== {label} ===\")\n        self.append_log(description)\n        self.append_maintenance_log(f\"\\n=== {label} ===\")\n        self.append_maintenance_log(description)\n\n        code = self.runner.run(action[\"commands\"], requires_root=action.get(\"root\", True))\n        if code != 0:\n            QMessageBox.critical(self, \"Error\", f\"{self._tr('action_failed', 'Action failed with exit code:')} {code}\")\n\n        self.refresh_all()\n        self.set_activity(self._tr(\"ready\", \"Ready\", \"Gata\"), busy=False)\n""",
        """    def run_action_by_index(self, index: int):\n        if self._maintenance_busy():\n            QMessageBox.information(\n                self,\n                \"Info\",\n                self._tr(\n                    \"maintenance_running\",\n                    \"Another maintenance task is already running.\",\n                    \"O altă acțiune de mentenanță rulează deja.\",\n                ),\n            )\n            return\n\n        if not 0 <= index < len(self.actions):\n            QMessageBox.warning(\n                self,\n                \"Warning\",\n                self._tr(\"warning_select_action\", \"Please select an action first.\", \"Selectează mai întâi o acțiune.\"),\n            )\n            return\n\n        action = self.actions[index]\n        label = action[\"label_en\"] if self.i18n.lang == \"en\" else action[\"label_ro\"]\n        description = action[\"description_en\"] if self.i18n.lang == \"en\" else action[\"description_ro\"]\n\n        self.current_action_label = label\n        self.tabs.setCurrentWidget(self.maintenance_tab)\n        self.sync_section_selection(self.tabs.indexOf(self.maintenance_tab))\n        self.maintenance_tab.progress.setRange(0, 0)\n        self.maintenance_tab.status_label.setText(\n            self._tr(\"running_label\", \"Running: {label}\", \"Se rulează: {label}\", label=label)\n        )\n        self.maintenance_tab.step_label.setText(\n            self._tr(\n                \"maintenance_single_action_step\",\n                \"Command is running and live output is shown below.\",\n                \"Comanda rulează, iar output-ul live este afișat mai jos.\",\n            )\n        )\n        self.maintenance_tab.eta_label.setText(\n            self._tr(\n                \"maintenance_single_action_state\",\n                \"Status: in progress\",\n                \"Stare: în desfășurare\",\n            )\n        )\n        self.set_activity(self._tr(\"running_label\", \"Running: {label}\", \"Se rulează: {label}\", label=label), busy=True)\n        self._set_maintenance_controls_enabled(False)\n\n        self.append_log(f\"\\n=== {label} ===\")\n        self.append_log(description)\n        self.append_maintenance_log(f\"\\n=== {label} ===\")\n        self.append_maintenance_log(description)\n\n        self.action_worker = ActionWorker(action[\"commands\"], requires_root=action.get(\"root\", True))\n        self.action_worker.log_signal.connect(self.append_log)\n        self.action_worker.log_signal.connect(self.append_maintenance_log)\n        self.action_worker.error_signal.connect(self.on_single_action_error)\n        self.action_worker.finished_signal.connect(self.on_single_action_finished)\n        self.action_worker.start()\n\n    def on_single_action_error(self, message: str):\n        self.append_log(f\"Error: {message}\")\n        self.append_maintenance_log(f\"Error: {message}\")\n        QMessageBox.critical(self, \"Error\", message)\n\n    def on_single_action_finished(self, code: int):\n        label = self.current_action_label or self._tr(\"maintenance\", \"Maintenance\", \"Mentenanță\")\n        self.action_worker = None\n        self._set_maintenance_controls_enabled(True)\n        self.maintenance_tab.progress.setRange(0, 100)\n\n        self.refresh_all()\n\n        if code == 0:\n            message = self._tr(\n                \"maintenance_single_action_done\",\n                \"Action completed successfully: {label}\",\n                \"Acțiune finalizată cu succes: {label}\",\n                label=label,\n            )\n            self.maintenance_tab.progress.setValue(100)\n            self.maintenance_tab.status_label.setText(message)\n            self.maintenance_tab.step_label.setText(\n                self._tr(\n                    \"maintenance_single_action_done_step\",\n                    \"The command finished successfully.\",\n                    \"Comanda s-a încheiat cu succes.\",\n                )\n            )\n            self.maintenance_tab.eta_label.setText(\n                self._tr(\n                    \"maintenance_single_action_done_state\",\n                    \"Status: completed\",\n                    \"Stare: finalizată\",\n                )\n            )\n            self.append_log(message)\n            self.append_maintenance_log(message)\n            self.set_activity(message, busy=False)\n            self.notify(message)\n        else:\n            message = self._tr(\n                \"maintenance_single_action_failed\",\n                \"Action failed: {label} (exit code {code})\",\n                \"Acțiune eșuată: {label} (cod de ieșire {code})\",\n                label=label,\n                code=code,\n            )\n            self.maintenance_tab.progress.setValue(0)\n            self.maintenance_tab.status_label.setText(message)\n            self.maintenance_tab.step_label.setText(\n                self._tr(\n                    \"maintenance_single_action_failed_step\",\n                    \"The command finished with an error.\",\n                    \"Comanda s-a încheiat cu eroare.\",\n                )\n            )\n            self.maintenance_tab.eta_label.setText(\n                self._tr(\n                    \"maintenance_single_action_failed_state\",\n                    \"Status: failed\",\n                    \"Stare: eșuată\",\n                )\n            )\n            self.append_log(message)\n            self.append_maintenance_log(message)\n            self.set_activity(message, busy=False)\n            QMessageBox.critical(self, \"Error\", message)\n\n        self.current_action_label = \"\"\n""",
        "run_action_by_index",
    )

    text = must_replace_once(
        text,
        "        self.maintenance_tab.full_btn.setEnabled(False)\n",
        "        self._set_maintenance_controls_enabled(False)\n",
        "disable maintenance controls",
    )

    text = must_replace_once(
        text,
        "        self.maintenance_tab.full_btn.setEnabled(True)\n",
        "        self._set_maintenance_controls_enabled(True)\n",
        "enable maintenance controls",
    )

    backup = UI_MAIN.with_suffix('.py.bak')
    shutil.copy2(UI_MAIN, backup)
    UI_MAIN.write_text(text, encoding='utf-8')
    print(f"Patch aplicat cu succes. Backup: {backup}")


if __name__ == '__main__':
    main()
