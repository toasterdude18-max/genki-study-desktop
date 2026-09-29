"""Shared quiz runner: one item at a time, Japanese TTS with a per-quiz mute
toggle and replay button, and per-word star feedback."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QProgressBar, QSizePolicy,
)

from app import models as M
from app import tts
from app.quiz import grade


class QuizWidget(QFrame):
    finished = Signal(dict)            # {score, total}
    answer_given = Signal(object, bool)  # (item, ok)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quizCard")
        self.setProperty("class", "quizCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.items = []
        self.i = 0
        self.score = 0
        self.answer = None
        self.checked = False
        self._opt_btns = []
        self.sound = True
        self._voice_ok = tts.has_ja_voice()
        self._build()
        self.hide()

    def _build(self):
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(28, 22, 28, 22)
        self._lay.setSpacing(12)

        top = QHBoxLayout()
        self.quit_btn = QPushButton("✕ Quit")
        self.quit_btn.setProperty("class", "ghost")
        self.quit_btn.clicked.connect(self._quit)
        top.addWidget(self.quit_btn)
        top.addStretch(1)
        self.count_lbl = QLabel("")
        self.count_lbl.setProperty("class", "countLbl")
        top.addWidget(self.count_lbl)
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setProperty("class", "ghost")
        self.mute_btn.setToolTip("Toggle sound for this quiz")
        self.mute_btn.clicked.connect(self._toggle_sound)
        top.addWidget(self.mute_btn)
        self._lay.addLayout(top)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self._lay.addWidget(self.progress)

        self._lay.addStretch(1)

        prompt_row = QHBoxLayout()
        prompt_row.addStretch(1)
        self.prompt_lbl = QLabel("")
        self.prompt_lbl.setProperty("class", "prompt")
        self.prompt_lbl.setWordWrap(True)
        self.prompt_lbl.setAlignment(Qt.AlignCenter)
        prompt_row.addWidget(self.prompt_lbl)
        self.replay_btn = QPushButton("🔊")
        self.replay_btn.setProperty("class", "ghost")
        self.replay_btn.setToolTip("Listen again")
        self.replay_btn.clicked.connect(self._replay)
        prompt_row.addWidget(self.replay_btn)
        prompt_row.addStretch(1)
        self._lay.addLayout(prompt_row)

        self.opts_lay = QVBoxLayout()
        self.opts_lay.setSpacing(10)
        self._lay.addLayout(self.opts_lay)

        self.answer_edit = QLineEdit()
        self.answer_edit.setProperty("class", "answer")
        self.answer_edit.setPlaceholderText("Type your answer…")
        self.answer_edit.returnPressed.connect(self._check)
        self._lay.addWidget(self.answer_edit)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setWordWrap(True)
        self.feedback_lbl.setAlignment(Qt.AlignCenter)
        self._lay.addWidget(self.feedback_lbl)

        self.pips_lbl = QLabel("")
        self.pips_lbl.setAlignment(Qt.AlignCenter)
        self._lay.addWidget(self.pips_lbl)

        self._lay.addStretch(1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.check_btn = QPushButton("Check")
        self.check_btn.setProperty("class", "primary")
        self.check_btn.clicked.connect(self._check)
        bottom.addWidget(self.check_btn)
        self._lay.addLayout(bottom)

    # ---------- sound ----------
    def _toggle_sound(self):
        self.sound = not self.sound
        self.mute_btn.setText("🔊" if self.sound else "🔇")
        if not self.sound:
            tts.stop()

    def _replay(self):
        q = self.items[self.i] if self.i < len(self.items) else None
        if q and q.get("speakText") and self.sound:
            tts.speak(q["speakText"])

    def _speak(self, text):
        if self.sound and self._voice_ok and text:
            tts.speak(text)

    # ---------- lifecycle ----------
    def start(self, items, sound=None):
        self.items = list(items)
        self.i = 0
        self.score = 0
        self.answer = None
        self.checked = False
        self.sound = self._voice_ok if sound is None else bool(sound)
        self.mute_btn.setEnabled(self._voice_ok)
        self.mute_btn.setText("🔊" if self.sound else "🔇")
        self.show()
        self._render()

    def _quit(self):
        self.hide()
        tts.stop()
        parent = self.parent()
        if parent is not None and hasattr(parent, "on_quiz_quit"):
            parent.on_quiz_quit()

    def _render(self):
        if self.i >= len(self.items):
            return self._finish()
        q = self.items[self.i]
        self.count_lbl.setText(f"{self.i + 1} / {len(self.items)}")
        self.progress.setMaximum(len(self.items))
        self.progress.setValue(self.i)
        self.prompt_lbl.setText(q["prompt"])
        self.prompt_lbl.setProperty("lang", "ja" if q.get("promptJa") else "en")
        self.prompt_lbl.style().unpolish(self.prompt_lbl)
        self.prompt_lbl.style().polish(self.prompt_lbl)

        self._clear_dynamic()
        self.checked = False
        self.answer = None
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Check")

        self.replay_btn.setVisible(bool(q.get("speakText")))

        if q["kind"] == "mc":
            self.answer_edit.hide()
            for idx, opt in enumerate(q["options"]):
                b = QPushButton(opt)
                b.setProperty("class", "opt")
                if q.get("optionsJa") is not None:
                    b.setProperty("lang", "ja" if q["optionsJa"] else "en")
                b.setMinimumHeight(46)
                b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                b.clicked.connect(lambda _=False, i=idx: self._choose(i))
                self.opts_lay.addWidget(b)
                self._opt_btns.append(b)
            if self._opt_btns:
                self._opt_btns[0].setFocus()
        else:
            self.answer_edit.setPlaceholderText("日本語で入力" if q.get("lang") == "ja"
                                                else "Type your answer…")
            self.answer_edit.show()
            self.answer_edit.clear()
            self.answer_edit.setEnabled(True)
            self.answer_edit.setFocus()

        if q.get("speakText"):
            self._speak(q["speakText"])

    def _clear_dynamic(self):
        while self.opts_lay.count():
            item = self.opts_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._opt_btns = []
        self.feedback_lbl.setText("")
        self.feedback_lbl.setProperty("class", "")
        self.pips_lbl.setText("")
        self.pips_lbl.setProperty("class", "")

    def _choose(self, idx):
        if self.checked:
            return
        self.answer = idx
        for i, b in enumerate(self._opt_btns):
            b.setProperty("sel", "1" if i == idx else "")
            b.style().unpolish(b)
            b.style().polish(b)
        self._check()

    def _check(self):
        if self.checked:
            self._next()
            return
        q = self.items[self.i]
        if q["kind"] == "mc":
            if self.answer is None:
                return
            ok = self.answer == q["correct"]
            for i, b in enumerate(self._opt_btns):
                if i == q["correct"]:
                    b.setProperty("ok", "1")
                elif i == self.answer:
                    b.setProperty("bad", "1")
                else:
                    b.setEnabled(False)
                b.style().unpolish(b)
                b.style().polish(b)
        else:
            text = self.answer_edit.text()
            if not text.strip():
                return
            ok = grade(q, text)
            self.answer_edit.setEnabled(False)

        self.checked = True
        if ok:
            self.score += 1
        self.feedback_lbl.setProperty("class", "feedbackOk" if ok else "feedbackBad")
        self.feedback_lbl.setText("Correct!" if ok else f"Not quite — {q['explain']}")
        self.answer_given.emit(q, ok)
        self.check_btn.setText("Finish" if self.i + 1 >= len(self.items) else "Next")
        if q.get("speakAnswer"):
            self._speak(q["speakAnswer"])

    def _next(self):
        self.i += 1
        self._render()

    def _finish(self):
        total = len(self.items)
        self.hide()
        tts.stop()
        self.finished.emit({"score": self.score, "total": total})

    # ---------- per-word star feedback ----------
    def show_word_status(self, status):
        if not status:
            self.pips_lbl.setText("")
            return
        greens = status.get("green", 0)
        yellow = status.get("yellow", 0)
        parts = []
        if greens:
            parts.append("★" * min(greens, 3) + (f"×{greens}" if greens > 3 else ""))
        parts.append("●" * yellow + "○" * (M.YELLOW_MAX - yellow))
        line = " ".join(p for p in parts if p)
        if status.get("gained_green"):
            self.pips_lbl.setProperty("class", "starGain")
            line = f"⭐ Green star earned!  {line}"
        elif status.get("lost"):
            self.pips_lbl.setProperty("class", "feedbackBad")
            line = f"Yellow stars reset  {line}"
        else:
            self.pips_lbl.setProperty("class", "pips")
        self.pips_lbl.setText(line)
