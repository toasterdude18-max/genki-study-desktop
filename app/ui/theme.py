"""App-wide QSS themes. One template, two palettes (light/dark)."""

# ---------- palettes ----------
LIGHT = {
    "bg": "#f6f7fb", "panel": "#ffffff", "border": "#e5e7eb",
    "text": "#1f2430", "muted": "#6b7280",
    "accent": "#ff9f43", "accent_hover": "#f0902a", "accent_text": "#ffffff",
    "nav_bg": "#2b3242", "nav_text": "#cbd5e1", "nav_hover": "#384154",
    "pill_xp": "#fff3e0", "pill_xp_text": "#b45309",
    "pill_streak": "#fee2e2", "pill_streak_text": "#b91c1c",
    "pill_stars": "#fff7e0", "pill_stars_text": "#b45309",
    "extra": "#7c3aed", "extra_bg": "#f5f3ff",
    "ok_bg": "#ecfdf5", "ok_border": "#22c55e", "ok_text": "#15803d",
    "bad_bg": "#fef2f2", "bad_border": "#ef4444", "bad_text": "#b91c1c",
    "danger_border": "#fecaca",
    "input_border": "#e5e7eb", "input_focus": "#3b82f6",
    "lesson_started_bg": "#fff7e0", "lesson_started_border": "#f59e0b",
    "lesson_done_bg": "#ecfdf5", "lesson_done_border": "#22c55e",
    "lesson_locked_bg": "#f3f4f6", "lesson_locked_border": "#e5e7eb",
    "lesson_locked_text": "#9ca3af",
    "disabled": "#d1d5db",
    "weak_bg": "#fffbeb", "weak_border": "#f59e0b",
    "progress_bg": "#e5e7eb",
    "dash_bg": "#ffe6c7",          # home page: orange
    "jp_color": "#d90429",         # Japanese text in quizzes: red
    "en_color": "#1d4ed8",         # English text in quizzes: blue
}

DARK = {
    "bg": "#16181d", "panel": "#1f242e", "border": "#2e3542",
    "text": "#e7eaf0", "muted": "#9aa3b2",
    "accent": "#ff9f43", "accent_hover": "#f0902a", "accent_text": "#1a1410",
    "nav_bg": "#101319", "nav_text": "#9aa3b2", "nav_hover": "#232a36",
    "pill_xp": "#3a2a12", "pill_xp_text": "#fbbf24",
    "pill_streak": "#3b1518", "pill_streak_text": "#fca5a5",
    "pill_stars": "#3a2a12", "pill_stars_text": "#fbbf24",
    "extra": "#a78bfa", "extra_bg": "#2b2440",
    "ok_bg": "#16301f", "ok_border": "#22c55e", "ok_text": "#86efac",
    "bad_bg": "#381b1b", "bad_border": "#ef4444", "bad_text": "#fca5a5",
    "danger_border": "#4a2323",
    "input_border": "#2e3542", "input_focus": "#3b82f6",
    "lesson_started_bg": "#3a2a12", "lesson_started_border": "#f59e0b",
    "lesson_done_bg": "#16301f", "lesson_done_border": "#22c55e",
    "lesson_locked_bg": "#1a1e26", "lesson_locked_border": "#2e3542",
    "lesson_locked_text": "#5c6675",
    "disabled": "#3a414e",
    "weak_bg": "#2e2510", "weak_border": "#f59e0b",
    "progress_bg": "#2e3542",
    "dash_bg": "#2b2015",          # home page: warm dark orange
    "jp_color": "#ff6b81",         # Japanese text in quizzes: red
    "en_color": "#60a5fa",         # English text in quizzes: blue
}

