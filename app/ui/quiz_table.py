"""Education-Perfect-style preview table: every word/point in a drill with its
answer and per-word progress, shown before the quiz starts."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from app import models as M


class QuizTable(QWidget):
    def __init__(self, progress, on_start, on_back, parent=None):
        super().__init__(parent)
        self.progress = progress
        self.on_start = on_start
        self.on_back = on_back

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 12, 4, 4)
        lay.setSpacing(10)

        header = QHBoxLayout()
        back = QPushButton("‹ Back")
        back.setProperty("class", "ghost")
        back.clicked.connect(self.on_back)
        header.addWidget(back)
        self.title_lbl = QLabel("")
        self.title_lbl.setProperty("class", "modeTitle")
        header.addWidget(self.title_lbl)
        header.addStretch(1)
        self.count_lbl = QLabel("")
        self.count_lbl.setProperty("class", "muted")
        header.addWidget(self.count_lbl)
        lay.addLayout(header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Word", "Answer", "Progress"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(36)
        lay.addWidget(self.table, 1)

        foot = QHBoxLayout()
        foot.addStretch(1)
        self.start_btn = QPushButton("Start")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.clicked.connect(self.on_start)
        foot.addWidget(self.start_btn)
        lay.addLayout(foot)

    def set_rows(self, title, rows):
        self.title_lbl.setText(title)
        self.count_lbl.setText(f"{len(rows)} item(s)")
        self.table.setRowCount(0)
        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(r["stim"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["ans"]))
            self.table.setItem(i, 2, QTableWidgetItem(self._progress(r.get("vid"))))

    def _progress(self, vocab_id):
        if not vocab_id:
            return "—"
        c = self.progress.word_card(vocab_id)
        g, y = c["green"], c["yellow"]
        s = ("★" * min(g, 3) + (f"×{g}" if g > 3 else "")) if g else ""
        return s + "●" * y + "○" * (M.YELLOW_MAX - y)
