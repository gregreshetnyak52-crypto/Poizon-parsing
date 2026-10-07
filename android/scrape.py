"""Scroll the Dewu app's product list on an Android emulator and read visible card text.

The app makes its own signed requests; we only read what is rendered on screen
(no pinning/signature bypass). Selectors live in selectors.json and MUST be tuned
from `dump.py` output of your app version.

Usage: python android/scrape.py [--max 500] [--serial emulator-5554]
Open the target category/list screen in the app first.
"""
import argparse
import csv
import json
import random
import time
from pathlib import Path

import uiautomator2 as u2

SEL = json.loads((Path(__file__).parent / "selectors.json").read_text(encoding="utf-8"))


def read_cards(d):
    """Return list of dicts for cards currently on screen."""
    cards = []
    for card in d(**SEL["card"]):
        info = {}
        for field, sel in SEL["fields"].items():
            el = card.child(**sel)
            info[field] = el.get_text() if el.exists else None
        if info.get("title"):
            cards.append(info)
    return cards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=500)
    ap.add_argument("--serial")
    ap.add_argument("--out", default="out/app_products")
    a = ap.parse_args()

    d = u2.connect(a.serial)
    Path("out").mkdir(exist_ok=True)
    seen, rows, stale = set(), [], 0
    while len(rows) < a.max and stale < 5:
        new = 0
        for c in read_cards(d):
            key = (c["title"], c.get("price"))
            if key not in seen:
                seen.add(key)
                rows.append(c)
                new += 1
        stale = stale + 1 if new == 0 else 0
        d.swipe_ext("up", scale=0.8)
        time.sleep(random.uniform(1.0, 2.5))  # polite pacing
    fields = list(SEL["fields"])
    with open(a.out + ".json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    with open(a.out + ".csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} products -> {a.out}.json/.csv")


if __name__ == "__main__":
    main()
