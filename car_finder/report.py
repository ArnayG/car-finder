"""Render classified listings as a standalone, clickable HTML page."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from car_finder import config

TEMPLATE = Path(__file__).with_name("report_template.html")


def build_rows(scraped: Dict[str, List[Dict]], verdicts: Dict[str, Dict]) -> List[Dict]:
    rows = []
    for category, listings in scraped.items():
        for l in listings:
            v = verdicts.get(f"{category}:{l['listingId']}")
            if not v:
                continue
            seller = l.get("seller") or {}
            rows.append({
                "category": category,
                "title": " ".join(str(x) for x in (l.get("year"), l.get("make"), l.get("model"), l.get("trim")) if x),
                "price": int(float(l["price"])) if l.get("price") else None,
                "mileage": int(float(l["mileage"])) if l.get("mileage") else None,
                "condition": l.get("stockType"),
                "body": l.get("bodyStyle"),
                "drivetrain": l.get("drivetrain"),
                "dealer": seller.get("dealerName"),
                "zip": seller.get("zip"),
                "photo": l.get("primaryThumbnail"),
                "url": config.LISTING_URL.format(listing_id=l["listingId"]),
                "fits": v["fits"],
                "score": v["score"],
                "reason": v["reason"],
            })
    return rows


def write_report(scraped: Dict[str, List[Dict]], verdicts: Dict[str, Dict]) -> Path:
    data = {
        "generated": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        "categories": {k: v["label"] for k, v in config.CATEGORIES.items()},
        "rows": build_rows(scraped, verdicts),
    }
    html = TEMPLATE.read_text().replace(
        "/*__DATA__*/null", json.dumps(data).replace("</", "<\\/")
    )
    out = Path(config.DATA_DIR) / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out
