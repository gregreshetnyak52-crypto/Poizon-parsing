"""Automatic crawl on Android: from an open product LIST screen (category/search/brand),
open every product, scrape title + per-size prices + size chart, go back, scroll, repeat.

Results are appended to out/products.jsonl; re-running resumes (seen products skipped).
Nothing is selected or purchased.

Usage: python android/auto.py [--serial ID] [--max 200] [--break-every 30]
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
from scrape_item import scrape_current  # noqa: E402

PRICE = re.compile(r"^[¥￥]\s*\d+(?:\.\d+)?$")
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def list_cards(xml_source):
    """Find product cards on a list screen by their ¥price text.
    Returns [(key, x, y)]: key = texts of the card, (x, y) = tap point (price centre)."""
    root = ET.fromstring(xml_source)
    parent = {c: p for p in root.iter() for c in p}
    cards = []
    for n in root.iter("node"):
        if not PRICE.match((n.get("text") or "").strip()):
            continue
        m = BOUNDS.match(n.get("bounds") or "")
        if not m:
            continue
        card = n
        for _ in range(4):
            if card in parent:
                card = parent[card]
            texts = [t.get("text") for t in card.iter("node") if t.get("text")]
            if len(texts) >= 2:
                break
        texts = [t.get("text") for t in card.iter("node") if t.get("text")]
        if len(texts) > 8:  # climbed into the whole list: fall back to the price alone
            texts = [n.get("text")]
        x1, y1, x2, y2 = map(int, m.groups())
        cards.append(("|".join(texts), (x1 + x2) // 2, (y1 + y2) // 2))
    return cards


def main():
    import uiautomator2 as u2
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial")
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--break-every", type=int, default=30)
    ap.add_argument("--out", default="out/products.jsonl")
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(exist_ok=True)
    seen = set()
    if out.exists():
        seen = {json.loads(l)["key"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    d = u2.connect(a.serial)
    done = stale = 0
    while done < a.max and stale < 4:
        fresh = [c for c in list_cards(d.dump_hierarchy()) if c[0] not in seen]
        if not fresh:
            stale += 1
            d.swipe_ext("up", scale=0.7)
            time.sleep(random.uniform(1.0, 2.0))
            continue
        stale = 0
        key, x, y = fresh[0]
        d.click(x, y)
        time.sleep(random.uniform(2.0, 3.5))
        item = scrape_current(d)
        item["key"] = key
        d.press("back")
        time.sleep(random.uniform(1.2, 2.2))
        if not list_cards(d.dump_hierarchy()):  # lost the list screen: stop rather than wander
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
    print(f"done: {done} products -> {out}")


if __name__ == "__main__":
    main()
