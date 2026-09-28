import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from car_finder.filters import matches
from car_finder.scraper import scrape

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Find cars for sale near Stanford.")
    parser.parse_args()

    listings = list(scrape())
    df = pd.json_normalize(listings)
    matched = df[[matches(row) for row in listings]] if listings else df

    DATA_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    df.to_csv(DATA_DIR / f"all-{stamp}.csv", index=False)
    matched.to_csv(DATA_DIR / f"matches-{stamp}.csv", index=False)
    print(f"Scraped {len(df)} listings, {len(matched)} match your criteria.")


if __name__ == "__main__":
    main()
