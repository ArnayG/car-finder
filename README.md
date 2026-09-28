# car-finder

Scrapes cars.com for cars for sale near Stanford (ZIP 94305) and filters them down to ones worth buying.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python -m car_finder            # opens a Chromium window
python -m car_finder --headless
```

Results are written to `data/` as `all-<timestamp>.csv` and `matches-<timestamp>.csv`.

## Layout

- `car_finder/config.py` — search location, radius, paging
- `car_finder/scraper.py` — loads result pages in Playwright and parses listings
- `car_finder/filters.py` — buying criteria (`matches(listing)`)
