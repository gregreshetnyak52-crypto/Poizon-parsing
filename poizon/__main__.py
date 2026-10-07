"""Command line: python -m poizon <item|crawl|dump|export> ...  (see README)."""
import argparse
import json
import sys
from pathlib import Path


def _device(a):
    from .devices import AndroidDevice, IOSDevice
    if a.platform == "android":
        return AndroidDevice(a.serial)
    if not a.udid:
        sys.exit("--udid is required for iOS (find it with: idevice_id -l)")
    return IOSDevice(a.udid, a.bundle_id, a.server, a.team_id, a.wda_bundle_id)


def _close(dev):
    if hasattr(dev, "quit"):
        dev.quit()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m poizon", description="Dewu (Poizon) app scraper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    dev_args = argparse.ArgumentParser(add_help=False)
    dev_args.add_argument("--platform", choices=["android", "ios"], required=True)
    dev_args.add_argument("--serial", help="Android: device id from `adb devices` (if several)")
    dev_args.add_argument("--udid", help="iOS: device UDID (idevice_id -l)")
    dev_args.add_argument("--bundle-id", default="com.siwuai.duapp", help="iOS: Dewu bundle id")
    dev_args.add_argument("--server", default="http://127.0.0.1:4723", help="iOS: Appium server")
    dev_args.add_argument("--team-id", help="iOS: Apple Team ID if WebDriverAgent is not signed in Xcode")
    dev_args.add_argument("--wda-bundle-id", help="iOS: unique bundle id for WebDriverAgentRunner")

    texts = argparse.ArgumentParser(add_help=False)
    texts.add_argument("--buy-text", default="立即购买", help="button that opens the size sheet")
    texts.add_argument("--chart-text", default="尺码推荐", help="link on the size sheet that opens 尺码助手")

    p = sub.add_parser("item", parents=[dev_args, texts], help="scrape the product page that is open")
    p.add_argument("--out", default="out/item.json")

    p = sub.add_parser("crawl", parents=[dev_args, texts], help="scrape every product of the open list")
    p.add_argument("--max", type=int, default=200, help="products per run")
    p.add_argument("--break-every", type=int, default=30, help="long pause after N products (0 = off)")
    p.add_argument("--source", help="label saved with each product, e.g. 'Nike sneakers'")
    p.add_argument("--out", default="out/products.jsonl")

    p = sub.add_parser("dump", parents=[dev_args], help="save screenshot + UI tree of the current screen")
    p.add_argument("--out", default="out/screen")

    p = sub.add_parser("export", help="products.jsonl -> CSV/XLSX (one row per size)")
    p.add_argument("--in", dest="src", default="out/products.jsonl")
    p.add_argument("--out", default="out/products", help="path without extension")
    p.add_argument("--rate", type=float, help="CNY->RUB rate, adds a price_rub column")

    a = ap.parse_args(argv)

    if a.cmd == "export":
        from .export import export
        export(a.src, a.out, a.rate)
        return

    from .crawler import crawl, scrape_item
    dev = _device(a)
    try:
        if a.cmd == "item":
            item = scrape_item(dev, a.buy_text, a.chart_text)
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(json.dumps(item, ensure_ascii=False, indent=1), encoding="utf-8")
            print(json.dumps(item, ensure_ascii=False, indent=1))
        elif a.cmd == "crawl":
            crawl(dev, a.out, a.max, a.break_every, a.source, a.buy_text, a.chart_text)
        elif a.cmd == "dump":
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            dev.screenshot(f"{a.out}.png")
            Path(f"{a.out}.xml").write_text(dev.source(), encoding="utf-8")
            print(f"saved {a.out}.png, {a.out}.xml")
    finally:
        _close(dev)


if __name__ == "__main__":
    main()
