"""Lesson page: flashcards (with per-word stars), grammar reference, and the
practice quizzes (vocabulary, grammar, and the four honorific sub-drills)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QGridLayout, QScrollArea, QFrame, QSizePolicy, QStackedLayout,
)

from app import models as M
from app.quiz import (
    quiz_vocab, quiz_grammar,
    quiz_keigo_en_jp, quiz_keigo_jp_en, quiz_keigo_hon_norm, quiz_keigo_norm_hon,
    vocab_rows, grammar_rows, keigo_rows,
)
from app.ui.quiz_widget import QuizWidget
from app.ui.quiz_table import QuizTable

KEIGO_BUILDERS = {
    "keigo-en-jp": quiz_keigo_en_jp,
    "keigo-jp-en": quiz_keigo_jp_en,
    "keigo-hon-norm": quiz_keigo_hon_norm,
    "keigo-norm-hon": quiz_keigo_norm_hon,
}


class LessonPage(QWidget):
    def __init__(self, data, progress, lesson_id, on_back, on_change=None, parent=None):
        super().__init__(parent)
        self.data = data
        self.progress = progress
        self.lesson = next(l for l in data["lessons"] if l["id"] == lesson_id)
        self.lesson_id = lesson_id
        self.on_back = on_back
        self.on_change = on_change
        self.key = "vocab"
        self.greens_gained = 0
        self._keigo_verbs = [v for l in data["lessons"] if l["id"] <= lesson_id
                             for v in l["vocab"] if v.get("keigo")]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)
        outer.setSpacing(14)

        # header
        header = QHBoxLayout()
        back = QPushButton("‹ Lessons")
        back.setProperty("class", "ghost")
        back.clicked.connect(self._back)
        header.addWidget(back)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        self.title_lbl = QLabel(f"Lesson {lesson_id}: {self.lesson['title']}")
        self.title_lbl.setProperty("class", "h1")
        self.sub_lbl = QLabel(self.lesson["titleJP"])
        self.sub_lbl.setProperty("class", "muted")
        titles.addWidget(self.title_lbl)
        titles.addWidget(self.sub_lbl)
        header.addLayout(titles)
        header.addStretch(1)
        self.star_pill = QLabel("")
        self.star_pill.setProperty("class", "pillStars")
        header.addWidget(self.star_pill)
        outer.addLayout(header)

        # tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_vocab_tab(), "Vocab")
        self.tabs.addTab(self._build_grammar_tab(), "Grammar")
        self.tabs.addTab(self._build_practice_tab(), "Practice")
        outer.addWidget(self.tabs, 1)

        # quiz card (centred)
        quiz_wrap = QHBoxLayout()
        quiz_wrap.addStretch(1)
        self.quiz = QuizWidget(self)
        self.quiz.setMaximumWidth(760)
        self.quiz.answer_given.connect(self._on_answer)
        self.quiz.finished.connect(self._on_finished)
        quiz_wrap.addWidget(self.quiz, 1)
        quiz_wrap.addStretch(1)
        outer.addLayout(quiz_wrap, 1)

        # result card (centred)
        result_wrap = QHBoxLayout()
        result_wrap.addStretch(1)
        self.result_frame = QFrame()
        self.result_frame.setProperty("class", "card")
        self.result_frame.setMaximumWidth(640)
        res = QVBoxLayout(self.result_frame)
        res.setContentsMargins(32, 32, 32, 32)
        res.setSpacing(10)
        res.addStretch(1)
        self.res_title = QLabel("")
        self.res_title.setProperty("class", "resultTitle")
        self.res_title.setAlignment(Qt.AlignCenter)
        res.addWidget(self.res_title)
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
        self.again_btn = QPushButton("Again")
        self.again_btn.setProperty("class", "primary")
        self.again_btn.clicked.connect(self._start_current)
        row.addWidget(self.again_btn)
        done_btn = QPushButton("Back to practice")
        done_btn.setProperty("class", "ghost")
        done_btn.clicked.connect(self._show_practice)
        row.addWidget(done_btn)
        row.addStretch(1)
        res.addLayout(row)
        res.addStretch(1)
        result_wrap.addWidget(self.result_frame, 1)
        result_wrap.addStretch(1)
        outer.addLayout(result_wrap, 1)
        self.result_frame.hide()

        self._refresh_mastery()

    # ---------- per-word star badge ----------
    def _word_badge(self, v):
        c = self.progress.word_card(v["id"])
        g, y = c["green"], c["yellow"]
        s = ("★" * min(g, 3) + (f"×{g}" if g > 3 else "")) if g else ""
        return s + "●" * y + "○" * (M.YELLOW_MAX - y)

    # ---------- tabs ----------
    def _build_vocab_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(4, 12, 4, 4)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        grid = QGridLayout(body)
        grid.setSpacing(9)
        self._cards = {}
        for i, v in enumerate(self.lesson["vocab"]):
            card = QPushButton()
            card.setProperty("class", "flash")
            if v.get("extra"):
                card.setProperty("extra", "1")
            card.setMinimumHeight(124)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            card.clicked.connect(lambda _=False, c=card, v=v: self._flip(c, v))
            self._cards[id(card)] = (card, v, False)
            grid.addWidget(card, i // 5, i % 5)
            self._render_card(card)
        scroll.setWidget(body)
        lay.addWidget(scroll)
        return page

    def _render_card(self, card):
        card_obj, v, flipped = self._cards[id(card)]
        if flipped:
            card.setText(f'{v["english"]}\n{v["type"]}')
        else:
            base = f'{v["kanji"]}\n{v["japanese"]}\n{v["reading"]}' if v.get("kanji") \
                else f'{v["japanese"]}\n{v["reading"]}'
            card.setText(f'{base}\n{self._word_badge(v)}')
        c = self.progress.word_card(v["id"])
        card.setProperty("weak", "1" if c["green"] == 0 else "")
        card.style().unpolish(card)
        card.style().polish(card)

    def _flip(self, card, v):
        _, _, flipped = self._cards[id(card)]
        self._cards[id(card)] = (card, v, not flipped)
        self._render_card(card)

    def _refresh_cards(self):
        for key in self._cards:
            self._render_card(self._cards[key][0])

    def _build_grammar_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(4, 12, 4, 4)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        box = QVBoxLayout(body)
        box.setSpacing(10)
        for g in self.lesson["grammar"]:
            frame = QFrame()
            frame.setProperty("class", "gram")
            if g.get("extra"):
                frame.setProperty("extra", "1")
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(16, 12, 16, 12)
            fl.setSpacing(4)
            pat = QLabel(g["pattern"])
            pat.setProperty("class", "gramPat")
            if g.get("extra"):
                pat.setProperty("extra", "1")
            pat.setWordWrap(True)
            fl.addWidget(pat)
            fl.addWidget(QLabel(g["meaning"]))
            ex = g.get("example")
            if ex:
                exl = QLabel(f'{ex["jp"]}\n{ex["en"]}')
                exl.setProperty("class", "gramEx")
                exl.setWordWrap(True)
                fl.addWidget(exl)
            box.addWidget(frame)
        box.addStretch(1)
        scroll.setWidget(body)
        lay.addWidget(scroll)
        return page

    def _build_practice_tab(self):
        page = QWidget()
        self.practice_stack = QStackedLayout(page)

        # menu: vocabulary / grammar / honorific hub
        menu = QWidget()
        lay = QVBoxLayout(menu)
        lay.setContentsMargins(4, 12, 4, 4)
        lay.setSpacing(12)
        hint = QLabel("Correct answers build yellow stars on each word; a miss resets them. "
                      "Three yellows become a permanent green star (one per word per day).")
        hint.setWordWrap(True)
        hint.setProperty("class", "muted")
        lay.addWidget(hint)

        self.vocab_badge = QLabel("")
        self.vocab_badge.setProperty("class", "trackStars")
        self.hon_badge = QLabel("")
        self.hon_badge.setProperty("class", "trackStars")

        frame_v = QFrame()
        frame_v.setProperty("class", "modeCard")
        fv = QHBoxLayout(frame_v)
        fv.setContentsMargins(20, 16, 20, 16)
        tv = QVBoxLayout()
        t = QLabel("Vocabulary Quiz")
        t.setProperty("class", "modeTitle")
        tv.addWidget(t)
        d = QLabel("JP → EN, EN → JP and typing — kanji, kana and rōmaji all accepted")
        d.setWordWrap(True)
        d.setProperty("class", "muted")
        tv.addWidget(d)
        fv.addLayout(tv, 1)
        fv.addWidget(self.vocab_badge)
        bv = QPushButton("Start")
        bv.setProperty("class", "primary")
        bv.clicked.connect(lambda _=False: self._show_table("vocab"))
        fv.addWidget(bv)
        lay.addWidget(frame_v)

        frame_g = QFrame()
        frame_g.setProperty("class", "modeCard")
        fg = QHBoxLayout(frame_g)
        fg.setContentsMargins(20, 16, 20, 16)
        tg = QVBoxLayout()
        t2 = QLabel("Grammar Quiz")
        t2.setProperty("class", "modeTitle")
        tg.addWidget(t2)
        d2 = QLabel("Pattern ↔ meaning and example-sentence translations")
        d2.setWordWrap(True)
        d2.setProperty("class", "muted")
        tg.addWidget(d2)
        fg.addLayout(tg, 1)
        bg = QPushButton("Start")
        bg.setProperty("class", "primary")
        bg.clicked.connect(lambda _=False: self._show_table("grammar"))
        fg.addWidget(bg)
        lay.addWidget(frame_g)

        frame_k = QFrame()
        frame_k.setProperty("class", "modeCard")
        fk = QHBoxLayout(frame_k)
        fk.setContentsMargins(20, 16, 20, 16)
        tk = QVBoxLayout()
        t3 = QLabel("Honorific Drill")
        t3.setProperty("class", "modeTitle")
        tk.addWidget(t3)
        d3 = QLabel("Four drills turning verbs into 尊敬語 — with audio")
        d3.setWordWrap(True)
        d3.setProperty("class", "muted")
        tk.addWidget(d3)
        fk.addLayout(tk, 1)
        fk.addWidget(self.hon_badge)
        bk = QPushButton("Choose")
        bk.setProperty("class", "primary")
        bk.clicked.connect(lambda _=False: self.practice_stack.setCurrentWidget(self._hub))
        fk.addWidget(bk)
        lay.addWidget(frame_k)
        lay.addStretch(1)

        # hub: the four honorific sub-drills
        self._hub = QWidget()
        hub_lay = QVBoxLayout(self._hub)
        hub_lay.setContentsMargins(4, 12, 4, 4)
        hub_lay.setSpacing(10)
        hub_back = QPushButton("‹ Back to practice")
        hub_back.setProperty("class", "ghost")
        hub_back.clicked.connect(lambda _=False: self.practice_stack.setCurrentIndex(0))
        hub_lay.addWidget(hub_back)
        for key, name, desc in (
            ("keigo-en-jp", "English → Japanese",
             "See the meaning, type the honorific (audio after you answer)"),
            ("keigo-jp-en", "Japanese → English",
             "Hear and see the honorific word, then type its meaning"),
            ("keigo-hon-norm", "Honorific → Normal",
             "Hear the honorific, type the base verb it comes from"),
            ("keigo-norm-hon", "Normal → Honorific",
             "Hear the base verb, type its honorific form"),
        ):
            b = QPushButton(f"{name}\n{desc}")
            b.setProperty("class", "hub")
            b.setMinimumHeight(72)
            b.clicked.connect(lambda _=False, k=key: self._show_table(k))
            hub_lay.addWidget(b)
        hub_lay.addStretch(1)

        # table: Education-Perfect-style preview before each drill
        self.table_page = QuizTable(self.progress,
                                    on_start=lambda: self._start_quiz(self.table_key),
                                    on_back=lambda: self.practice_stack.setCurrentIndex(
                                        self.table_back_target))
        self.table_key = "vocab"
        self.table_back_target = 0

        self.practice_stack.addWidget(menu)   # 0
        self.practice_stack.addWidget(self._hub)  # 1
        self.practice_stack.addWidget(self.table_page)  # 2
        return page

    # ---------- mastery summary ----------
    def _refresh_mastery(self):
        ids = [v["id"] for v in self.lesson["vocab"]]
        mastered = self.progress.mastered_words(ids)
        self.star_pill.setText(f"🟢 {mastered}/{len(ids)} words")
        self.vocab_badge.setText(f"{mastered}/{len(ids)}\nwords mastered")
        hon_ids = [v["id"] for v in self._keigo_verbs]
        self.hon_badge.setText(f"{self.progress.mastered_words(hon_ids)}/{len(hon_ids)}\nverbs mastered")
        if hasattr(self, "_cards"):
            self._refresh_cards()

    # ---------- quizzes ----------
    def _sort_rows(self, rows):
        """Weak words (0 greens) first, most-missed at the top; grammar rows last."""
        def key(r):
            vid = r.get("vid")
            if vid is None:
                return (2, 0)
            c = self.progress.word_card(vid)
            return (0 if c["green"] == 0 else 1, -c["wrong"])
        return sorted(rows, key=key)

    def _show_table(self, key):
        self.table_key = key
        if key == "vocab":
            title = "Vocabulary — lesson words"
            rows = vocab_rows(self.lesson)
            self.table_back_target = 0
        elif key == "grammar":
            title = "Grammar — patterns and meanings"
            rows = grammar_rows(self.lesson)
            self.table_back_target = 0
        else:
            titles = {"keigo-en-jp": "English → Japanese",
                      "keigo-jp-en": "Japanese → English",
                      "keigo-hon-norm": "Honorific → Normal",
                      "keigo-norm-hon": "Normal → Honorific"}
            title = f'{titles[key]} — words in this drill'
            rows = keigo_rows(self.data, self.lesson_id, key)
            self.table_back_target = 1
        self.table_page.set_rows(title, self._sort_rows(rows))
        self.practice_stack.setCurrentWidget(self.table_page)

    def _start_quiz(self, key):
        self.key = key
        if key == "vocab":
            items = quiz_vocab(self.lesson)
        elif key == "grammar":
            items = quiz_grammar(self.lesson)
        else:
            items = KEIGO_BUILDERS[key](self.data, self.lesson_id)
        self.greens_gained = 0
        self.tabs.hide()
        self.quiz.start(items, sound=self.progress.data.get("soundOn", True))

    def _start_current(self):
        self.result_frame.hide()
        self._start_quiz(self.key)

    def _on_answer(self, item, ok):
        status = None
        if item.get("vocabId"):
            status = self.progress.word_answer(item["vocabId"], ok)
            if status.get("gained_green"):
                self.greens_gained += 1
        self.quiz.show_word_status(status)
        if self.on_change:
            self.on_change()

    def _on_finished(self, result):
        score, total = result["score"], result["total"]
        ratio = score / total if total else 0
        xp = round(ratio * 20) + (5 if ratio == 1 else 0)
        self.progress.add_xp(xp)
        self._refresh_mastery()
        self.res_title.setText("Perfect!" if ratio == 1 else "Great job!")
        self.res_score.setText(f"{score} / {total}")
        self.res_note.setText(f"+{xp} XP · {self.greens_gained} green star(s) earned")
        self.result_frame.show()
        if self.on_change:
            self.on_change()

    def on_quiz_quit(self):
        self.tabs.show()
        self.practice_stack.setCurrentIndex(0)
        self.result_frame.hide()
        self._refresh_mastery()

    def _show_practice(self):
        self.result_frame.hide()
        self.tabs.show()
        self.tabs.setCurrentIndex(2)
        self.practice_stack.setCurrentIndex(0)
        self._refresh_mastery()

    def _back(self):
        self.on_back()
