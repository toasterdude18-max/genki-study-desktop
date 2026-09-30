"""Domain constants for the Genki study app."""

VERSION = "1.1.0"

LESSON_COUNT = 23

# Word-owned stars: each word collects yellow stars for correct answers
# (reset to zero on a miss); 3 yellows convert into one green star.
# At most one green can be earned per word per day; greens are permanent.
YELLOW_MAX = 3
GREEN_PER_DAY = 1

DEFAULT_PROGRESS = {
    "xp": 0,
    "streak": 0,
    "lastStudied": None,
    "dailyXp": {},          # "YYYY-MM-DD" -> xp
    "dailyGoal": 50,
    "freePractice": True,
    "soundOn": True,        # auto-speak Japanese stimuli by default
    "darkMode": False,      # dark theme toggle (top-right of the top bar)
    "words": {},            # vocabId -> {yellow, green, lastGreen, right, wrong, seen}
    "stars": {},            # legacy activity tracks (unused since word-owned stars)
}

# Non-textbook (expanded edition) content is tinted violet, matching the web app.
COLOR_EXTRA = "#7c3aed"
COLOR_EXTRA_BG = "#f5f3ff"
