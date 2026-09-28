"""Carfax source.

Carfax's search page loads its listings from a JSON endpoint, which we call
directly. No browser needed, and each listing includes Carfax history info.
"""

import random
import time
from typing import Dict, Iterator

import requests

from car_finder import config
from car_finder.sources import BlockedError, PageCache

NAME = "carfax"
LABEL = "Carfax"
API_URL = "https://helix.carfax.com/search/v2/vehicles"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def normalize(raw: Dict) -> Dict:
    dealer = raw.get("dealer") or {}
    photo = ((raw.get("images") or {}).get("firstPhoto") or {}).get("large")
    history = [(raw.get("accidentHistory") or {}).get("text")]
    if raw.get("serviceRecords"):
        history.append("Service records available")
    return {
        "id": f"{NAME}:{raw['id']}",
        "vin": raw.get("vin"),
        "year": raw.get("year"),
        "make": raw.get("make"),
        "model": raw.get("model"),
        "trim": raw.get("trim") if raw.get("trim") != "Unspecified" else None,
        "price": raw.get("currentPrice") or raw.get("listPrice"),
        "mileage": raw.get("mileage"),
        "body": raw.get("bodytype"),
        "drivetrain": raw.get("drivetype"),
        "transmission": raw.get("transmission"),
        "fuel": raw.get("fuel"),
        "condition": (raw.get("vehicleCondition") or "").title() or None,
        "color": raw.get("exteriorColor"),
        "history": "; ".join(h for h in history if h) or None,
        "dealer": dealer.get("name"),
        "dealer_zip": dealer.get("zip"),
        "photo": photo,
        "links": {LABEL: raw.get("vdpUrl")},
    }


def fetch_pages(searches: Dict[str, Dict]) -> Iterator[tuple]:
    """Yield (category, page_num, raw listings) page by page."""
    session = requests.Session()
    session.headers.update(HEADERS)
    for category, search in searches.items():
        cache = PageCache(NAME, category)
        for page_num in range(1, config.MAX_PAGES + 1):
            listings, last = cache.get(page_num), False
            if listings is None:
                params = {
                    "zip": config.ZIP,
                    "radius": config.RADIUS_MILES,
                    "sort": "BEST",
                    "rows": 24,
                    "page": page_num,
                    **search,
                }
                resp = session.get(API_URL, params=params, timeout=30)
                if resp.status_code in (403, 429):
                    raise BlockedError(f"{LABEL}: HTTP {resp.status_code}")
                if resp.status_code == 400:  # past Carfax's page limit
                    break
                resp.raise_for_status()
                data = resp.json()
                listings = data.get("listings") or []
                last = page_num >= (data.get("totalPageCount") or 0)
                cache.put(page_num, listings)
                time.sleep(random.uniform(*config.DELAY_SECONDS[NAME]))
            if listings:
                yield category, page_num, listings
            if not listings or last:
                break
