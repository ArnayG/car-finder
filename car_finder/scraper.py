"""Scrape cars.com search results.

cars.com sits behind Cloudflare and rejects plain HTTP clients, so pages are
loaded with a real Chromium browser via Playwright.
"""

import json
import time
from typing import Dict, Iterator, List
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from car_finder import config


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


def scrape(headless: bool = False) -> Iterator[Dict]:
    """Yield every listing near Stanford, page by page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        for page_num in range(1, config.MAX_PAGES + 1):
            page.goto(build_url(page_num), wait_until="domcontentloaded")
            listings = parse_listings(page.content())
            if not listings:
                break
            yield from listings
            time.sleep(config.REQUEST_DELAY_SECONDS)
        browser.close()
