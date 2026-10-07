"""Parse Dewu screens from a flat list of on-screen texts (document order, no resource ids).

Every function takes the texts a device adapter read from the screen and returns plain data,
so they are tested without a phone (see tests/).
"""
import re

# --- primitives -------------------------------------------------------------------------------

PRICE_RE = re.compile(r"^[¥￥]\s*(?P<price>\d+(?:\.\d+)?)\s*起?$")
# Shoe sizes (39.5, 42 2/3), letter sizes (XS..XXXL, 2XL), one-size, Chinese clothing (170/88A)
SIZE_CORE = (r"\d{2}(?:\.\d)?(?:\s?\d/\d)?"
             r"|X{0,3}S|M|X{0,3}L|\dXL|均码|F|ONE ?SIZE"
             r"|\d{3}/\d{2,3}[A-Z]?")
SIZE_RE = re.compile(rf"^(?P<size>{SIZE_CORE})\s*(?P<hint>[（(][^）)]*[）)])?$", re.I)
HINT_RE = re.compile(r"^[（(][^）)]*[）)]$")
UNAVAILABLE = ("--", "-", "到货提醒", "缺货", "售罄", "暂无", "已售罄", "补货中")
ETA_RE = re.compile(r"约?\s*\d+\s*[-–~]?\s*\d*\s*天到")

# Texts on the product page that are long but are NOT the title
TITLE_NOISE = ("商家竞价", "人买过", "人想要", "降价提醒", "领券", "正品", "鉴别", "无理由", "运费",
               "解读", "同款", "评价", "穿过", "想要", "补贴", "分期", "包邮", "直播")


def _clean(texts):
    return [t.strip() for t in texts if t and t.strip()]


def _price(t):
    m = PRICE_RE.match(t)
    return float(m["price"]) if m else None


# --- product page ------------------------------------------------------------------------------

def parse_title(texts, window=8):
    """Title: the longest non-noise text among the first `window` texts after the first price."""
    cells = _clean(texts)
    start = next((i for i, t in enumerate(cells) if _price(t) is not None
                  or re.fullmatch(r"≈?\s*[¥￥]\s*\d+(?:\.\d+)?", t)), None)
    if start is None:
        return None
    best = None
    for t in cells[start + 1:start + 1 + window]:
        if len(t) < 8 or "¥" in t or "￥" in t or any(n in t for n in TITLE_NOISE):
            continue
        if re.fullmatch(r"[\d\s.,()（）万+%]+", t):
            continue
        if best is None or len(t) > len(best):
            best = t
    return best


SPEC_LABELS = {
    "货号": "article", "品牌": "brand", "发售日期": "release_date", "发售价格": "retail_price",
    "配色": "colorway", "主色": "color", "鞋面材质": "upper_material", "适用季节": "season",
    "适用人群": "gender", "系列": "series",
}


def parse_specs(texts):
    """商品信息 block: '<label>' followed by '<value>' (or 'label value' / 'label：value' in one text).
    Returns e.g. {'article': '10061', 'brand': 'Timberland'}; unknown labels are ignored."""
    cells = _clean(texts)
    out = {}
    for i, t in enumerate(cells):
        for label, key in SPEC_LABELS.items():
            if key in out:
                continue
            if t == label and i + 1 < len(cells):
                out[key] = cells[i + 1]
            elif t.startswith(label) and len(t) > len(label):
                rest = t[len(label):].lstrip(" :：\t")
                if rest:
                    out[key] = rest
    return out


# --- size sheet --------------------------------------------------------------------------------

