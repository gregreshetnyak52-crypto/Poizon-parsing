"""Read ONE open product page on an iPhone via Appium: title, price per size, size chart.

Open the product page in the Dewu app first. Only opens the size sheet (never selects a
size or pays) and the size chart, reading on-screen texts.

Usage: python ios/scrape_item_ios.py --udid <UDID> [--bundle-id <id>] [--chart-text 尺码推荐]
Requires a running Appium server (see README, iOS section).
"""
import argparse
import json
import sys
import time
from pathlib import Path

from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ios_screen import texts_from_source  # noqa: E402
from parse_screen import parse_size_chart, parse_sizes, parse_title  # noqa: E402


class Screen:
    def __init__(self, drv):
        self.d = drv
        size = drv.get_window_size()
        self.w, self.h = size["width"], size["height"]

    def texts(self):
        return texts_from_source(self.d.page_source)

    def tap_text(self, needle, timeout=3):
        end = time.time() + timeout
        while time.time() < end:
            els = self.d.find_elements(AppiumBy.IOS_PREDICATE, f'label CONTAINS "{needle}" OR name CONTAINS "{needle}"')
            if els:
                els[0].click()
                return True
            time.sleep(0.5)
        return False

    def tap_xy(self, fx, fy):
        self.d.execute_script("mobile: tap", {"x": int(self.w * fx), "y": int(self.h * fy)})

    def swipe_up(self):
        self.d.execute_script("mobile: dragFromToForDuration", {
            "fromX": self.w // 2, "fromY": int(self.h * 0.75),
            "toX": self.w // 2, "toY": int(self.h * 0.35), "duration": 0.4})

    def close_sheet(self):
        self.tap_xy(0.5, 0.08)  # dimmed area above a bottom sheet dismisses it


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--udid", required=True)
    ap.add_argument("--bundle-id", default="com.siwuai.duapp", help="check with: ideviceinstaller -l")
    ap.add_argument("--server", default="http://127.0.0.1:4723")
    ap.add_argument("--buy-text", default="立即购买")
    ap.add_argument("--chart-text", default="尺码推荐")
    ap.add_argument("--out", default="out/item_ios.json")
    a = ap.parse_args()

    opts = XCUITestOptions()
    opts.udid = a.udid
    opts.bundle_id = a.bundle_id
    opts.no_reset = True  # keep login and the open screen
    opts.set_capability("appium:includeSafariInWebviews", False)
    drv = webdriver.Remote(a.server, options=opts)
    try:
        s = Screen(drv)
        item = {"title": parse_title(s.texts())}
        if s.tap_text(a.buy_text):
            time.sleep(2)
            item["sizes"] = parse_sizes(s.texts())
            if s.tap_text(a.chart_text):
                time.sleep(2)
                chart, stale = {}, 0
                while stale < 2:
                    new = 0
                    for r in parse_size_chart(s.texts()):
                        if r["eu"] not in chart:
                            chart[r["eu"]] = r
                            new += 1
                    stale = stale + 1 if new == 0 else 0
                    s.swipe_up()
                    time.sleep(1)
                item["size_chart"] = list(chart.values())
                s.close_sheet()
            s.close_sheet()
    finally:
        drv.quit()
    Path(a.out).parent.mkdir(exist_ok=True)
    Path(a.out).write_text(json.dumps(item, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(item, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
