"""Offline Japanese text-to-speech via Windows SAPI (pyttsx3).

Speak requests are queued onto a single worker thread so the UI never blocks.
If no Japanese voice is installed everything degrades to silence.
"""
import queue
import threading

import pyttsx3

_engine = None
_ja_voice = None
_checked = False
_lock = threading.Lock()
_queue = queue.Queue()


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
        except Exception:
            _engine = None
            _ja_voice = None


def _worker():
    while True:
        text = _queue.get()
        if text is None:
            return
        try:
            _engine.say(text)
            _engine.runAndWait()
        except Exception:
            pass


def has_ja_voice():
    _init()
    return _ja_voice is not None


def speak(text):
    """Queue Japanese text to be read aloud. Silent no-op without a voice."""
    _init()
    if not _engine or not _ja_voice or not text:
        return
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