def parse_sizes(texts):
    """Size sheet: '<size>(hint)' then '¥<price>'. Handles size and hint as separate texts and
    sold-out sizes ('--', '到货提醒' ...), which get price None and available False."""
    cells = _clean(texts)
    out, pending = [], None

    def flush(price):
        nonlocal pending
        if pending:
            pending.update(price_cny=price, available=price is not None)
            out.append(pending)
            pending = None

    for t in cells:
        m = SIZE_RE.match(t)
        if m:
            if pending:  # previous size had neither price nor an 'unavailable' marker
                flush(None)
            pending = {"size": m["size"].upper() if m["size"].isascii() else m["size"],
                       "hint": (m["hint"] or "").strip("（）()")}
            continue
        if pending and HINT_RE.match(t) and not pending["hint"]:
            pending["hint"] = t.strip("（）()")
            continue
        p = _price(t)
        if p is not None and pending:
            flush(p)
        elif pending and t in UNAVAILABLE:
            flush(None)
    flush(None)
    return out


def parse_delivery(texts):
    """Delivery options at the bottom of the size sheet: '¥512.77' '约1-3天到' '已含税' '保税直发'.
    An option is a price followed (within 2 texts) by an ETA; labels are the short texts after it."""
    cells = _clean(texts)
    out = []
    for i, t in enumerate(cells):
        p = _price(t)
        if p is None:
            continue
        eta_i = next((j for j in range(i + 1, min(i + 3, len(cells))) if ETA_RE.search(cells[j])), None)
        if eta_i is None:
            continue
        labels = []
        for u in cells[eta_i + 1:eta_i + 4]:
            if _price(u) is not None or ETA_RE.search(u):
                break
            if len(u) <= 6 and not re.search(r"\d", u) and u not in ("≈", "|"):
                labels.append(u)
        out.append({"price_cny": p, "eta": ETA_RE.search(cells[eta_i]).group(0).replace(" ", ""),
                    "labels": labels})
    return out


# --- size chart (尺码助手) ----------------------------------------------------------------------

COLUMN_KEYS = {"欧码EU": "eu", "尺码说明": "note", "US美码": "us", "适合脚长(cm)": "foot_cm",
               "适合脚长（cm）": "foot_cm", "UK英码": "uk", "JP日码": "jp", "尺码": "size",
               "胸围": "chest", "衣长": "length", "肩宽": "shoulder", "袖长": "sleeve",
               "腰围": "waist", "臀围": "hips", "身高": "height"}
BADGES = {"推荐", "推", "荐", "推\n荐"}
CHART_TITLES = {"尺码助手", "尺码表", "尺码对照表"}
_CELL_VALUE = re.compile(rf"^(?:{SIZE_CORE}|\d+(?:\.\d+)?(?:\s*[-~–]\s*\d+(?:\.\d+)?)?|-)$", re.I)


def parse_size_chart(texts, columns=None):
    """尺码助手 table. Learns column names from the header (first screen) and splits the cells
    after it into rows. Pass `columns` from a previous screen when the header scrolled away.
    Returns (columns, rows); each row maps column key -> text (ranges like '25-25.5' kept)."""
    cells = [t for t in _clean(texts) if t not in BADGES and t not in CHART_TITLES]
    start = 0
    if columns is None:
        hdr = [i for i, t in enumerate(cells) if t in COLUMN_KEYS]
        if not hdr:
            return None, []
        first, last = hdr[0], hdr[0]
        while last + 1 < len(cells) and not _CELL_VALUE.match(cells[last + 1]):
            last += 1
        columns = [COLUMN_KEYS.get(t, t) for t in cells[first:last + 1]]
        start = last + 1
    n = len(columns)
    rows, i = [], start
    while i + n <= len(cells):
        chunk = cells[i:i + n]
        if SIZE_RE.match(chunk[0]) and all(_CELL_VALUE.match(c) or not re.search(r"\d", c) for c in chunk):
            rows.append(dict(zip(columns, chunk)))
            i += n
        else:
            i += 1
    return columns, rows


# --- page detection and popups ----------------------------------------------------------------

POPUP_CLOSE_TEXTS = ("我知道了", "知道了", "暂不", "以后再说", "跳过", "关闭", "残忍离开", "不感兴趣")


def is_product_page(texts, buy_text="立即购买"):
    return any(buy_text in t for t in _clean(texts))
