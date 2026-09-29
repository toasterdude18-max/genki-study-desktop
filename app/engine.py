"""XP, streak and per-word star logic.

Word stars are owned by the words themselves, not the activities:
  - a correct answer adds one yellow star (max YELLOW_MAX)
  - YELLOW_MAX yellows convert into one green star (max one green per word per day)
  - a wrong answer resets all yellows; greens are permanent
  - weak words are those with no green star
"""
from datetime import datetime, timedelta

from app import models as M


def _today(d=None):
    return (d or datetime.now()).strftime("%Y-%m-%d")


def _days_from(n):
    return (datetime.now() + timedelta(days=n)).strftime("%Y-%m-%d")


class Progress:
    def __init__(self, store):
        self.store = store
        self.data = store.load(M.DEFAULT_PROGRESS)
        self._migrate()
        self._refresh_streak()

    def save(self):
        self.store.save(self.data)

    # ---------- migration from earlier versions ----------
    def _migrate(self):
        self.data.setdefault("words", {})
        legacy_srs = self.data.pop("srs", {})
        if legacy_srs and not self.data["words"]:
            # old Leitner boxes seed a starting green so progress is not lost
            for vid, c in legacy_srs.items():
                if isinstance(c, dict) and c.get("box", 0) >= 3:
                    self.data["words"][vid] = {
                        "yellow": 0, "green": 1, "lastGreen": _days_from(-7),
                        "right": c.get("right", 0), "wrong": c.get("wrong", 0),
                        "seen": c.get("seen", 0)}

    # ---------- xp / streak ----------
    def _refresh_streak(self):
        t, y = _today(), _days_from(-1)
        if self.data["lastStudied"] and self.data["lastStudied"] not in (t, y):
            self.data["streak"] = 0
            self.save()

    def add_xp(self, amount):
        if amount <= 0:
            return
        t = _today()
        d = self.data
        d["xp"] += amount
        d["dailyXp"][t] = d["dailyXp"].get(t, 0) + amount
        if d["lastStudied"] != t:
            d["streak"] = d["streak"] + 1 if d["lastStudied"] == _days_from(-1) else 1
            d["lastStudied"] = t
        cutoff = _days_from(-370)
        for k in [k for k in d["dailyXp"] if k < cutoff]:
            del d["dailyXp"][k]
        self.save()

    def today_xp(self):
        return self.data["dailyXp"].get(_today(), 0)

    def week_xp(self):
        return sum(self.data["dailyXp"].get(_days_from(-i), 0) for i in range(7))

    def set(self, **kwargs):
        self.data.update(kwargs)
        self.save()

    # ---------- word-owned stars ----------
    def word_card(self, vocab_id):
        return self.data["words"].get(vocab_id, {
            "yellow": 0, "green": 0, "lastGreen": None,
            "right": 0, "wrong": 0, "seen": 0})

    def word_answer(self, vocab_id, correct):
        """Record one answer for a word.

        Returns {yellow, green, gained_green, lost} for feedback display.
        """
        c = self.word_card(vocab_id)
        c["seen"] += 1
        gained = lost = False
        if correct:
            c["right"] += 1
            c["yellow"] = min(c["yellow"] + 1, M.YELLOW_MAX)
            if c["yellow"] >= M.YELLOW_MAX:
                if c.get("lastGreen") != _today():
                    c["green"] += 1
                    c["yellow"] = 0
                    c["lastGreen"] = _today()
                    gained = True
                # else: hold at max yellows until tomorrow (one green per day)
        else:
            c["wrong"] += 1
            if c["yellow"] > 0:
                c["yellow"] = 0
                lost = True
        self.data["words"][vocab_id] = c
        self.save()
        return {"yellow": c["yellow"], "green": c["green"],
                "gained_green": gained, "lost": lost}

    def mastered_words(self, vocab_ids):
        """Count of words with at least one green star."""
        return sum(1 for vid in vocab_ids if self.word_card(vid)["green"] > 0)

    def weak_words(self, vocab_items):
        """[(vocab, card), ...] for 0-green words, most-missed first."""
        pairs = []
        for v in vocab_items:
            c = self.word_card(v["id"])
            if c["green"] == 0:
                pairs.append((v, c))
        pairs.sort(key=lambda t: (-t[1]["wrong"], t[0]["id"]))
        return pairs
