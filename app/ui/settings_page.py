"""Settings: daily goal, free practice, export/import/reset."""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QCheckBox,
    QPushButton, QFileDialog, QMessageBox, QFrame,
)

from app import models as M
from app import tts


class SettingsPage(QWidget):
    def __init__(self, progress, parent=None):
        super().__init__(parent)
        self.progress = progress

        page = QVBoxLayout(self)
        page.setContentsMargins(28, 24, 28, 24)
        page.setSpacing(18)

        title = QLabel("Settings")
        title.setProperty("class", "h1")
        page.addWidget(title)

        # study settings
        frame = QFrame()
        frame.setProperty("class", "card")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(12)

        head = QLabel("Study")
        head.setProperty("class", "h2")
        fl.addWidget(head)

        goal_row = QHBoxLayout()
        goal_text = QVBoxLayout()
        goal_text.setSpacing(1)
        t = QLabel("Daily goal (XP)")
        t.setProperty("class", "modeTitle")
        d = QLabel("XP per day to keep the ring full")
        d.setProperty("class", "muted")
        goal_text.addWidget(t)
        goal_text.addWidget(d)
        goal_row.addLayout(goal_text)
        goal_row.addStretch(1)
        self.goal_spin = QSpinBox()
        self.goal_spin.setRange(10, 500)
        self.goal_spin.setSingleStep(10)
        self.goal_spin.setValue(self.progress.data["dailyGoal"])
        self.goal_spin.valueChanged.connect(lambda v: self.progress.set(dailyGoal=v))
        goal_row.addWidget(self.goal_spin)
        fl.addLayout(goal_row)

        self.free_check = QCheckBox("Free practice (unlock every lesson)")
        self.free_check.setChecked(self.progress.data["freePractice"])
        self.free_check.toggled.connect(lambda v: self.progress.set(freePractice=v))
        fl.addWidget(self.free_check)

        self.sound_check = QCheckBox("Read Japanese aloud (Japanese Windows voice)")
        if tts.has_ja_voice():
            self.sound_check.setChecked(self.progress.data["soundOn"])
            self.sound_check.toggled.connect(lambda v: self.progress.set(soundOn=v))
        else:
            self.sound_check.setChecked(False)
            self.sound_check.setEnabled(False)
            no_voice = QLabel("No Japanese voice found — install Microsoft Haruka "
                              "to enable audio.")
            no_voice.setWordWrap(True)
            no_voice.setProperty("class", "muted")
            fl.addWidget(no_voice)
        fl.addWidget(self.sound_check)
        page.addWidget(frame)

        # data frame
        data_frame = QFrame()
        data_frame.setProperty("class", "card")
        dl = QVBoxLayout(data_frame)
        dl.setContentsMargins(20, 16, 20, 16)
        dl.setSpacing(12)
        dh = QLabel("Your data")
        dh.setProperty("class", "h2")
        dl.addWidget(dh)
        note = QLabel("Progress is saved in data\\state\\progress.json with timestamped backups.")
        note.setWordWrap(True)
        note.setProperty("class", "muted")
        dl.addWidget(note)
        row = QHBoxLayout()
        export_btn = QPushButton("Export backup")
        export_btn.setProperty("class", "primary")
        export_btn.clicked.connect(self._export)
        row.addWidget(export_btn)
        import_btn = QPushButton("Import backup")
        import_btn.setProperty("class", "ghost")
        import_btn.clicked.connect(self._import)
        row.addWidget(import_btn)
        row.addStretch(1)
        reset_btn = QPushButton("Reset all progress")
        reset_btn.setProperty("class", "danger")
        reset_btn.clicked.connect(self._reset)
        row.addWidget(reset_btn)
        dl.addLayout(row)
        page.addWidget(data_frame)

        ver = QLabel(f"Version {M.VERSION} · toasterdude18-max/genki-study-desktop")
        ver.setProperty("class", "muted")
        page.addWidget(ver)

        page.addStretch(1)

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export progress", "genki-progress.json", "JSON (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.progress.store.export_json())
        QMessageBox.information(self, "Exported", f"Saved to {path}")

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import progress", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = self.progress.store.import_json(f.read())
        except (OSError, ValueError):
            QMessageBox.warning(self, "Import failed", "That file is not a valid progress backup.")
            return
        self.progress.data = data
        self.goal_spin.blockSignals(True)
        self.goal_spin.setValue(data.get("dailyGoal", 50))
        self.goal_spin.blockSignals(False)
        self.free_check.blockSignals(True)
        self.free_check.setChecked(data.get("freePractice", True))
        self.free_check.blockSignals(False)
        QMessageBox.information(self, "Imported", "Progress restored.")

    def _reset(self):
        answer = QMessageBox.question(
            self, "Reset", "Delete ALL progress? Export a backup first if unsure.",
            QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            try:
                os.remove(self.progress.store.path)
            except OSError:
                pass
            self.progress.data = dict(M.DEFAULT_PROGRESS)
            self.goal_spin.blockSignals(True)
            self.goal_spin.setValue(self.progress.data["dailyGoal"])
            self.goal_spin.blockSignals(False)
            self.free_check.blockSignals(True)
            self.free_check.setChecked(self.progress.data["freePractice"])
            self.free_check.blockSignals(False)
            QMessageBox.information(self, "Reset", "Progress cleared.")
