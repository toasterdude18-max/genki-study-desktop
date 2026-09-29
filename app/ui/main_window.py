"""Main window: top bar, nav rail + stacked pages (Dashboard, Settings), lesson routing."""
import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QPushButton,
)

from app import models as M
from app.ui.dashboard import Dashboard
from app.ui.settings_page import SettingsPage
from app.ui.lesson_page import LessonPage


def _nav_log(msg):
    """Append a navigation trace line to data\\state\\app.log (best-effort)."""
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with open(os.path.join(app_dir, "data", "state", "app.log"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] NAV {msg}\n")
    except Exception:
        pass


class MainWindow(QMainWindow):
    def __init__(self, data, progress, parent=None):
        super().__init__(parent)
        self.data = data
        self.progress = progress
        self._in_lesson = False
        self._all_ids = [v["id"] for l in data["lessons"] for v in l["vocab"]]
        self.setWindowTitle("Genki Study")

        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- nav rail ----
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(190)
        self.nav.setFocusPolicy(Qt.NoFocus)  # never take focus: no accidental activation
        for label in ("Dashboard", "Settings"):
            QListWidgetItem(label, self.nav)
        self.nav.currentRowChanged.connect(self._switch_page)
        root.addWidget(self.nav)

        # ---- right side: top bar + stack ----
        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(0)

        topbar = QWidget()
        topbar.setObjectName("topbar")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(22, 12, 22, 12)
        brand = QLabel("Genki Study")
        brand.setObjectName("appTitle")
        tb.addWidget(brand)
        tb.addStretch(1)
        self.xp_pill = QLabel("0 XP")
        self.xp_pill.setProperty("class", "pill")
        self.streak_pill = QLabel("🔥 0")
        self.streak_pill.setProperty("class", "pillStreak")
        self.stars_pill = QLabel("★ 0")
        self.stars_pill.setProperty("class", "pillStars")
        tb.addWidget(self.xp_pill)
        tb.addWidget(self.streak_pill)
        tb.addWidget(self.stars_pill)
        self.theme_btn = QPushButton("☀️" if progress.data.get("darkMode") else "🌙")
        self.theme_btn.setProperty("class", "ghost")
        self.theme_btn.setToolTip("Toggle dark mode")
        self.theme_btn.clicked.connect(self.toggle_dark)
        tb.addWidget(self.theme_btn)
        side.addWidget(topbar)

        self.stack = QStackedWidget()
        self.dashboard = Dashboard(data, progress, self.open_lesson)
        self.settings = SettingsPage(progress)
        self.stack.addWidget(self.dashboard)   # 0
        self.stack.addWidget(self.settings)    # 1
        side.addWidget(self.stack, 1)
        root.addLayout(side, 1)

        self.nav.setCurrentRow(0)
        self.refresh_topbar()

    # ---------- top bar ----------
    def refresh_topbar(self):
        p = self.progress
        self.xp_pill.setText(f"{p.data['xp']} XP")
        self.streak_pill.setText(f"🔥 {p.data['streak']}")
        self.stars_pill.setText(f"🟢 {p.mastered_words(self._all_ids)} / {len(self._all_ids)} words")

    def toggle_dark(self):
        from app.ui.theme import apply_theme, set_titlebar_dark
        dark = not bool(self.progress.data.get("darkMode"))
        self.progress.set(darkMode=dark)
        apply_theme(dark)
        set_titlebar_dark(self, dark)
        self.theme_btn.setText("☀️" if dark else "🌙")

    # ---------- navigation ----------
    def _switch_page(self, row):
        _nav_log(f"switch_page row={row} in_lesson={self._in_lesson} count={self.stack.count()}")
        if self._in_lesson:
            return  # a lesson is open: only _close_lesson may leave it
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)
            self.dashboard.refresh()
            self.refresh_topbar()

    def open_lesson(self, lesson_id):
        _nav_log(f"open_lesson {lesson_id}")
        self._in_lesson = True
        page = LessonPage(self.data, self.progress, lesson_id,
                          on_back=self._close_lesson,
                          on_change=self.refresh_topbar)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.nav.setCurrentRow(-1)

    def _close_lesson(self):
        widget = self.stack.currentWidget()
        _nav_log(f"close_lesson widget={type(widget).__name__}")
        if not isinstance(widget, LessonPage):
            return  # ignore re-entrant/stray activations
        self._in_lesson = False
        self.stack.setCurrentIndex(0)
        self.stack.removeWidget(widget)
        widget.deleteLater()
        self.nav.setCurrentRow(0)
        self.dashboard.refresh()
        self.refresh_topbar()
