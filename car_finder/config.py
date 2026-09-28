"""Search settings and buying categories."""

STANFORD_ZIP = "94305"
RADIUS_MILES = 50

RESULTS_URL = "https://www.cars.com/shopping/results/"
LISTING_URL = "https://www.cars.com/vehicledetail/{listing_id}/"

MAX_PAGES = 200  # per category; cars.com serves 24 listings per page
# Randomized pause between page loads, to stay well under Cloudflare's radar.
DELAY_SECONDS = (8, 15)

# Persistent browser profile so Cloudflare clearance cookies survive between runs.
BROWSER_PROFILE_DIR = ".browser-profile"
DATA_DIR = "data"

# Model alias passed to the Claude Code CLI (`claude -p --model ...`).
CLAUDE_MODEL = "opus"

# Each category gets its own cars.com search (so the site does the coarse
# filtering and we fetch far fewer pages), a hard price/year check applied in
# code, and a description Claude uses to judge fit.
CATEGORIES = {
    "fun_budget": {
        "label": "Fun budget",
        "search": {
            "stock_type": "used",
            "list_price_max": 15000,
            "year_max": 1989,
        },
        "price": (None, 15000),
        "year": (None, 1989),
        "criteria": (
            "An older car (built before 1990) priced under $15,000 that is genuinely "
            "interesting or has pedigree: a classic, a collectible, a notable model or "
            "trim with motorsport or design history, or something with a real enthusiast "
            "following. Reject plain old economy cars or trucks with nothing special about them."
        ),
    },
    "fun_expensive": {
        "label": "Fun expensive",
        "search": {
            "stock_type": "all",
            "list_price_min": 70000,
        },
        "price": (70000, None),
        "year": (None, None),
        "criteria": (
            "A car priced above $70,000 that is sporty (sports car, performance variant, "
            "track-focused trim) or really interesting for what it costs (rare, exotic, "
            "historically significant, or an unusually strong value for the price). "
            "Reject generic luxury SUVs, luxury sedans without a performance angle, and "
            "pickup trucks."
        ),
    },
    "daily_driver": {
        "label": "Daily driver",
        "search": {
            "stock_type": "all",
            "list_price_min": 30000,
            "list_price_max": 50000,
            "body_style_slugs[]": ["suv", "sedan"],
            "mileage_max": 40000,
        },
        "price": (30000, 50000),
        "year": (None, None),
        "criteria": (
            "A normal daily driver priced $30,000-$50,000 that is an SUV or a 4-door sedan "
            "with low mileage (roughly under 30,000 miles; new is ideal). Favor reliable, "
            "practical, well-regarded models. Reject coupes, 2-doors, convertibles, "
            "trucks, and vans."
        ),
    },
}
