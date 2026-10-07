import argparse
import csv
import json
from .capture import capture
from .extract import extract_dir


def main():
    ap = argparse.ArgumentParser(prog="dewu-parser")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover", help="open URL, save all JSON responses to out/raw")
    d.add_argument("url")
    d.add_argument("--headed", action="store_true")
    e = sub.add_parser("export", help="extract products from out/raw to out/products.json|csv")
    e.add_argument("--raw", default="out/raw")
    a = ap.parse_args()

    if a.cmd == "discover":
        for url, path in capture(a.url, headless=not a.headed):
            print(path, url)
    else:
        rows = extract_dir(a.raw)
        with open("out/products.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        with open("out/products.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "title", "price_raw", "image"])
            for r in rows:
                w.writerow([r["id"], r["title"], r["price_raw"], r["image"]])
        print(f"{len(rows)} products -> out/products.json, out/products.csv")


if __name__ == "__main__":
    main()
