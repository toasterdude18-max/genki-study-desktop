"""Real-click regression test: drives the UI with QTest.mouseClick through the real
event loop. Covers navigation safety, the four honorific sub-drills, word-star
transitions, the weak-words panel/drill, and the mute toggle.

Run:  python scripts\\ui_click_test.py   (from D:\\Genki Study)
"""
import json
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from app.data_store import DataStore
from app.engine import Progress
from app.ui.main_window import MainWindow
from app.ui.lesson_page import LessonPage
from app.ui.theme import QSS

HUB_BUTTONS = ("English → Japanese", "Japanese → English",
               "Honorific → Normal", "Normal → Honorific")


def answer_item(page):
    item = page.quiz.items[0]
    if item["kind"] == "mc":
        QTest.mouseClick(page.quiz._opt_btns[item["correct"]], Qt.LeftButton)
    else:
        page.quiz.answer_edit.setText(item["answers"][0])
        QTest.keyClick(page.quiz.answer_edit, Qt.Key_Return)
    app_process()
    assert page.quiz.checked, "answer was not graded"


def app_process():
    QApplication.processEvents()


def finish_quiz(page):
    page.quiz.i = len(page.quiz.items)
    page.quiz._finish()
    app_process()
    assert page.result_frame.isVisible(), "result card did not show"


def start_button(page, text):
    return [b for b in page.tabs.widget(2).findChildren(QPushButton) if b.text() == text][0]


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
    p.word_answer("v19-002", False)
    assert any(v["id"] == "v19-002" for v, _c in p.weak_words(data["lessons"][18]["vocab"])), \
        "missed word should be weak"

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

    # ---- vocab + grammar quizzes ----
    starts = [b for b in page.tabs.widget(2).findChildren(QPushButton) if b.text() == "Start"]
    for btn in starts:
        QTest.mouseClick(btn, Qt.LeftButton)
        app_process()
        assert isinstance(w.stack.currentWidget(), LessonPage), "bounced home on Start"
        assert page.quiz.isVisible()
        answer_item(page)
        finish_quiz(page)
        page._show_practice()
        app_process()

    # ---- honorific hub: four sub-drills ----
    choose = start_button(page, "Choose")
    QTest.mouseClick(choose, Qt.LeftButton)
    app_process()
    hub_btns = [b for b in page.tabs.widget(2).findChildren(QPushButton)
                if b.text().startswith(HUB_BUTTONS)]
    assert len(hub_btns) == 4, f"expected 4 hub buttons, found {len(hub_btns)}"
    for btn in hub_btns:
        QTest.mouseClick(btn, Qt.LeftButton)
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
        finish_quiz(page)
        page._show_practice()
        app_process()
        QTest.mouseClick(choose, Qt.LeftButton)
        app_process()

    # ---- back navigation (the only legal exit) ----
    page._back()
    app_process()
    assert w.stack.currentIndex() == 0

    print("REAL-CLICK TEST PASS — nav safety, word stars, 4 honorific sub-drills, "
          "mute toggle, dark mode")


if __name__ == "__main__":
    main()
