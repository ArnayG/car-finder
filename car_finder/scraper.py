"""Scrape cars.com search results.

cars.com sits behind Cloudflare, which blocks plain HTTP clients and headless
browsers. Pages are loaded in a visible Google Chrome window (via Playwright)
with a persistent profile, and we wait for the Cloudflare check to clear.
"""

import json
import time
from typing import Dict, Iterator, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from car_finder import config

CHALLENGE_TITLE = "just a moment"
BLOCKED_TITLE = "attention required"


def build_url(page: int) -> str:
    params = dict(config.SEARCH, page=page)
    return f"{config.RESULTS_URL}?{urlencode(params)}"


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
            raise RuntimeError(f"Stuck on Cloudflare challenge at {url}")
        page.wait_for_timeout(1000)
    if BLOCKED_TITLE in page.title().lower():
        raise RuntimeError("Blocked by Cloudflare; wait a while (or switch networks) and retry.")
    return page.content()


def scrape() -> Iterator[Dict]:
    """Yield every listing near Stanford, page by page."""
    seen = set()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            config.BROWSER_PROFILE_DIR, headless=False, channel="chrome"
        )
        page = ctx.new_page()
        for page_num in range(1, config.MAX_PAGES + 1):
            listings = parse_listings(load(page, build_url(page_num)))
            new = [l for l in listings if l.get("listingId") not in seen]
            if not new:
                break
            seen.update(l.get("listingId") for l in new)
            print(f"page {page_num}: {len(new)} listings ({len(seen)} total)")
            yield from new
            time.sleep(config.REQUEST_DELAY_SECONDS)
        ctx.close()
