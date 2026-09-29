"""JSON persistence with atomic writes and rolling backups."""
import json
import os
import shutil
import tempfile
from datetime import datetime


class DataStore:
    """State lives in one JSON file; saves are atomic (temp + replace) and the
    previous file is copied to backups/ before each overwrite."""

    def __init__(self, path):
        self.path = path
        self.backup_dir = os.path.join(os.path.dirname(path), "backups")

    def load(self, default=None):
        default = default or {}
        if not os.path.exists(self.path):
            return dict(default)
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return dict(default)
        merged = dict(default)
        merged.update(data)
        return merged

    def save(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        if os.path.exists(self.path):
            os.makedirs(self.backup_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            try:
                shutil.copy2(self.path, os.path.join(self.backup_dir, f"progress-{stamp}.json"))
            except OSError:
                pass
        os.replace(tmp, self.path)

    def export_json(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()

    def import_json(self, text):
        data = json.loads(text)  # raises on malformed input
        self.save(data)
        return data
