"""Scrape cars.com search results.

cars.com sits behind Cloudflare, which blocks plain HTTP clients and headless
browsers. Pages are loaded in a visible Google Chrome window (via Playwright)
with a persistent profile, and we wait for the Cloudflare check to clear.

To avoid getting blocked, each category runs its own narrow search, page loads
are spaced out with a randomized delay, and every fetched page is cached to
disk so an interrupted run resumes where it stopped instead of refetching.
"""

import json
import random
import time
from datetime import date
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from car_finder import config

CHALLENGE_TITLE = "just a moment"
BLOCKED_TITLE = "attention required"


class BlockedError(RuntimeError):
    pass


def build_url(search: Dict, page: int) -> str:
    params = {
        "zip": config.STANFORD_ZIP,
        "maximum_distance": config.RADIUS_MILES,
        "sort": "best_match_desc",
        **search,
        "page": page,
    }
    return f"{config.RESULTS_URL}?{urlencode(params, doseq=True)}"


def parse_listings(html: str) -> List[Dict]:
    """Extract listing dicts from a results page."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for card in soup.select("[data-vehicle-details]"):
        try:
            details = json.loads(card["data-vehicle-details"])
        except (KeyError, json.JSONDecodeError):
            continue
        listings.append(details)
    return listings


def load(page: Page, url: str, timeout_s: float = 90) -> str:
    """Navigate to url and wait out any Cloudflare challenge."""
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    deadline = time.time() + timeout_s
    warned = False
    while CHALLENGE_TITLE in page.title().lower():
        if not warned:
            print("Waiting on Cloudflare check; complete it in the Chrome window if prompted.")
            warned = True
        if time.time() > deadline:
            raise BlockedError(f"Stuck on Cloudflare challenge at {url}")
        page.wait_for_timeout(1000)
    if BLOCKED_TITLE in page.title().lower():
        raise BlockedError("Blocked by Cloudflare. Progress is saved; wait a while (or switch networks) and rerun.")
    return page.content()


def cache_dir(category: str) -> Path:
    return Path(config.DATA_DIR) / "pages" / date.today().isoformat() / category


def scrape_category(page: Page, category: str) -> List[Dict]:
    search = config.CATEGORIES[category]["search"]
    cdir = cache_dir(category)
    cdir.mkdir(parents=True, exist_ok=True)
    seen, results = set(), []
    for page_num in range(1, config.MAX_PAGES + 1):
        cached = cdir / f"{page_num:03d}.json"
        if cached.exists():
            listings = json.loads(cached.read_text())
        else:
            listings = parse_listings(load(page, build_url(search, page_num)))
            cached.write_text(json.dumps(listings))
            time.sleep(random.uniform(*config.DELAY_SECONDS))
        new = [l for l in listings if l.get("listingId") not in seen]
        if not new:
            break
        seen.update(l["listingId"] for l in new)
        results.extend(new)
        print(f"  [{category}] page {page_num}: {len(new)} listings ({len(results)} total)")
    return results


def scrape(categories: List[str]) -> Dict[str, List[Dict]]:
    """Scrape each category's search. Returns {category: listings}."""
    out = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            config.BROWSER_PROFILE_DIR, headless=False, channel="chrome"
        )
        page = ctx.new_page()
        try:
            for category in categories:
                out[category] = scrape_category(page, category)
        finally:
            ctx.close()
    return out
