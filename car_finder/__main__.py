import argparse
import json
import sys
import webbrowser
from datetime import date
from pathlib import Path

from car_finder import config
from car_finder.classify import classify, load_cache
from car_finder.report import write_report
from car_finder.scraper import scrape
from car_finder.sources import BlockedError

SCRAPED_FILE = Path(config.DATA_DIR) / "listings.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Find cars for sale near you.")
    parser.add_argument(
        "step", nargs="?", default="all", choices=["all", "scrape", "classify", "report"],
        help="run one step, or all of them (default)",
    )
    parser.add_argument(
        "--category", action="append", choices=list(config.CATEGORIES),
        help="limit to a category (repeatable)",
    )
    parser.add_argument("--zip", default=config.ZIP, help=f"ZIP code to search around (default {config.ZIP})")
    parser.add_argument("--radius", type=int, default=config.RADIUS_MILES,
                        help=f"search radius in miles (default {config.RADIUS_MILES})")
    args = parser.parse_args()
    categories = args.category or list(config.CATEGORIES)
    config.ZIP, config.RADIUS_MILES = args.zip, args.radius
    location = f"{args.radius} miles of ZIP {args.zip}"

    saved = json.loads(SCRAPED_FILE.read_text()) if SCRAPED_FILE.exists() else {}
    if saved.get("location") != location and args.step in ("all", "scrape"):
        saved = {}  # new search area: don't mix in another city's listings
    saved.setdefault("listings", {})
    saved.setdefault("sources", {})
    location = saved.get("location", location)
    if args.step in ("all", "scrape"):
        print(f"Scraping ({date.today()})...")
        try:
            listings, status = scrape(categories)
        except BlockedError as e:
            sys.exit(str(e))
        saved = {"location": location, "listings": {**saved["listings"], **listings}, "sources": status}
        SCRAPED_FILE.parent.mkdir(parents=True, exist_ok=True)
        SCRAPED_FILE.write_text(json.dumps(saved))
    if not saved["listings"]:
        sys.exit("Nothing scraped yet. Run `python -m car_finder scrape` first.")

    if args.step in ("all", "classify"):
        out = write_report(saved["listings"], load_cache(), saved["sources"], location, live=True)
        print(f"Classifying with Claude... (the report in your browser updates as batches finish)")
        webbrowser.open(out.resolve().as_uri())
        verdicts = classify(
            {k: v for k, v in saved["listings"].items() if k in categories},
            on_progress=lambda cache: write_report(saved["listings"], cache, saved["sources"], location, live=True),
        )
    else:
        verdicts = load_cache()

    out = write_report(saved["listings"], verdicts, saved["sources"], location)
    matches = sum(
        1 for c, ls in saved["listings"].items() for l in ls
        if verdicts.get(f"{c}:{l['id']}", {}).get("fits")
    )
    print(f"{matches} matches. Report: {out.resolve()}")
    if args.step == "report":
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
