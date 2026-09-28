# car-finder

Scrapes cars.com for cars for sale near Stanford (ZIP 94305) and filters them down to ones worth buying.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m car_finder
```

This opens a Google Chrome window (Chrome must be installed). cars.com is behind Cloudflare, which blocks headless browsers and plain HTTP requests, so the scraper drives a visible Chrome with a persistent profile in `.browser-profile/`. cars.com serves 24 listings per page; a full 50-mile scrape is roughly 400 pages and takes about 25 minutes.

Results are written to `data/` as `all-<timestamp>.csv` and `matches-<timestamp>.csv`.

## Layout

- `car_finder/config.py` — search location, radius, paging
- `car_finder/scraper.py` — loads result pages in Playwright and parses listings
- `car_finder/filters.py` — buying criteria (`matches(listing)`)
