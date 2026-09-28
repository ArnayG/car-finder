"""Scrape every source, falling back gracefully when one is blocked."""

from typing import Dict, List, Tuple

from car_finder import config
from car_finder.sources import BlockedError, carfax, cars_com

SOURCES = [carfax, cars_com]


def merge(listings: List[Dict]) -> List[Dict]:
    """Dedupe the same car listed on multiple sites (by VIN), keeping every link."""
    by_key: Dict[str, Dict] = {}
    for l in listings:
        key = l.get("vin") or l["id"]
        if key in by_key:
            kept = by_key[key]
            kept["links"].update(l["links"])
            for field, value in l.items():
                if kept.get(field) in (None, "") and value not in (None, ""):
                    kept[field] = value
        else:
            by_key[key] = dict(l, links=dict(l["links"]))
    return list(by_key.values())


def scrape(categories: List[str]) -> Tuple[Dict[str, List[Dict]], Dict[str, str]]:
    """Returns ({category: merged listings}, {source: status}).
    Raises only if every source fails."""
    collected: Dict[str, List[Dict]] = {c: [] for c in categories}
    status = {}
    for source in SOURCES:
        searches = {c: config.CATEGORIES[c][source.NAME] for c in categories}
        count = 0
        try:
            for category, page_num, raw in source.fetch_pages(searches):
                collected[category].extend(source.normalize(r) for r in raw)
                count += len(raw)
                print(f"  [{source.LABEL}/{category}] page {page_num}: {len(raw)} listings")
            status[source.LABEL] = f"ok ({count} listings)"
        except BlockedError as e:
            status[source.LABEL] = f"blocked after {count} listings ({e}); continuing with other sources"
        except Exception as e:  # network errors, site changes, etc.
            status[source.LABEL] = f"failed after {count} listings ({type(e).__name__}: {e})"
        print(f"{source.LABEL}: {status[source.LABEL]}")
    if not any(collected.values()):
        raise BlockedError("Every source failed. Progress is saved; wait a while (or switch networks) and rerun.")
    return {c: merge(ls) for c, ls in collected.items()}, status
