"""Search settings and buying categories."""

STANFORD_ZIP = "94305"
RADIUS_MILES = 50

MAX_PAGES = 200  # per category per source; both sites serve 24 listings per page

# Randomized pause between page loads, to stay well under bot-detection radar.
DELAY_SECONDS = {
    "cars_com": (8, 15),  # Cloudflare-protected; go slow
    "carfax": (2, 5),
}

# Persistent browser profile so Cloudflare clearance cookies survive between runs.
BROWSER_PROFILE_DIR = ".browser-profile"
DATA_DIR = "data"

# Model alias passed to the Claude Code CLI (`claude -p --model ...`).
CLAUDE_MODEL = "opus"
CLASSIFY_WORKERS = 4  # concurrent Claude calls

# Each category runs its own search on each site (so the sites do the coarse
# filtering and we fetch far fewer pages), then a hard price/year check in
# code, then Claude judges fit against `criteria`.
CATEGORIES = {
    "fun_budget": {
        "label": "Fun budget",
        "cars_com": {"stock_type": "used", "list_price_max": 15000, "year_max": 1989},
        "carfax": {"priceMin": 1, "priceMax": 15000, "yearMax": 1989},
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
        "cars_com": {"stock_type": "all", "list_price_min": 70000},
        "carfax": {"priceMin": 70000},
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
        "cars_com": {
            "stock_type": "all",
            "list_price_min": 30000,
            "list_price_max": 50000,
            "body_style_slugs[]": ["suv", "sedan"],
            "mileage_max": 40000,
        },
        "carfax": {
            "priceMin": 30000,
            "priceMax": 50000,
            "mileageMax": 40000,
            "bodytypes": "SUV,Sedan",
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
