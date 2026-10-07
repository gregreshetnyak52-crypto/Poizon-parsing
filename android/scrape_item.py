"""Read ONE open product page on a connected Android device: title, price per size, size chart.

Open the product page in the app first. Only opens the size sheet (never selects a size
or pays) and the size-chart view, reading on-screen texts; then goes back.

Usage: python android/scrape_item.py [--serial ID] [--chart-text 尺码表] [--out out/item.json]
"""
import argparse
import json
import time
import xml.etree.ElementTree as ET

import uiautomator2 as u2

from parse_screen import parse_sizes, parse_title


def screen_texts(d):
    root = ET.fromstring(d.dump_hierarchy())
    return [n.get("text") for n in root.iter("node") if n.get("text")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial")
    ap.add_argument("--buy-text", default="立即购买", help="button that opens the size sheet")
    ap.add_argument("--chart-text", default="尺码表", help="link text that opens the size chart")
    ap.add_argument("--out", default="out/item.json")
    a = ap.parse_args()
    d = u2.connect(a.serial)

    item = {"title": parse_title(screen_texts(d))}

    if d(textContains=a.buy_text).click_exists(timeout=3):  # opens size sheet only
        time.sleep(2)
        sheet = screen_texts(d)
        item["sizes"] = parse_sizes(sheet)
        if d(textContains=a.chart_text).click_exists(timeout=2):
            time.sleep(2)
            item["size_chart_texts"] = screen_texts(d)  # raw; structure after seeing the screen
            d.press("back")
        d.press("back")  # close the sheet
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=1)
    print(json.dumps(item, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
