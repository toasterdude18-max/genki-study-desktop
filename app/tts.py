"""Offline Japanese text-to-speech via Windows SAPI (pyttsx3).

Speak requests are queued onto a single worker thread so the UI never blocks;
a new request replaces any still-queued backlog. If no Japanese voice is
installed everything degrades to silence, and any failure is logged to
data\\state\\app.log.
"""
import os
import queue
import threading
from datetime import datetime

import pyttsx3

_engine = None
_ja_voice = None
_checked = False
_lock = threading.Lock()
_queue = queue.Queue()
_worker_started = False


def _log(msg):
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(app_dir, "data", "state", "app.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] TTS {msg}\n")
    except Exception:
        pass


def _init():
    global _engine, _ja_voice, _checked
    with _lock:
        if _checked:
            return
        _checked = True
        try:
            _engine = pyttsx3.init()
            for v in _engine.getProperty("voices"):
                blob = f"{v.name}|{v.id}".lower()
                if "ja" in blob or "japanese" in blob or "haruka" in blob:
                    _ja_voice = v.id
                    break
            if _ja_voice:
                _engine.setProperty("voice", _ja_voice)
                _log(f"voice found: {_ja_voice}")
            else:
                _log("no Japanese voice found")
        except Exception as e:
            _engine = None
            _ja_voice = None
            _log(f"init failed: {e!r}")


def _start_worker():
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True
    threading.Thread(target=_worker, daemon=True).start()
    _log("worker started")


def _worker():
    while True:
        text = _queue.get()
        if text is None:
            return
        try:
            _engine.say(text)
            _engine.runAndWait()
        except Exception as e:
            _log(f"speak failed: {e!r}")


def has_ja_voice():
    _init()
    return _ja_voice is not None


def speak(text):
    """Queue Japanese text to be read aloud. Silent no-op without a voice."""
    _init()
    if not _engine or not _ja_voice or not text:
        return
    _start_worker()
    # drop the backlog: only the most recent request matters
    while not _queue.empty():
        try:
            _queue.get_nowait()
        except queue.Empty:
            break
    _queue.put(text)


def stop():
    """Interrupt anything currently being spoken (used by the mute toggle)."""
    _init()
    if not _engine:
        return
    try:
        _engine.stop()
    except Exception:
        pass
