"""Use Claude to decide which listings fit each buying category.

Runs through the Claude Code CLI in headless mode (`claude -p`), so it uses your
Claude Code login instead of an API key.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from car_finder import config

BATCH_SIZE = 40
CACHE_FILE = Path(config.DATA_DIR) / "classifications.json"

SYSTEM = (
    "You are an experienced car buyer and enthusiast helping a Stanford student shop "
    "for cars listed on cars.com near Palo Alto, CA. For each listing you are given, "
    "decide whether it fits the shopper's category, score how appealing it is within "
    "that category from 1 (poor) to 10 (excellent), and give a one or two sentence "
    "reason a buyer would find useful (what makes it interesting or a good buy, or why "
    "it doesn't fit). Judge from the year, make, model, trim, price, and mileage."
)


SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "listing_id": {"type": "string"},
                    "fits": {"type": "boolean"},
                    "score": {"type": "integer", "minimum": 1, "maximum": 10},
                    "reason": {"type": "string"},
                },
                "required": ["listing_id", "fits", "score", "reason"],
            },
        }
    },
    "required": ["verdicts"],
}


def _num(value) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def in_range(value: Optional[int], bounds) -> bool:
    lo, hi = bounds
    if value is None:
        return lo is None and hi is None
    return (lo is None or value >= lo) and (hi is None or value <= hi)


def prefilter(category: str, listings: List[Dict]) -> List[Dict]:
    """Hard price/year checks, in case the site's filters are loose."""
    cat = config.CATEGORIES[category]
    return [
        l for l in listings
        if in_range(_num(l.get("price")), cat["price"])
        and in_range(_num(l.get("year")), cat["year"])
    ]


def summarize(listing: Dict) -> Dict:
    return {
        "listing_id": listing["listingId"],
        "year": listing.get("year"),
        "make": listing.get("make"),
        "model": listing.get("model"),
        "trim": listing.get("trim"),
        "price": listing.get("price"),
        "mileage": listing.get("mileage"),
        "body_style": listing.get("bodyStyle"),
        "drivetrain": listing.get("drivetrain"),
        "fuel": listing.get("fuelType"),
        "condition": listing.get("stockType"),
        "color": listing.get("exteriorColor"),
    }


def classify_batch(category: str, batch: List[Dict]) -> List[Dict]:
    criteria = config.CATEGORIES[category]["criteria"]
    prompt = (
        f"Category: {config.CATEGORIES[category]['label']}\n"
        f"What the shopper wants: {criteria}\n\n"
        f"Return one verdict per listing, using its listing_id.\n\n"
        f"Listings:\n{json.dumps([summarize(l) for l in batch], indent=1)}"
    )
    proc = subprocess.run(
        [
            "claude", "-p",
            "--model", config.CLAUDE_MODEL,
            "--effort", "low",
            "--tools", "",
            "--no-session-persistence",
            "--system-prompt", SYSTEM,
            "--output-format", "json",
            "--json-schema", json.dumps(SCHEMA),
        ],
        input=prompt, capture_output=True, text=True, timeout=600,
    )
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result = {}
    verdicts = (result.get("structured_output") or {}).get("verdicts")
    if result.get("is_error") or verdicts is None:
        detail = result.get("result") or proc.stderr.strip() or proc.stdout.strip()
        print(f"  [{category}] batch skipped: {detail[:200]}")
        return []
    return verdicts


def load_cache() -> Dict[str, Dict]:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def classify(scraped: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """Classify every listing not already in the cache. Returns the full cache,
    keyed by "<category>:<listingId>"."""
    if not shutil.which("claude"):
        raise SystemExit("The Claude Code CLI (`claude`) must be installed and logged in.")
    cache = load_cache()
    for category, listings in scraped.items():
        todo = [
            l for l in prefilter(category, listings)
            if f"{category}:{l['listingId']}" not in cache
        ]
        print(f"  [{category}] {len(todo)} new listings to classify")
        for i in range(0, len(todo), BATCH_SIZE):
            for v in classify_batch(category, todo[i:i + BATCH_SIZE]):
                cache[f"{category}:{v['listing_id']}"] = v
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps(cache, indent=1))
    return cache
