# Genki Study (desktop)

Offline companion to the Pagelove web app. Same Genki I/II content (30 textbook +
10 expanded vocab per lesson, 30 grammar points per lesson), star-based mastery,
XP and streaks.

## Run

    run.bat        (or: python app\main.py)

## Layout

    app\main.py        entry point (PySide6, Fusion style)
    app\models.py      constants: star delays, SRS boxes, defaults
    app\data_store.py  JSON persistence with atomic saves + backups
    app\engine.py      XP / streak / stars / SRS logic
    app\quiz.py        quiz_vocab(lesson) and quiz_grammar(lesson) builders
    app\ui\            main window, dashboard, lesson page, quiz widget, settings
    data\genki-data.json   bundled content (regenerate from the web project's
                            tools/convert.mjs; keeps one source of truth)
    data\state\        progress.json + backups

Progress starts fresh in data\state\progress.json.
