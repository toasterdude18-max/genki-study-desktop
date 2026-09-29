"""Standalone drill page (e.g. weak words) reusing QuizWidget."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

from app.ui.quiz_widget import QuizWidget


class DrillPage(QWidget):
    def __init__(self, progress, items, title, on_back, on_change=None, parent=None):
        super().__init__(parent)
        self.progress = progress
        self.items = items
        self.title = title
        self.on_back = on_back
        self.on_change = on_change
        self.greens_gained = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)
        outer.setSpacing(14)

        header = QHBoxLayout()
        back = QPushButton("‹ Back")
        back.setProperty("class", "ghost")
        back.clicked.connect(self.on_back)
        header.addWidget(back)
        t = QLabel(title)
        t.setProperty("class", "h1")
        header.addWidget(t)
        header.addStretch(1)
        outer.addLayout(header)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        self.quiz = QuizWidget(self)
        self.quiz.setMaximumWidth(760)
        self.quiz.answer_given.connect(self._on_answer)
        self.quiz.finished.connect(self._on_finished)
        wrap.addWidget(self.quiz, 1)
        wrap.addStretch(1)
        outer.addLayout(wrap, 1)

        rwrap = QHBoxLayout()
        rwrap.addStretch(1)
        self.result_frame = QFrame()
        self.result_frame.setProperty("class", "card")
        self.result_frame.setMaximumWidth(640)
        res = QVBoxLayout(self.result_frame)
        res.setContentsMargins(32, 32, 32, 32)
        res.setSpacing(10)
        res.addStretch(1)
        self.res_score = QLabel("")
        self.res_score.setProperty("class", "scoreBig")
        self.res_score.setAlignment(Qt.AlignCenter)
        res.addWidget(self.res_score)
        self.res_note = QLabel("")
        self.res_note.setProperty("class", "muted")
        self.res_note.setAlignment(Qt.AlignCenter)
        res.addWidget(self.res_note)
        row = QHBoxLayout()
        row.addStretch(1)
        again = QPushButton("Again")
        again.setProperty("class", "primary")
        again.clicked.connect(self._restart)
        row.addWidget(again)
        done = QPushButton("Back")
        done.setProperty("class", "ghost")
        done.clicked.connect(self.on_back)
        row.addWidget(done)
        row.addStretch(1)
        res.addLayout(row)
        res.addStretch(1)
        rwrap.addWidget(self.result_frame, 1)
        rwrap.addStretch(1)
        outer.addLayout(rwrap, 1)
        self.result_frame.hide()

        self.quiz.start(self.items, sound=self.progress.data.get("soundOn", True))

    def _restart(self):
        self.result_frame.hide()
        self.greens_gained = 0
        self.quiz.start(self.items, sound=self.progress.data.get("soundOn", True))

    def _on_answer(self, item, ok):
        if not item.get("vocabId"):
            return
        status = self.progress.word_answer(item["vocabId"], ok)
        self.quiz.show_word_status(status)
        if status.get("gained_green"):
            self.greens_gained += 1
        if self.on_change:
            self.on_change()

    def _on_finished(self, result):
        score, total = result["score"], result["total"]
        ratio = score / total if total else 0
        xp = round(ratio * 20) + (5 if ratio == 1 else 0)
        self.progress.add_xp(xp)
        self.res_score.setText(f"{score} / {total}")
        self.res_note.setText(f"+{xp} XP · {self.greens_gained} green star(s) earned")
        self.result_frame.show()
        if self.on_change:
            self.on_change()

    def on_quiz_quit(self):
        self.on_back()
