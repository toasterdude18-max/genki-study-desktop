"""Genki Study — offline desktop companion (PySide6).

Run with run.bat or:  python app\\main.py
"""
import json
import os
import sys
import traceback
from datetime import datetime


def _app_dir():
    """Folder holding data/, assets/ etc. Works for source, onefile, and onedir."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(base, "data")):
            return base                       # onefile: exe sits in the app root
        parent = os.path.dirname(base)
        if os.path.exists(os.path.join(parent, "data")):
            return parent                     # onedir: exe sits in dist\<name>
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR = _app_dir()
ICON_PATH = os.path.join(APP_DIR, "assets", "genki.ico")


def _log(msg):
    """Best-effort early log line (works before Qt/PySide6 is imported)."""
    try:
        path = os.path.join(APP_DIR, "data", "state", "app.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] BOOT {msg}\n")
    except Exception:
        pass


# Never let inherited Qt environment variables override the bundled plugins.
for _qt_var in ("QT_QPA_PLATFORM", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
    os.environ.pop(_qt_var, None)


def _check_runtime():
    """Before Qt loads, verify the bundled runtime is complete so a mid-update
    launch shows a friendly message instead of the cryptic Qt plugin error."""
    if not getattr(sys, "frozen", False):
        return True
    internal = os.path.join(APP_DIR, "_internal")
    critical = [
        os.path.join(internal, "PySide6", "Qt6Core.dll"),
        os.path.join(internal, "PySide6", "Qt6Gui.dll"),
        os.path.join(internal, "PySide6", "Qt6Widgets.dll"),
        os.path.join(internal, "PySide6", "plugins", "platforms", "qwindows.dll"),
        os.path.join(internal, "python310.dll"),
    ]
    missing = [p for p in critical if not os.path.exists(p)]
    if missing:
        _log("incomplete install detected; missing: " + "; ".join(missing))
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                "Genki Study's files are incomplete — an update may still be running. "
                "Wait a moment and try again. Nothing was damaged.",
                "Genki Study", 0x30)  # MB_ICONWARNING
        except Exception:
            pass
        return False
    return True


_log("starting")
if not _check_runtime():
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app import models as M
from app.data_store import DataStore
from app.engine import Progress
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme, set_titlebar_dark


def _log_error(exc_type, exc_value, exc_tb):
    """Append any unhandled exception to data\\state\\app.log (plus console)."""
    try:
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(msg, file=sys.stderr)
        with open(os.path.join(APP_DIR, "data", "state", "app.log"), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] UNHANDLED EXCEPTION\n{msg}\n")
    except Exception:
        pass


sys.excepthook = _log_error


def load_data():
    path = os.path.join(APP_DIR, "data", "genki-data.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Genki Study")
    app.setStyle("Fusion")
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    data = load_data()
    store = DataStore(os.path.join(APP_DIR, "data", "state", "progress.json"))
    progress = Progress(store)
    dark = bool(progress.data.get("darkMode"))

    window = MainWindow(data, progress)
    window.resize(1500, 950)
    if os.path.exists(ICON_PATH):
        window.setWindowIcon(QIcon(ICON_PATH))
    apply_theme(dark)
    set_titlebar_dark(window, dark)
    _log(f"window ready v{M.VERSION}")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
