"""Application configuration (paths, env)."""

from __future__ import annotations

import os
from pathlib import Path

# Project base directory (week2/), parent of app/
BASE_DIR = Path(__file__).resolve().parents[1]
# Data directory for SQLite DB; override with WEEK2_DATA_DIR env if needed
DATA_DIR = Path(os.getenv("WEEK2_DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "app.db"
