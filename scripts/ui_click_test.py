"""Real-click regression test: drives the UI with QTest.mouseClick through the real
event loop. Covers navigation safety, preview tables for every quiz, the four
honorific sub-drills, word-star transitions, banner feedback, Enter-to-advance,
mute toggle and dark mode.

Run:  python scripts\\ui_click_test.py   (from the app root)
"""
import json
import os
import sys
import tempfile
from datetime import datetime

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def today_str():
    return datetime.now().strftime("%Y-%m-%d")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from app.data_store import DataStore
from app.engine import Progress
from app.ui.main_window import MainWindow
from app.ui.lesson_page import LessonPage
from app.ui.theme import QSS
from app.quiz import session_items, vocab_item, SESSION_SIZE
from app import tts

HUB_BUTTONS = ("English → Japanese", "Japanese → English",
               "Honorific → Normal", "Normal → Honorific")


def answer_item(page):
    item = page.quiz.items[0]
    assert item["kind"] == "type", "all questions must be typing-only (no multiple choice)"
    page.quiz.answer_edit.setText(item["answers"][0])
    QTest.keyClick(page.quiz.answer_edit, Qt.Key_Return)
    app_process()
    assert page.quiz.checked, "answer was not graded"
    assert page.quiz.feedback_lbl.property("class") in ("feedbackOk", "feedbackBad"), \
        "banner feedback class not set"


def app_process():
    QApplication.processEvents()


def finish_quiz(page):
    page.quiz.i = len(page.quiz.items)
    page.quiz._finish()
    app_process()
    assert page.result_frame.isVisible(), "result card did not show"


def start_button(page, text):
    """Find a button on the practice MENU (not the table's own Start)."""
    menu = page.practice_stack.widget(0)
    return [b for b in menu.findChildren(QPushButton) if b.text() == text][0]


def enter_advances(page):
    before = page.quiz.i
    QTest.keyClick(page.quiz.answer_edit, Qt.Key_Return)  # real user presses Enter in the box
    app_process()
    assert page.quiz.i == before + 1, "Enter did not advance after checking"


