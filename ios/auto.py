"""Automatic crawl on iPhone: from an open product LIST screen (category/search/brand),
open every product, scrape title + per-size prices + size chart, go back, scroll, repeat.

Results are appended to out/products.jsonl as they are scraped; re-running resumes
(already-seen products are skipped). Nothing is selected or purchased.

Usage: python ios/auto.py --udid <UDID> [--max 200] [--break-every 30]
"""
import argparse
import json
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape_item_ios import Screen, connect, scrape_current  # noqa: E402

PRICE = re.compile(r"^[¥￥]\s*\d+(?:\.\d+)?$")


def list_cards(xml_source):
    """Find product cards on a list screen: each visible ¥price text and the card's texts.
    Returns [(key, x, y)] where (x, y) is a safe tap point (the price text centre)."""
    root = ET.fromstring(xml_source)
    parent = {c: p for p in root.iter() for c in p}
    cards = []
    for n in root.iter("XCUIElementTypeStaticText"):
        label = n.get("label") or n.get("value") or ""
        if not PRICE.match(label.strip()) or n.get("visible") == "false":
            continue
        # nearest ancestor that holds a small, card-sized group of texts
        card = n
        for _ in range(4):
            if card in parent:
                card = parent[card]
            texts = [t.get("label") for t in card.iter("XCUIElementTypeStaticText") if t.get("label")]
            if len(texts) >= 2:
                break
        texts = [t.get("label") for t in card.iter("XCUIElementTypeStaticText") if t.get("label")]
        if len(texts) > 8:  # climbed into the whole list: fall back to the price alone
            texts = [label]
        try:
            x = int(n.get("x")) + int(n.get("width")) // 2
            y = int(n.get("y")) + int(n.get("height")) // 2
        except (TypeError, ValueError):
            continue
        cards.append(("|".join(texts), x, y))
    return cards


def go_back(s):
    # iOS edge-swipe back gesture
    s.d.execute_script("mobile: dragFromToForDuration", {
        "fromX": 3, "fromY": s.h // 2, "toX": int(s.w * 0.8), "toY": s.h // 2, "duration": 0.3})
    time.sleep(random.uniform(1.2, 2.2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--udid", required=True)
    ap.add_argument("--bundle-id", default="com.siwuai.duapp")
    ap.add_argument("--team-id")
    ap.add_argument("--wda-bundle-id")
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--break-every", type=int, default=30)
    ap.add_argument("--out", default="out/products.jsonl")
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(exist_ok=True)
    seen = set()
    if out.exists():
        seen = {json.loads(l)["key"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    done = 0
    drv = connect(a.udid, a.bundle_id, team_id=a.team_id, wda_bundle_id=a.wda_bundle_id)
    try:
        s = Screen(drv)
        stale = 0
        while done < a.max and stale < 4:
            fresh = [c for c in list_cards(drv.page_source) if c[0] not in seen]
            if not fresh:
                stale += 1
                s.swipe_up()
                time.sleep(random.uniform(1.0, 2.0))
                continue
            stale = 0
            key, x, y = fresh[0]
            drv.execute_script("mobile: tap", {"x": x, "y": y})
            time.sleep(random.uniform(2.0, 3.5))
            item = scrape_current(s)
            item["key"] = key
            go_back(s)
            if not list_cards(drv.page_source):  # lost the list screen: stop rather than wander
                print("list screen not found after going back; stopping")
                break
            seen.add(key)
            if item.get("sizes") or item.get("title"):
                with out.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
                done += 1
                print(f"[{done}] {item.get('title')}")
            if a.break_every and done and done % a.break_every == 0:
                time.sleep(random.uniform(30, 90))
    finally:
        drv.quit()
    print(f"done: {done} products -> {out}")


if __name__ == "__main__":
    main()
