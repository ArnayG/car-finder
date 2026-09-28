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
            v = verdicts.get(f"{category}:{l['id']}")
            if not v:
                continue
            rows.append({
                "category": category,
                "title": " ".join(str(x) for x in (l["year"], l["make"], l["model"], l["trim"]) if x),
                "price": _int(l["price"]),
                "mileage": _int(l["mileage"]),
                "condition": l["condition"],
                "body": l["body"],
                "drivetrain": l["drivetrain"],
                "history": l["history"],
                "dealer": l["dealer"],
                "zip": l["dealer_zip"],
                "photo": l["photo"],
                "links": l["links"],
                "fits": v["fits"],
                "score": v["score"],
                "reason": v["reason"],
            })
    return rows


def _int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def write_report(scraped: Dict[str, List[Dict]], verdicts: Dict[str, Dict], sources: Dict[str, str]) -> Path:
    data = {
        "sources": sources,
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
