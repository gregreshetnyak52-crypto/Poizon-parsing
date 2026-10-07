"""Parse Dewu product screens from a flat list of on-screen texts (no resource ids needed)."""
import re

SIZE_RE = re.compile(r"^(?P<size>\d{2}(?:\.\d)?|[XSML]{1,3}L?|\d{2,3}/\d{2,3}\w?)(?P<hint>[（(][^）)]*[）)])?$")
PRICE_RE = re.compile(r"^[¥￥]\s*(?P<price>\d+(?:\.\d+)?)$")


def parse_sizes(texts):
    """Size sheet: pairs of '<size>(hint)' followed by '¥<price>'. Returns list of dicts."""
    out, pending = [], None
    for t in (x.strip() for x in texts if x and x.strip()):
        m = SIZE_RE.match(t)
        if m:
            pending = m
            continue
        p = PRICE_RE.match(t)
        if p and pending:
            out.append({"size": pending["size"], "hint": (pending["hint"] or "").strip("（）()"),
                        "price_cny": float(p["price"])})
            pending = None
    return out


def parse_title(texts):
    """Title = first long text after the first price on the product page."""
    seen_price = False
    for t in (x.strip() for x in texts if x and x.strip()):
        if PRICE_RE.match(t) or re.fullmatch(r"≈?[¥￥]?\d+", t):
            seen_price = True
            continue
        if seen_price and len(t) >= 8 and "¥" not in t and "￥" not in t:
            return t
    return None
