import sys

if sys.platform == "darwin":
    from PySide6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QProgressBar,
        QTextEdit,
        QSlider,
        QFrame,
        QDialog,
        QDialogButtonBox,
        QRadioButton,
        QButtonGroup,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QCheckBox,
        QApplication,
        QScrollArea,
    )
    from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal, QObject
else:
    from PyQt6.QtWidgets import (
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QProgressBar,
        QTextEdit,
        QSlider,
        QFrame,
        QDialog,
        QDialogButtonBox,
        QRadioButton,
        QButtonGroup,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QCheckBox,
        QApplication,
        QScrollArea,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject

import core.config as config
from core.installer import (
    fetch_release_versions,
    fetch_fabric_versions,
    install_minecraft,
    install_fabric,
    install_mods,
    AVAILABLE_MODS,
)
from core.launcher import launch


# ── Workers ───────────────────────────────────────────────────────────────────


class Worker(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool, str)

    def __init__(self, task, **kwargs):
        super().__init__()
        self.task = task
        self.kwargs = kwargs

    def run(self):
        try:
            self.task(log=self.log.emit, progress=self.progress.emit, **self.kwargs)
            self.finished.emit(True, "Done!")
        except Exception as e:
            self.finished.emit(False, str(e))


class LaunchWorker(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mc_version, profile_type, fabric_profile_id, username, ram_gb):
        super().__init__()
        self.mc_version = mc_version
        self.profile_type = profile_type
        self.fabric_profile_id = fabric_profile_id
        self.username = username
        self.ram_gb = ram_gb

    def run(self):
        try:
            proc = launch(
                mc_version=self.mc_version,
                profile_type=self.profile_type,
                fabric_profile_id=self.fabric_profile_id,
                username=self.username,
                ram_gb=self.ram_gb,
                log=self.log.emit,
            )
            self.log.emit("🎮 Game launched!")
            for line in proc.stdout:
                self.log.emit(line.rstrip())
            proc.wait()
            self.finished.emit(True, f"Game exited (code {proc.returncode})")
        except Exception as e:
            self.finished.emit(False, str(e))


# ── New Profile Dialog ────────────────────────────────────────────────────────


class NewProfileDialog(QDialog):
    def __init__(
        self, all_versions: list[str], fabric_versions: list[str], parent=None
    ):
        super().__init__(parent)
        self.all_versions = all_versions
        self.fabric_versions = fabric_versions
        self.setWindowTitle("New Profile")
        self.setMinimumWidth(400)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Name
        layout.addWidget(self._lbl("Profile Name"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Survival World, Speedrun, etc.")
        layout.addWidget(self.name_edit)

        # Type
        layout.addWidget(self._lbl("Profile Type"))
        type_row = QHBoxLayout()
        self.fabric_radio = QRadioButton("Fabric + Mods")
        self.vanilla_radio = QRadioButton("Vanilla")
        self.fabric_radio.setChecked(True)
        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.fabric_radio)
        self.btn_group.addButton(self.vanilla_radio)
        type_row.addWidget(self.fabric_radio)
        type_row.addWidget(self.vanilla_radio)
        type_row.addStretch()
        layout.addLayout(type_row)

        # Version
        layout.addWidget(self._lbl("Minecraft Version"))
        self.version_list = QListWidget()
        self.version_list.setMaximumHeight(160)
        layout.addWidget(self.version_list)

        # Mods section (only shown for Fabric)
        self.mods_frame = QFrame()
        mods_layout = QVBoxLayout(self.mods_frame)
        mods_layout.setContentsMargins(0, 0, 0, 0)
        mods_layout.setSpacing(6)
        mods_layout.addWidget(self._lbl("Mods  (Fabric API always included)"))

        self.mod_checks = {}
        for key, mod in AVAILABLE_MODS.items():
            cb = QCheckBox(f"{mod['label']}  :  {mod['desc']}")
            cb.setChecked(True)
            self.mod_checks[key] = cb
            mods_layout.addWidget(cb)

        layout.addWidget(self.mods_frame)

        # Connect radio buttons to update version list + show/hide mods
        self.fabric_radio.toggled.connect(self._on_type_changed)
        self._on_type_changed(True)  # initial populate

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #6b7280; letter-spacing: 1px;"
        )
        return l

    def _on_type_changed(self, fabric_checked):
        self.version_list.clear()
        if self.fabric_radio.isChecked():
            versions = self.fabric_versions
            self.mods_frame.setVisible(True)
        else:
            versions = self.all_versions
            self.mods_frame.setVisible(False)
        for v in versions:
            self.version_list.addItem(v)
        if versions:
            self.version_list.setCurrentRow(0)

    def get_profile(self) -> dict | None:
        name = self.name_edit.text().strip()
        if not name:
            return None
        item = self.version_list.currentItem()
        if not item:
            return None
        mc_version = item.text()
        profile_type = "fabric" if self.fabric_radio.isChecked() else "vanilla"
        enabled_mods = (
            [key for key, cb in self.mod_checks.items() if cb.isChecked()]
            if profile_type == "fabric"
            else []
        )
        return {
            "name": name,
            "mc_version": mc_version,
            "type": profile_type,
            "mods": enabled_mods,
        }


# ── Stylesheet ────────────────────────────────────────────────────────────────

STYLE = """
QMainWindow, QWidget, QDialog {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel#title {
    font-size: 24px; font-weight: bold;
    color: #4ade80; letter-spacing: 2px;
}
QLabel#subtitle { font-size: 11px; color: #6b7280; }
QLineEdit, QComboBox {
    background-color: #16213e; border: 1px solid #2d3748;
    border-radius: 6px; padding: 8px 12px; color: #e0e0e0;
}
QLineEdit:focus { border-color: #4ade80; }
QListWidget {
    background-color: #16213e; border: 1px solid #2d3748;
    border-radius: 6px; padding: 4px; color: #e0e0e0;
}
QListWidget::item { padding: 10px 8px; border-radius: 4px; }
QListWidget::item:selected { background-color: #4ade80; color: #1a1a2e; }
QListWidget::item:hover:!selected { background-color: #1e293b; }
QPushButton {
    border-radius: 6px; padding: 8px 16px;
    font-size: 13px; font-weight: bold;
}
QPushButton#play {
    background-color: #4ade80; color: #1a1a2e;
    border: none; font-size: 15px; padding: 12px 32px;
}
QPushButton#play:hover { background-color: #22c55e; }
QPushButton#play:disabled { background-color: #2d3748; color: #6b7280; }
QPushButton#install {
    background-color: #16213e; color: #4ade80; border: 1px solid #4ade80;
}
QPushButton#install:hover { background-color: #4ade80; color: #1a1a2e; }
QPushButton#install:disabled { border-color: #2d3748; color: #6b7280; }
QPushButton#new_profile {
    background-color: #16213e; color: #60a5fa;
    border: 1px solid #60a5fa; padding: 6px 12px; font-size: 12px;
}
QPushButton#new_profile:hover { background-color: #60a5fa; color: #1a1a2e; }
QPushButton#delete_profile {
    background-color: #16213e; color: #f87171;
    border: 1px solid #f87171; padding: 6px 12px; font-size: 12px;
}
QPushButton#delete_profile:hover { background-color: #f87171; color: #1a1a2e; }
QProgressBar {
    background-color: #16213e; border: 1px solid #2d3748;
    border-radius: 4px; height: 8px;
}
QProgressBar::chunk { background-color: #4ade80; border-radius: 4px; }
QTextEdit {
    background-color: #0f0f1a; border: 1px solid #2d3748;
    border-radius: 6px; color: #a0aec0;
    font-family: 'Consolas', monospace; font-size: 11px; padding: 8px;
}
QSlider::groove:horizontal {
    background: #16213e; height: 4px;
    border-radius: 2px; border: 1px solid #2d3748;
}
QSlider::handle:horizontal {
    background: #4ade80; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #4ade80; border-radius: 2px; }
QFrame#divider { background-color: #2d3748; max-height: 1px; }
QRadioButton, QCheckBox { color: #e0e0e0; spacing: 8px; }
QCheckBox::indicator, QRadioButton::indicator { width: 14px; height: 14px; }
QCheckBox::indicator:checked { background-color: #4ade80; border-radius: 3px; }
"""


# ── Main Window ───────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = config.load()
        self.all_versions = []  # all MC releases
        self.fabric_versions = []  # MC versions Fabric supports
        self._thread = None
        self._worker = None
        self._setup_ui()
        self._check_java()
        self._load_versions()

    def _check_java(self):
        from core.java_manager import is_runtime_installed
        if not is_runtime_installed():
            self._log("⚠  Java runtime not found — it will be downloaded automatically when you click Install.")
        else:
            self._log("✅ Java runtime ready.")

    def _setup_ui(self):
        self.setWindowTitle("RevoMC")
        self.setMinimumSize(920, 640)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        t = QLabel("⛏  RevoMC")
        t.setObjectName("title")
        s = QLabel("Fabric enabled, performance optimised launcher for Minecraft")
        s.setObjectName("subtitle")
        title_col.addWidget(t)
        title_col.addWidget(s)
        header.addLayout(title_col)
        header.addStretch()

        user_col = QVBoxLayout()
        user_col.setSpacing(4)
        user_col.addWidget(self._slbl("Username"))
        self.username_edit = QLineEdit(self.cfg.get("username", ""))
        self.username_edit.setPlaceholderText("Enter username…")
        self.username_edit.setFixedWidth(200)
        self.username_edit.textChanged.connect(self._on_username_changed)
        user_col.addWidget(self.username_edit)
        header.addLayout(user_col)
        root.addLayout(header)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(div)

        content = QHBoxLayout()
        content.setSpacing(16)

        # ── Left: profiles ────────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)

        ph = QHBoxLayout()
        ph.addWidget(self._slbl("Profiles"))
        ph.addStretch()
        self.new_btn = QPushButton("+ New")
        self.new_btn.setObjectName("new_profile")
        self.new_btn.clicked.connect(self._on_new_profile)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("delete_profile")
        self.del_btn.clicked.connect(self._on_delete_profile)
        ph.addWidget(self.new_btn)
        ph.addWidget(self.del_btn)
        left.addLayout(ph)

        self.profile_list = QListWidget()
        self.profile_list.currentRowChanged.connect(self._on_profile_selected)
        left.addWidget(self.profile_list, 1)

        # Profile info card
        self.info_card = QFrame()
        self.info_card.setStyleSheet(
            "QFrame { background: #16213e; border: 1px solid #2d3748; border-radius: 6px; }"
        )
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(3)
        self.info_version = QLabel("")
        self.info_version.setStyleSheet("color: #9ca3af; font-size: 12px;")
        self.info_mods = QLabel("")
        self.info_mods.setStyleSheet("color: #9ca3af; font-size: 12px;")
        self.info_mods.setWordWrap(True)
        info_layout.addWidget(self.info_version)
        info_layout.addWidget(self.info_mods)
        left.addWidget(self.info_card)

        self.ram_label = self._slbl(f"RAM — {self.cfg.get('ram_gb', 2)} GB")
        left.addWidget(self.ram_label)
        self.ram_slider = QSlider(Qt.Orientation.Horizontal)
        self.ram_slider.setMinimum(1)
        self.ram_slider.setMaximum(16)
        self.ram_slider.setValue(self.cfg.get("ram_gb", 2))
        self.ram_slider.valueChanged.connect(self._on_ram_changed)
        left.addWidget(self.ram_slider)

        self.install_btn = QPushButton("⬇  Install / Update")
        self.install_btn.setObjectName("install")
        self.install_btn.clicked.connect(self._on_install)
        self.install_btn.setEnabled(False)
        left.addWidget(self.install_btn)

        self.play_btn = QPushButton("▶  PLAY")
        self.play_btn.setObjectName("play")
        self.play_btn.clicked.connect(self._on_play)
        self.play_btn.setEnabled(False)
        left.addWidget(self.play_btn)

        content.addLayout(left, 1)

        # ── Right: console ────────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(self._slbl("Console"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        right.addWidget(self.log_box, 1)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        right.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        right.addWidget(self.status_label)

        content.addLayout(right, 1)
        root.addLayout(content, 1)

        self._refresh_profile_list()

    def _slbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #6b7280; letter-spacing: 1px;"
        )
        return l

    # ── Version loading ───────────────────────────────────────────────────────

    def _load_versions(self):
        self._log("🌐 Fetching Minecraft versions…")
        try:
            all_v = fetch_release_versions()
            self.all_versions = [v["id"] for v in all_v]
            self._log(f"✅ {len(self.all_versions)} total MC releases found.")
        except Exception as e:
            self._log(f"❌ Could not fetch MC versions: {e}")

        try:
            self.fabric_versions = fetch_fabric_versions()
            self._log(f"✅ {len(self.fabric_versions)} versions supported by Fabric.")
        except Exception as e:
            self._log(f"❌ Could not fetch Fabric versions: {e}")

        self._refresh_buttons()

    # ── Profiles ──────────────────────────────────────────────────────────────

    def _refresh_profile_list(self):
        self.profile_list.clear()
        for p in self.cfg.get("profiles", []):
            type_tag = "🟢 Fabric" if p["type"] == "fabric" else "🍦 Vanilla"
            item = QListWidgetItem(f"{p['name']}\n{p['mc_version']}  ·  {type_tag}")
            self.profile_list.addItem(item)

        active = self.cfg.get("active_profile")
        if active:
            for i, p in enumerate(self.cfg.get("profiles", [])):
                if p["name"] == active:
                    self.profile_list.setCurrentRow(i)
                    break
        self._refresh_buttons()

    def _current_profile(self) -> dict | None:
        row = self.profile_list.currentRow()
        profiles = self.cfg.get("profiles", [])
        return profiles[row] if 0 <= row < len(profiles) else None

    def _on_profile_selected(self, row):
        profiles = self.cfg.get("profiles", [])
        if 0 <= row < len(profiles):
            self.cfg["active_profile"] = profiles[row]["name"]
            config.save(self.cfg)
            self._update_info_card(profiles[row])
        self._refresh_buttons()

    def _update_info_card(self, profile: dict):
        self.info_version.setText(
            f"MC {profile['mc_version']}  ·  {'Fabric' if profile['type'] == 'fabric' else 'Vanilla'}"
        )
        if profile["type"] == "fabric":
            mods = profile.get("mods", [])
            from core.installer import AVAILABLE_MODS

            labels = [AVAILABLE_MODS[m]["label"] for m in mods if m in AVAILABLE_MODS]
            self.info_mods.setText("Mods: " + (", ".join(labels) if labels else "none"))
        else:
            self.info_mods.setText("No mods — pure vanilla")

    def _on_new_profile(self):
        if not self.all_versions:
            self._log("⚠  Still loading versions, try again in a moment.")
            return
        dlg = NewProfileDialog(self.all_versions, self.fabric_versions, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            profile = dlg.get_profile()
            if not profile:
                self._log("⚠  Profile name cannot be empty.")
                return
            if any(p["name"] == profile["name"] for p in self.cfg.get("profiles", [])):
                self._log(f"⚠  A profile named '{profile['name']}' already exists.")
                return
            self.cfg.setdefault("profiles", []).append(profile)
            self.cfg["active_profile"] = profile["name"]
            config.save(self.cfg)
            self._refresh_profile_list()
            self._log(
                f"✅ Profile '{profile['name']}' created  ({profile['mc_version']}, {profile['type']})."
            )

    def _on_delete_profile(self):
        profile = self._current_profile()
        if not profile:
            return
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Delete '{profile['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cfg["profiles"] = [
                p for p in self.cfg.get("profiles", []) if p["name"] != profile["name"]
            ]
            if self.cfg.get("active_profile") == profile["name"]:
                self.cfg["active_profile"] = None
            config.save(self.cfg)
            self._refresh_profile_list()
            self._log(f"🗑  Deleted '{profile['name']}'.")

    # ── Install / Play ────────────────────────────────────────────────────────

    def _on_install(self):
        profile = self._current_profile()
        if not profile:
            return
        mc_version = profile["mc_version"]
        profile_type = profile["type"]
        enabled_mods = profile.get("mods", [])

        self._set_busy(True)
        self._log(f"\n{'─'*40}")
        self._log(f"📦 Installing '{profile['name']}' ({mc_version}, {profile_type})…")

        def install_task(log, progress):
            from core.java_manager import install_java
            install_java(log, progress)
            install_minecraft(mc_version, log, progress)
            fabric_profile_id = None
            if profile_type == "fabric":
                fabric_profile_id = install_fabric(mc_version, log, progress)
                install_mods(mc_version, enabled_mods, log, progress)

            self.cfg.setdefault("installed_versions", {})[mc_version] = {
                "fabric_profile_id": fabric_profile_id,
                "type": profile_type,
            }
            config.save(self.cfg)

        self._run_worker(install_task)

    def _on_play(self):
        profile = self._current_profile()
        if not profile:
            return
        username = self.username_edit.text().strip()
        mc_version = profile["mc_version"]
        profile_type = profile["type"]
        ram_gb = self.ram_slider.value()
        fabric_id = (
            self.cfg.get("installed_versions", {})
            .get(mc_version, {})
            .get("fabric_profile_id")
        )

        self._set_busy(True)
        self._log(f"\n{'─'*40}")
        self._log(f"🚀 Launching '{profile['name']}'…")

        self._thread = QThread()
        self._worker = LaunchWorker(
            mc_version, profile_type, fabric_id, username, ram_gb
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log)
        self._worker.finished.connect(self._on_worker_done)
        self._thread.start()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_username_changed(self, text):
        self.cfg["username"] = text
        config.save(self.cfg)
        self._refresh_buttons()

    def _on_ram_changed(self, val):
        self.cfg["ram_gb"] = val
        config.save(self.cfg)
        self.ram_label.setText(f"RAM — {val} GB")

    def _refresh_buttons(self):
        profile = self._current_profile()
        username = self.username_edit.text().strip()
        installed = self.cfg.get("installed_versions", {})
        has_profile = profile is not None
        is_installed = has_profile and profile["mc_version"] in installed
        self.install_btn.setEnabled(has_profile)
        self.play_btn.setEnabled(is_installed and bool(username))
        self.del_btn.setEnabled(has_profile)

    def _run_worker(self, task):
        self._thread = QThread()
        self._worker = Worker(task)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_worker_done)
        self._thread.start()

    def _on_progress(self, task, pct):
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"{task}: {pct}%")

    def _on_worker_done(self, success, message):
        self._set_busy(False)
        self.progress_bar.setValue(100 if success else 0)
        self._log(f"{'✅' if success else '❌'} {message}")
        self.status_label.setText("Ready.")
        self._refresh_buttons()
        if self._thread:
            self._thread.quit()

    def _set_busy(self, busy):
        self.install_btn.setEnabled(not busy)
        self.play_btn.setEnabled(not busy)
        self.new_btn.setEnabled(not busy)
        self.del_btn.setEnabled(not busy)

    def _log(self, text):
        self.log_box.append(text)
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )
