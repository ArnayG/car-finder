"""cars.com source.

cars.com sits behind Cloudflare, which blocks plain HTTP clients and headless
browsers. Pages are loaded in a visible Google Chrome window (via Playwright)
with a persistent profile, and we wait for the Cloudflare check to clear.
"""

import json
import random
import time
from typing import Dict, Iterator, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from car_finder import config
from car_finder.sources import BlockedError, PageCache

NAME = "cars_com"
LABEL = "cars.com"
RESULTS_URL = "https://www.cars.com/shopping/results/"
LISTING_URL = "https://www.cars.com/vehicledetail/{listing_id}/"

CHALLENGE_TITLE = "just a moment"
BLOCKED_TITLE = "attention required"


def build_url(search: Dict, page: int) -> str:
    params = {
        "zip": config.STANFORD_ZIP,
        "maximum_distance": config.RADIUS_MILES,
        "sort": "best_match_desc",
        **search,
        "page": page,
    }
    return f"{RESULTS_URL}?{urlencode(params, doseq=True)}"


def parse_listings(html: str) -> List[Dict]:
    """Extract raw listing dicts from a results page."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for card in soup.select("[data-vehicle-details]"):
        try:
            listings.append(json.loads(card["data-vehicle-details"]))
        except (KeyError, json.JSONDecodeError):
            continue
    return listings


def normalize(raw: Dict) -> Dict:
    seller = raw.get("seller") or {}
    return {
        "id": f"{NAME}:{raw['listingId']}",
        "vin": raw.get("vin"),
        "year": raw.get("year"),
        "make": raw.get("make"),
        "model": raw.get("model"),
        "trim": raw.get("trim"),
        "price": raw.get("price"),
        "mileage": raw.get("mileage"),
        "body": raw.get("bodyStyle"),
        "drivetrain": raw.get("drivetrain"),
        "transmission": None,
        "fuel": raw.get("fuelType"),
        "condition": raw.get("stockType"),
        "color": raw.get("exteriorColor"),
        "history": None,
        "dealer": seller.get("dealerName"),
        "dealer_zip": seller.get("zip"),
        "photo": raw.get("primaryThumbnail"),
        "links": {LABEL: LISTING_URL.format(listing_id=raw["listingId"])},
    }


def load(page: Page, url: str, timeout_s: float = 90) -> str:
    """Navigate to url and wait out any Cloudflare challenge."""
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    deadline = time.time() + timeout_s
    warned = False
    while CHALLENGE_TITLE in page.title().lower():
        if not warned:
            print("  Waiting on Cloudflare check; complete it in the Chrome window if prompted.")
            warned = True
        if time.time() > deadline:
            raise BlockedError(f"{LABEL}: stuck on Cloudflare challenge")
        page.wait_for_timeout(1000)
    if BLOCKED_TITLE in page.title().lower():
        raise BlockedError(f"{LABEL}: blocked by Cloudflare")
    return page.content()


def fetch_pages(searches: Dict[str, Dict]) -> Iterator[tuple]:
    """Yield (category, raw listings) page by page for each category's search."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            config.BROWSER_PROFILE_DIR, headless=False, channel="chrome"
        )
        page = ctx.new_page()
        try:
            for category, search in searches.items():
                cache = PageCache(NAME, category)
                for page_num in range(1, config.MAX_PAGES + 1):
                    listings = cache.get(page_num)
                    if listings is None:
                        listings = parse_listings(load(page, build_url(search, page_num)))
                        cache.put(page_num, listings)
                        time.sleep(random.uniform(*config.DELAY_SECONDS[NAME]))
                    if not listings:
                        break
                    yield category, page_num, listings
        finally:
            ctx.close()
