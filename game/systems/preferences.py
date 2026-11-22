"""Persistência dos dados locais do jogo."""

import json
import os
import tempfile
from pathlib import Path

DATA_DIR = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "ctrl-revolt"


def read_data(filename, default=None):
    try:
        return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_data(filename, value):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=DATA_DIR, delete=False
    )
    path = Path(temporary.name)
    try:
        with temporary:
            json.dump(value, temporary, ensure_ascii=False)
        path.replace(DATA_DIR / filename)
    finally:
        path.unlink(missing_ok=True)
