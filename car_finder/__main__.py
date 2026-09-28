import argparse
import json
import sys
import webbrowser
from datetime import date
from pathlib import Path

from car_finder import config
from car_finder.classify import classify, load_cache
from car_finder.report import write_report
from car_finder.scraper import BlockedError, scrape

SCRAPED_FILE = Path(config.DATA_DIR) / "listings.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Find cars for sale near Stanford.")
    parser.add_argument(
        "step", nargs="?", default="all", choices=["all", "scrape", "classify", "report"],
        help="run one step, or all of them (default)",
    )
    parser.add_argument(
        "--category", action="append", choices=list(config.CATEGORIES),
        help="limit to a category (repeatable)",
    )
    args = parser.parse_args()
    categories = args.category or list(config.CATEGORIES)

    if args.step in ("all", "scrape"):
        print(f"Scraping cars.com ({date.today()})...")
        try:
            scraped = scrape(categories)
        except BlockedError as e:
            sys.exit(str(e))
        previous = json.loads(SCRAPED_FILE.read_text()) if SCRAPED_FILE.exists() else {}
        SCRAPED_FILE.parent.mkdir(parents=True, exist_ok=True)
        SCRAPED_FILE.write_text(json.dumps({**previous, **scraped}))
    scraped = json.loads(SCRAPED_FILE.read_text())

    if args.step in ("all", "classify"):
        print("Classifying with Claude...")
        verdicts = classify({k: v for k, v in scraped.items() if k in categories})
    else:
        verdicts = load_cache()

    out = write_report(scraped, verdicts)
    matches = sum(1 for v in verdicts.values() if v["fits"])
    print(f"{matches} matches. Report: {out.resolve()}")
    webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
