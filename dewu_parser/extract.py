"""Turn captured JSON into flat product rows.

Field names in Dewu responses are not documented. We walk the JSON and treat any dict
that has a title-like AND a price-like key as a product. Adjust KEYS after `discover`.
"""
import json
from pathlib import Path

TITLE_KEYS = ("title", "name", "spuTitle", "productName")
PRICE_KEYS = ("price", "minPrice", "authPrice", "salePrice")
ID_KEYS = ("spuId", "id", "productId", "articleNumber")


def _first(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]


def walk(node):
    if isinstance(node, dict):
        title, price = _first(node, TITLE_KEYS), _first(node, PRICE_KEYS)
        if title and price is not None:
            yield {"id": _first(node, ID_KEYS), "title": title, "price_raw": price,
                   "image": _first(node, ("logoUrl", "image", "imageUrl")), "raw": node}
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def extract_dir(raw_dir: str = "out/raw"):
    seen, rows = set(), []
    for f in sorted(Path(raw_dir).glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for r in walk(data["body"]):
            key = r["id"] or r["title"]
            if key not in seen:
                seen.add(key)
                rows.append(r)
    return rows
