"""Shared quiz runner: one typed item at a time, Japanese TTS with a per-quiz
mute toggle and replay button, and per-word star feedback.

Multiple choice was removed — every question is answered by typing.
"""
from PySide6.QtCore import Qt, Signal, QEvent
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
        self.setFocusPolicy(Qt.StrongFocus)
        self.items = []
        self.i = 0
        self.score = 0
        self.answer = None
        self.checked = False
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
        self.dont_know_btn = QPushButton("I don't know")
        self.dont_know_btn.setProperty("class", "ghost")
        self.dont_know_btn.setToolTip("Submit a blank answer (counts as wrong)")
        self.dont_know_btn.clicked.connect(self._dont_know)
        bottom.addWidget(self.dont_know_btn)
        bottom.addStretch(1)
        self.check_btn = QPushButton("Check")
        self.check_btn.setProperty("class", "primary")
        self.check_btn.clicked.connect(self._check)
        self.check_btn.installEventFilter(self)
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

        self.feedback_lbl.setText("")
        self.feedback_lbl.setProperty("class", "")
        self.pips_lbl.setText("")
        self.pips_lbl.setProperty("class", "")
        self.checked = False
        self.answer = None
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Check")
        self.dont_know_btn.setVisible(True)

        self.replay_btn.setVisible(bool(q.get("speakText")))

        self.answer_edit.setPlaceholderText("日本語で入力" if q.get("lang") == "ja"
                                            else "Type your answer…")
        self.answer_edit.show()
        self.answer_edit.clear()
        self.answer_edit.setEnabled(True)
        self.answer_edit.setFocus()

        if q.get("speakText"):
            self._speak(q["speakText"])

    def _check(self):
        if self.checked:
            self._next()
            return
        q = self.items[self.i]
        text = self.answer_edit.text()
        if not text.strip():
            return
        self._submit(q, grade(q, text))

    def _dont_know(self):
        """Submit a null answer — exactly like getting it wrong."""
        if self.checked:
            return
        q = self.items[self.i]
        self.answer = None
        self._submit(q, False)
        if not q.get("speakAnswer") and q.get("speakText"):
            self._speak(q["speakText"])  # hear the word again when the answer is English

    def _submit(self, q, ok):
        self.checked = True
        if ok:
            self.score += 1
        self.feedback_lbl.setProperty("class", "feedbackOk" if ok else "feedbackBad")
        self.feedback_lbl.setText("Correct!" if ok else f"Not quite — {q['explain']}")
        # keep the input enabled: the next Enter advances to the next question
        self.answer_given.emit(q, ok)
        self.check_btn.setText("Finish" if self.i + 1 >= len(self.items) else "Next")
        self.dont_know_btn.hide()
        if q.get("speakAnswer"):
            self._speak(q["speakAnswer"])

    def eventFilter(self, obj, event):
        # Enter on the Check/Next button behaves like clicking it: checks when
        # unanswered, advances when already checked.
        if (obj is self.check_btn and event.type() == QEvent.KeyPress
                and event.key() in (Qt.Key_Return, Qt.Key_Enter)):
            if self.check_btn.isEnabled():
                self._check()
                return True
        return False

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
