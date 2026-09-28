"""Search settings for the cars.com scrape."""

STANFORD_ZIP = "94305"

SEARCH = {
    "zip": STANFORD_ZIP,
    "maximum_distance": 50,  # miles
    "stock_type": "all",  # "new", "used", "cpo", or "all"
    "sort": "best_match_desc",
}

MAX_PAGES = 500  # cars.com serves 24 listings per page
REQUEST_DELAY_SECONDS = 3.0

RESULTS_URL = "https://www.cars.com/shopping/results/"

# Persistent browser profile so Cloudflare clearance cookies survive between runs.
BROWSER_PROFILE_DIR = ".browser-profile"