_TEMPLATE = """
QWidget {{ font-family: "Segoe UI", "Noto Sans JP", "Yu Gothic UI", sans-serif; font-size: 14px; color: {text}; }}
QMainWindow, QWidget#root {{ background: {bg}; }}
QWidget#dashPage {{ background: {dash_bg}; }}

/* ---------- language colours in quizzes ---------- */
QLabel.prompt[lang="ja"] {{ color: {jp_color}; }}
QLabel.prompt[lang="en"] {{ color: {en_color}; }}
QPushButton.opt[lang="ja"] {{ color: {jp_color}; }}
QPushButton.opt[lang="en"] {{ color: {en_color}; }}

/* ---------- top bar ---------- */
QWidget#topbar {{ background: {panel}; border-bottom: 1px solid {border}; }}
QLabel#appTitle {{ font-size: 19px; font-weight: 800; color: #e8891f; }}
QLabel.pill {{ background: {pill_xp}; color: {pill_xp_text}; border-radius: 13px; padding: 5px 14px; font-weight: 700; font-size: 14px; }}
QLabel.pillStreak {{ background: {pill_streak}; color: {pill_streak_text}; border-radius: 13px; padding: 5px 14px; font-weight: 700; }}
QLabel.pillStars {{ background: {pill_stars}; color: {pill_stars_text}; border-radius: 13px; padding: 5px 14px; font-weight: 800; }}

/* ---------- nav rail ---------- */
QListWidget#nav {{ background: {nav_bg}; border: none; color: {nav_text}; font-size: 15px; padding: 10px 0; }}
QListWidget#nav::item {{ padding: 13px 18px; margin: 3px 10px; border-radius: 10px; }}
QListWidget#nav::item:hover {{ background: {nav_hover}; }}
QListWidget#nav::item:selected {{ background: {accent}; color: #ffffff; font-weight: 700; }}

/* ---------- headings & cards ---------- */
QLabel.h1 {{ font-size: 26px; font-weight: 800; }}
QLabel.h2 {{ font-size: 17px; font-weight: 700; }}
QLabel.muted {{ color: {muted}; }}
QFrame.card {{ background: {panel}; border: 1px solid {border}; border-radius: 16px; }}
QLabel.statValue {{ font-size: 26px; font-weight: 800; color: #e8891f; }}
QLabel.statLabel {{ color: {muted}; font-size: 13px; }}

/* ---------- buttons ---------- */
QPushButton.primary {{ background: {accent}; color: {accent_text}; border: none; border-radius: 12px;
    padding: 12px 26px; font-size: 15px; font-weight: 700; }}
QPushButton.primary:hover {{ background: {accent_hover}; }}
QPushButton.primary:pressed {{ background: #e8891f; }}
QPushButton.primary:disabled {{ background: {disabled}; }}
QPushButton.ghost {{ background: transparent; color: {muted}; border: none; font-weight: 600; padding: 6px 10px; }}
QPushButton.ghost:hover {{ color: {text}; }}
QPushButton.danger {{ background: transparent; color: {bad_text}; border: 1px solid {danger_border}; border-radius: 10px; padding: 8px 16px; }}

/* ---------- lesson tiles ---------- */
QPushButton.lesson {{ background: {panel}; border: 1px solid {border}; border-radius: 14px; padding: 12px;
    font-size: 13px; font-weight: 600; }}
QPushButton.lesson:hover {{ border-color: {accent}; }}
QPushButton.lesson[started="1"] {{ background: {lesson_started_bg}; border-color: {lesson_started_border}; }}
QPushButton.lesson[mastered="1"] {{ background: {lesson_done_bg}; border-color: {lesson_done_border}; }}
QPushButton.lesson[locked="1"] {{ background: {lesson_locked_bg}; border-color: {lesson_locked_border}; color: {lesson_locked_text}; }}

/* ---------- tabs ---------- */
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{ background: {panel}; border: 1px solid {border}; padding: 10px 22px; margin-right: 6px;
    border-radius: 12px; color: {muted}; font-weight: 700; font-size: 14px; }}
QTabBar::tab:selected {{ background: {accent}; border-color: {accent}; color: #ffffff; }}
QTabBar::tab:hover:!selected {{ border-color: {accent}; }}

/* ---------- flashcards ---------- */
QPushButton.flash {{ background: {panel}; border: 1px solid {border}; border-radius: 14px;
    font-size: 17px; font-weight: 700; }}
QPushButton.flash:hover {{ border-color: {accent}; }}
QPushButton.flash[extra="1"] {{ border: 2px solid {extra}; background: {extra_bg}; }}
QPushButton.flash[weak="1"] {{ border: 2px solid {weak_border}; background: {weak_bg}; }}

/* ---------- practice hub (honorific sub-drills) ---------- */
QPushButton.hub {{ background: {panel}; border: 2px solid {border}; border-radius: 14px;
    padding: 14px 18px; font-weight: 700; font-size: 15px; }}
QPushButton.hub:hover {{ border-color: {accent}; }}
QLabel.weakBadge {{ color: {pill_stars_text}; font-weight: 800; }}
QPushButton.wordBtn {{ background: transparent; border: none; color: {text}; font-weight: 600; }}
QPushButton.wordBtn:hover {{ color: #e8891f; }}

/* ---------- grammar ---------- */
QFrame.gram {{ background: {panel}; border: 1px solid {border}; border-radius: 12px; }}
QFrame.gram[extra="1"] {{ background: {extra_bg}; border-color: {extra}; }}
QLabel.gramPat {{ font-weight: 800; font-size: 16px; }}
QLabel.gramPat[extra="1"] {{ color: {extra}; }}
QLabel.gramEx {{ color: {muted}; }}

/* ---------- practice mode cards ---------- */
QFrame.modeCard {{ background: {panel}; border: 2px solid {border}; border-radius: 16px; }}
QFrame.modeCard:hover {{ border-color: {accent}; }}
QLabel.modeTitle {{ font-size: 17px; font-weight: 800; }}
QLabel.trackStars {{ color: {pill_stars_text}; font-weight: 800; font-size: 15px; }}
QLabel.trackPips {{ color: #d97706; font-weight: 700; }}
QLabel.gateHint {{ color: {muted}; font-size: 12px; }}

/* ---------- quiz ---------- */
QFrame.quizCard {{ background: {panel}; border: 1px solid {border}; border-radius: 18px; }}
QLabel.prompt {{ font-size: 26px; font-weight: 800; }}
QLabel.countLbl {{ color: {muted}; }}
QPushButton.opt {{ background: {panel}; border: 2px solid {border}; border-radius: 14px;
    padding: 13px 18px; font-size: 16px; font-weight: 600; }}
QPushButton.opt:hover {{ border-color: {accent}; }}
QPushButton.opt[sel="1"] {{ border-color: {input_focus}; }}
QPushButton.opt[ok="1"] {{ border-color: {ok_border}; background: {ok_bg}; color: {ok_text}; font-weight: 700; }}
QPushButton.opt[bad="1"] {{ border-color: {bad_border}; background: {bad_bg}; color: {bad_text}; }}
QPushButton.opt:disabled {{ color: {muted}; }}
QLineEdit.answer {{ background: {panel}; border: 2px solid {input_border}; border-radius: 14px;
    padding: 12px 14px; font-size: 19px; }}
QLineEdit.answer:focus {{ border-color: {input_focus}; }}
QLabel.feedbackOk {{ color: {ok_text}; font-weight: 700; font-size: 16px; }}
QLabel.feedbackBad {{ color: {bad_text}; font-weight: 700; font-size: 16px; }}
QLabel.pips {{ color: #d97706; font-weight: 800; font-size: 16px; }}
QLabel.starGain {{ color: {pill_stars_text}; font-weight: 800; font-size: 17px; }}
QLabel.scoreBig {{ font-size: 48px; font-weight: 800; color: {pill_stars_text}; }}
QLabel.resultTitle {{ font-size: 22px; font-weight: 800; }}

/* ---------- progress bar & inputs ---------- */
QProgressBar {{ background: {progress_bg}; border: none; border-radius: 4px; min-height: 9px; max-height: 9px; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 4px; }}
QSpinBox {{ background: {panel}; border: 1px solid {border}; border-radius: 10px; padding: 5px 8px; min-width: 80px; }}
QCheckBox {{ spacing: 10px; }}
QScrollArea {{ border: none; background: transparent; }}
"""


def build_qss(palette):
    return _TEMPLATE.format(**palette)


def apply_theme(dark=False):
    """Apply the light or dark stylesheet app-wide (reads the QApplication)."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(build_qss(DARK if dark else LIGHT))


def set_titlebar_dark(window, dark):
    """Darken the native Windows title bar (best-effort, no-op on failure)."""
    try:
        import ctypes
        hwnd = int(window.winId())
        value = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (20H1+ / earlier)
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value))
                break
            except Exception:
                continue
    except Exception:
        pass


QSS = build_qss(LIGHT)  # kept for tests and one-shot usage
