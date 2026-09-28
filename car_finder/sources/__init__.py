"""Listing sources and the shared page cache.

Every fetched page is cached under data/pages/<date>/<zip>-<radius>mi/<source>/<category>/, so
an interrupted or blocked run resumes where it stopped instead of refetching.
"""

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from car_finder import config


class BlockedError(RuntimeError):
    pass


class PageCache:
    def __init__(self, source: str, category: str):
        location = f"{config.ZIP}-{config.RADIUS_MILES}mi"
        self.dir = Path(config.DATA_DIR) / "pages" / date.today().isoformat() / location / source / category
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, page: int) -> Path:
        return self.dir / f"{page:03d}.json"

    def get(self, page: int) -> Optional[List[Dict]]:
        path = self._path(page)
        return json.loads(path.read_text()) if path.exists() else None

    def put(self, page: int, listings: List[Dict]) -> None:
        self._path(page).write_text(json.dumps(listings))
