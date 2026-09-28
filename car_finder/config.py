"""Search settings for the cars.com scrape."""

STANFORD_ZIP = "94305"

SEARCH = {
    "zip": STANFORD_ZIP,
    "maximum_distance": 50,  # miles
    "stock_type": "all",  # "new", "used", "cpo", or "all"
    "page_size": 100,
    "sort": "best_match_desc",
}

MAX_PAGES = 50
REQUEST_DELAY_SECONDS = 3.0

RESULTS_URL = "https://www.cars.com/shopping/results/"
