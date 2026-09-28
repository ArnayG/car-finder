# car-finder

Scrapes cars.com for cars for sale within 50 miles of Stanford (ZIP 94305), uses Claude to pick the ones worth buying, and shows them in a clickable HTML page.

## Categories

| Category | Search on cars.com | Claude decides |
|---|---|---|
| Fun budget | used, under $15k, 1989 or older | Is it interesting or does it have pedigree? |
| Fun expensive | over $70k | Is it sporty, or really interesting for the price? |
| Daily driver | $30–50k, SUV or sedan, under 40k miles | Is it a low-mileage SUV or 4-door sedan that makes a good daily driver? |

Categories, search filters, and the criteria Claude judges against live in `car_finder/config.py`.

## Setup

Requires Python 3.10+ and Google Chrome.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
python -m car_finder                              # scrape, classify, open the report
python -m car_finder scrape                       # just scrape
python -m car_finder classify                     # classify already-scraped listings
python -m car_finder report                       # rebuild the report
python -m car_finder --category fun_budget        # limit to one category (repeatable)
```

The report is written to `data/report.html` and opened in your browser. Each card links to the cars.com listing.

## Not getting blocked

cars.com is behind Cloudflare, which blocks plain HTTP requests and headless browsers. The scraper:

- drives a visible Google Chrome window with a persistent profile (`.browser-profile/`), and waits for Cloudflare's "Just a moment…" check (complete it in the window if prompted)
- runs a narrow search per category so the site does the coarse filtering and far fewer pages are fetched
- waits a random 8–15 seconds between page loads
- caches every fetched page under `data/pages/<date>/`, so if it does get blocked, rerunning later resumes where it stopped

If you see "Blocked by Cloudflare", wait a few hours or switch networks and rerun.

## Cost

Claude classifications are cached in `data/classifications.json`, so reruns only pay for new listings. Listings are sent in batches of 40 to `claude-opus-5` at low effort.
