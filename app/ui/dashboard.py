"""Dashboard: stat cards, word-mastery lesson grid, and the weak-words panel."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout,
    QScrollArea, QFrame,
)

from app import models as M


def _stat_card(value, label):
    card = QFrame()
    card.setProperty("class", "card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(20, 16, 20, 16)
    v = QLabel(value)
    v.setProperty("class", "statValue")
    l = QLabel(label)
    l.setProperty("class", "statLabel")
    lay.addWidget(v)
    lay.addWidget(l)
    return card


class Dashboard(QWidget):
    def __init__(self, data, progress, open_lesson, parent=None):
        super().__init__(parent)
        self.setObjectName("dashPage")  # orange home page (see theme)
        self.progress = progress
        self.open_lesson = open_lesson
        self.all_vocab = [v for l in data["lessons"] for v in l["vocab"]]

        page = QVBoxLayout(self)
        page.setContentsMargins(28, 24, 28, 24)
        page.setSpacing(18)

        title = QLabel("Dashboard")
        title.setProperty("class", "h1")
        page.addWidget(title)

        # stat cards
        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.xp_card = _stat_card("0", "Total XP")
        self.streak_card = _stat_card("0", "Day streak")
        self.words_card = _stat_card("0", "Words mastered")
        self.goal_card = _stat_card("0/50", "Today's goal")
        for c in (self.xp_card, self.streak_card, self.words_card, self.goal_card):
            stats.addWidget(c, 1)
        page.addLayout(stats)

        sub = QLabel("Lessons")
        sub.setProperty("class", "h2")
        page.addWidget(sub)

        # lesson grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        grid = QGridLayout(body)
        grid.setSpacing(10)
        self.lesson_btns = {}
        for lesson in data["lessons"]:
            lid = lesson["id"]
            btn = QPushButton()
            btn.setProperty("class", "lesson")
            btn.setMinimumHeight(84)
            btn.clicked.connect(lambda _=False, i=lid: self.open_lesson(i))
            grid.addWidget(btn, (lid - 1) // 4, (lid - 1) % 4)
            self.lesson_btns[lid] = (btn, lesson)
        grid.setRowStretch((M.LESSON_COUNT - 1) // 4, 1)
        scroll.setWidget(body)
        page.addWidget(scroll, 1)

        self.refresh()

    def refresh(self):
        p = self.progress
        self.xp_card.findChild(QLabel).setText(f"{p.data['xp']}")
        self.streak_card.findChild(QLabel).setText(f"🔥 {p.data['streak']}")
        all_ids = [v["id"] for v in self.all_vocab]
        self.words_card.findChild(QLabel).setText(f"🟢 {p.mastered_words(all_ids)}/{len(all_ids)}")
        goal = p.data["dailyGoal"]
        self.goal_card.findChild(QLabel).setText(f"{p.today_xp()}/{goal}")

        for lid, (btn, lesson) in self.lesson_btns.items():
            ids = [v["id"] for v in lesson["vocab"]]
            m = p.mastered_words(ids)
            total = len(ids)
            btn.setProperty("mastered", "1" if m >= total else "")
            btn.setProperty("started", "1" if 0 < m < total else "")
            text = f"Lesson {lid}\n{lesson['title']}\n🟢 {m}/{total}"
            btn.setText(text)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
