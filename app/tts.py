"""Offline Japanese text-to-speech via Windows SAPI (pyttsx3).

Everything runs on the main thread: speak() replaces the current phrase and
returns immediately (SAPI speaks asynchronously), stop() cuts audio instantly.
Because no other thread ever touches the engine, the COM state cannot break.
Failures log to data\\state\\app.log and the engine self-heals on the next call.
"""
import os
import sys
from datetime import datetime

import pyttsx3

_engine = None
_ja_voice = None
_checked = False


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _log(msg):
    try:
        path = os.path.join(_app_dir(), "data", "state", "app.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] TTS {msg}\n")
    except Exception:
        pass


def _reset():
    global _engine, _ja_voice, _checked
    _engine = None
    _ja_voice = None
    _checked = False


def _init():
    global _engine, _ja_voice, _checked
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
        _reset()
        _log(f"init failed: {e!r}")


def has_ja_voice():
    _init()
    return _ja_voice is not None


def speak(text):
    """Speak now, replacing anything currently playing. Returns immediately."""
    _init()
    if not _engine or not _ja_voice or not text:
        return
    try:
        _engine.stop()          # cut the current phrase (instant)
        _engine.say(text)       # async SAPI speak; audio continues on its own
    except Exception as e:
        _log(f"speak failed: {e!r}")
        _reset()                # self-heal: recreate the engine on the next call


def stop():
    """Cut audio instantly (mute / quit / finish)."""
    _init()
    if not _engine:
        return
    try:
        _engine.stop()
    except Exception as e:
        _log(f"stop failed: {e!r}")
        _reset()