def main():
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    data = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       "data", "genki-data.json"), encoding="utf-8"))
    store = DataStore(os.path.join(tempfile.mkdtemp(), "progress.json"))
    p = Progress(store)
    p.set(soundOn=False)  # keep the test silent
    w = MainWindow(data, p)
    w.resize(1500, 950)
    w.show()
    app_process()

    # ---- dark mode toggle ----
    assert p.data.get("darkMode") is False
    QTest.mouseClick(w.theme_btn, Qt.LeftButton)
    app_process()
    assert p.data["darkMode"] is True, "toggle did not persist dark mode"
    assert "#16181d" in QApplication.instance().styleSheet(), "dark stylesheet not applied"
    assert w.theme_btn.text() == "☀️"
    QTest.mouseClick(w.theme_btn, Qt.LeftButton)
    app_process()
    assert p.data["darkMode"] is False and w.theme_btn.text() == "🌙", "toggle did not revert"

    # ---- word-star engine rules ----
    st = [p.word_answer("v19-001", True) for _ in range(3)]
    assert st[0]["yellow"] == 1 and st[1]["yellow"] == 2, "yellows not accumulating"
    assert st[2]["gained_green"] and st[2]["green"] == 1 and st[2]["yellow"] == 0, \
        "3 yellows should convert to a green"
    st4 = p.word_answer("v19-001", True)
    assert not st4["gained_green"] and st4["yellow"] == 1, \
        "second green on the same day must be blocked"
    st5 = p.word_answer("v19-001", False)
    assert st5["lost"] and st5["yellow"] == 0 and st5["green"] == 1, \
        "a miss resets yellows but never greens"

    # ---- TTS: main-thread engine survives speak/stop/speak cycles ----
    tts.speak('あ')
    tts.stop()
    tts.speak('い')
    assert tts.has_ja_voice() is True, "TTS engine did not survive the stop cycle"

    # ---- session re-presentation: a word comes back within the next 10 ----
    pool = data["lessons"][18]["vocab"]
    sess = session_items(pool, vocab_item, SESSION_SIZE)
    assert len(sess) == SESSION_SIZE, f"session should be {SESSION_SIZE} items"
    assert all(it["kind"] == "type" for it in sess), "vocab sessions must be typing-only"
    seen = set()
    for i in range(SESSION_SIZE - 10):
        vid = sess[i].get("vocabId")
        if vid in seen:
            continue
        seen.add(vid)
        window = [x.get("vocabId") for x in sess[i + 1:i + 11]]
        assert vid in window, f"{vid} not re-presented within the next 10"

    # ---- eligibility: green words rest until all green or 2 days ----
    l19_pool = data["lessons"][18]["vocab"]
    p.word_answer("v19-002", True)
    elig = p.eligible_words(l19_pool)
    assert all(p.word_card(v["id"])["green"] == 0 for v in elig), \
        "green words must rest while others lack greens"
    assert not any(v["id"] == "v19-001" for v in elig), "rested green word leaked in"
    for v in l19_pool:
        c = p.word_card(v["id"])
        if c["green"] == 0:
            p.data["words"][v["id"]] = {**c, "green": 1, "lastGreen": "2000-01-01"}
    elig2 = p.eligible_words(l19_pool)
    expected = {v["id"] for v in l19_pool} - {"v19-001"}  # v19-001 green is from today
    assert {v["id"] for v in elig2} == expected, \
        "old greens should return, but today's green must still rest"
    # fresh green must rest even when everything is green
    p.data["words"]["v19-003"]["lastGreen"] = today_str()
    elig3 = p.eligible_words(l19_pool)
    assert not any(v["id"] == "v19-003" for v in elig3), \
        "fresh green (<2 days) must rest"

    # ---- open lesson 19 via a REAL click ----
    tile = w.dashboard.lesson_btns[19][0]
    QTest.mouseClick(tile, Qt.LeftButton)
    app_process()
    assert isinstance(w.stack.currentWidget(), LessonPage), "lesson did not open"
    page = w.stack.currentWidget()

    tab_bar = page.tabs.tabBar()
    QTest.mouseClick(tab_bar, Qt.LeftButton, Qt.NoModifier, tab_bar.tabRect(2).center())
    app_process()
    assert page.tabs.currentIndex() == 2

    # ---- vocab + grammar: menu -> preview table -> quiz ----
    menu = page.practice_stack.widget(0)
    starts = [b for b in menu.findChildren(QPushButton) if b.text() == "Start"]
    assert len(starts) == 2, f"expected 2 Start buttons, found {len(starts)}"
    for btn in starts:
        QTest.mouseClick(btn, Qt.LeftButton)
        app_process()
        assert isinstance(w.stack.currentWidget(), LessonPage), "bounced home on Start"
        assert page.practice_stack.currentWidget() is page.table_page, "table did not open"
        assert page.table_page.table.rowCount() > 0, "table is empty"
        QTest.mouseClick(page.table_page.start_btn, Qt.LeftButton)
        app_process()
        assert page.quiz.isVisible(), "quiz did not start from table"
        answer_item(page)
        enter_advances(page)
        # "I don't know" submits a null answer, counts as wrong, resets yellows
        item_dk = page.quiz.items[page.quiz.i]
        QTest.mouseClick(page.quiz.dont_know_btn, Qt.LeftButton)
        app_process()
        assert page.quiz.checked, "I don't know did not submit"
        assert page.quiz.feedback_lbl.property("class") == "feedbackBad", \
            "I don't know must show the wrong-answer banner"
        assert not page.quiz.dont_know_btn.isVisible(), "button should hide after submitting"
        if item_dk.get("vocabId"):
            assert p.word_card(item_dk["vocabId"])["yellow"] == 0, \
                "I don't know must reset yellow stars"
        enter_advances(page)
        finish_quiz(page)
        assert page.cont_btn.isVisible(), "Continue button missing after a 50-word session"
        QTest.mouseClick(page.cont_btn, Qt.LeftButton)
        app_process()
        assert page.quiz.isVisible(), "Continue did not start another session"
        assert len(page.quiz.items) == 50, "continued session is not 50 words"
        page.on_quiz_quit()
        app_process()
        page._show_practice()
        app_process()

    # ---- honorific hub: choose -> table -> quiz (all four sub-drills) ----
    choose = start_button(page, "Choose")
    QTest.mouseClick(choose, Qt.LeftButton)
    app_process()
    hub_btns = [b for b in page.practice_stack.widget(1).findChildren(QPushButton)
                if b.text().startswith(HUB_BUTTONS)]
    assert len(hub_btns) == 4, f"expected 4 hub buttons, found {len(hub_btns)}"
    for btn in hub_btns:
        QTest.mouseClick(btn, Qt.LeftButton)
        app_process()
        assert page.practice_stack.currentWidget() is page.table_page, "keigo table did not open"
        assert page.table_page.table.rowCount() > 0, "keigo table is empty"
        QTest.mouseClick(page.table_page.start_btn, Qt.LeftButton)
        app_process()
        assert isinstance(w.stack.currentWidget(), LessonPage), "hub drill navigated home"
        assert page.quiz.isVisible()
        # mute toggle
        QTest.mouseClick(page.quiz.mute_btn, Qt.LeftButton)
        app_process()
        assert page.quiz.sound is True, "mute toggle did not flip sound on"
        QTest.mouseClick(page.quiz.mute_btn, Qt.LeftButton)
        app_process()
        assert page.quiz.sound is False, "mute toggle did not flip sound off"
        QTest.mouseClick(page.quiz.mute_btn, Qt.LeftButton)
        app_process()
        answer_item(page)
        enter_advances(page)
        finish_quiz(page)
        page._show_practice()
        app_process()
        QTest.mouseClick(choose, Qt.LeftButton)
        app_process()
    # ---- table back navigation: vocab -> table -> back -> menu ----
    QTest.mouseClick(start_button(page, "Start"), Qt.LeftButton)
    app_process()
    assert page.practice_stack.currentWidget() is page.table_page
    table_back = [b for b in page.table_page.findChildren(QPushButton) if b.text() == "‹ Back"][0]
    QTest.mouseClick(table_back, Qt.LeftButton)
    app_process()
    assert page.practice_stack.currentIndex() == 0, "table back did not return to menu"

    # ---- back navigation (the only legal exit) ----
    page._back()
    app_process()
    assert w.stack.currentIndex() == 0

    print("REAL-CLICK TEST PASS — nav safety, word stars, preview tables, banner "
          "feedback, Enter-to-advance, 4 honorific sub-drills, mute toggle, dark mode")


if __name__ == "__main__":
    main()
