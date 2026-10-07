"""Platform-independent scraping logic on top of a device adapter (see poizon.devices)."""
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from .parse import (POPUP_CLOSE_TEXTS, is_product_page, parse_delivery, parse_size_chart, parse_sizes,
                    parse_specs, parse_title)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def close_popups(dev, rounds=2):
    """Dismiss known coupon/ad/notice popups. Only call on the list or product page, never while
    the size sheet is open (its close button can also be labelled 关闭)."""
    closed = 0
    for _ in range(rounds):
        hit = False
        texts = dev.texts()
        for t in POPUP_CLOSE_TEXTS:
            if any(x.strip() == t for x in texts) and dev.tap_text(t, timeout=0):
                closed += 1
                hit = True
                break
        if not hit:
            break
    return closed


def scrape_item(dev, buy_text="立即购买", chart_text="尺码推荐", spec_scrolls=4, sheet_scrolls=3,
                pause=time.sleep):
    """Scrape the product page currently open: title, specs (article, brand...), price per size,
    delivery options, size chart. Opens the size sheet only to read it: never selects a size or pays."""
    item = {"scraped_at": _now()}
    top = dev.texts()
    item["title"] = parse_title(top)

    specs = parse_specs(top)
    for _ in range(spec_scrolls):  # 商品信息 block is further down the page
        if "article" in specs:
            break
        dev.scroll_down()
        pause(1)
        for k, v in parse_specs(dev.texts()).items():
            specs.setdefault(k, v)
    item.update(specs)

    if dev.tap_text(buy_text):
        pause(2)
        sheet = dev.texts()
        item["sizes"] = parse_sizes(sheet)
        item["delivery"] = parse_delivery(sheet)
        if dev.tap_text(chart_text, timeout=2):
            pause(2)
            columns, rows, stale = None, {}, 0
            while stale < 2:  # the table scrolls: collect until no new rows
                cols, page = parse_size_chart(dev.texts(), columns)
                columns = columns or cols
                new = 0
                for r in page:
                    key = next(iter(r.values()))
                    if key not in rows:
                        rows[key] = r
                        new += 1
                stale = stale + 1 if new == 0 else 0
                dev.scroll_down()
                pause(1)
            item["size_chart"] = {"columns": columns or [], "rows": list(rows.values())}
            dev.close_sheet()
            pause(1)
        # long size lists scroll inside the sheet (done after the chart: its link is at the top)
        have = {s["size"] for s in item["sizes"]}
        for _ in range(sheet_scrolls):
            dev.scroll_down()
            pause(1)
            more = [s for s in parse_sizes(dev.texts()) if s["size"] not in have]
            if not more:
                break
            item["sizes"] += more
            have.update(s["size"] for s in more)
        dev.close_sheet()
        pause(1)
    return item


def load_seen(path):
    cards, articles = set(), set()
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("card_key"):
                cards.add(rec["card_key"])
            if rec.get("article"):
                articles.add(rec["article"])
    return cards, articles


def crawl(dev, out="out/products.jsonl", max_items=200, break_every=30, source=None,
          buy_text="立即购买", chart_text="尺码推荐", errors_dir="out/errors",
          pause=time.sleep, jitter=random.uniform, log=print):
    """Open every product on the list screen that is currently open, scrape it, go back, scroll.
    Appends one JSON line per product to `out` and resumes from it on the next run."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    errors = Path(errors_dir)
    seen_cards, seen_articles = load_seen(out)
    done = stale = fails = 0

    def snap(reason):
        errors.mkdir(parents=True, exist_ok=True)
        name = errors / f"{datetime.now():%Y%m%d-%H%M%S}-{reason}"
        try:
            dev.screenshot(f"{name}.png")
            Path(f"{name}.xml").write_text(dev.source(), encoding="utf-8")
        except Exception as e:  # diagnostics must never stop the crawl
            log(f"  (could not save diagnostics: {e})")
        return name

    while done < max_items and stale < 4 and fails < 3:
        close_popups(dev)
        fresh = [c for c in dev.cards() if c[0] not in seen_cards]
        if not fresh:
            stale += 1
            dev.scroll_down()
            pause(jitter(1.0, 2.0))
            continue
        stale = 0
        key, x, y = fresh[0]
        seen_cards.add(key)
        dev.tap(x, y)
        pause(jitter(2.0, 3.5))
        close_popups(dev)

        if not is_product_page(dev.texts(), buy_text):
            fails += 1
            log(f"  not a product page after tapping '{key[:40]}' -> {snap('not-product')}.png")
            dev.back()
            pause(jitter(1.2, 2.2))
            continue
        try:
            item = scrape_item(dev, buy_text, chart_text, pause=pause)
        except Exception as e:
            fails += 1
            log(f"  error while scraping '{key[:40]}': {e} -> {snap('error')}.png")
            dev.back()
            pause(jitter(1.2, 2.2))
            continue

        item["card_key"] = key
        if source:
            item["source"] = source
        dev.back()
        pause(jitter(1.2, 2.2))
        close_popups(dev)
        if not dev.cards():  # lost the list screen: stop rather than wander around the app
            log(f"list screen not found after going back; stopping -> {snap('lost-list')}.png")
            break

        if item.get("article") and item["article"] in seen_articles:
            log(f"  skip duplicate article {item['article']}")
            continue
        if not (item.get("sizes") or item.get("title")):
            fails += 1
            log(f"  empty result for '{key[:40]}'")
            continue
        fails = 0
        if item.get("article"):
            seen_articles.add(item["article"])
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        done += 1
        log(f"[{done}] {item.get('article') or ''} {item.get('title')}")
        if break_every and done % break_every == 0:
            pause(jitter(30, 90))
    if fails >= 3:
        log("stopped after 3 failures in a row; see out/errors/")
    log(f"done: {done} products -> {out}")
    return done
