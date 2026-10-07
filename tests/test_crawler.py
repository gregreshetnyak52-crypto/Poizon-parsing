"""Crawler logic against a fake device that simulates the app's screens."""
import json

from poizon.crawler import crawl, scrape_item
from tests.test_parse import CHART, SHEET

PRODUCT_TOP = ["假日特惠", "≈", "¥512", "¥669", "降价提醒", "1431商家竞价中",
               "Timberland添柏岚 Martin 舒适防水 短筒 户外靴 男款 小麦色 宽版", "立即购买"]
PRODUCT_SPECS = ["商品信息", "货号", "10061", "品牌", "Timberland", "立即购买"]


class FakeDevice:
    """Screens: list -> product (tap card) -> sheet (立即购买) -> chart (尺码推荐)."""

    def __init__(self, cards, banner_keys=(), popup_on_product=False):
        self.screen = "list"
        self.all_cards = cards          # [(key, x, y)]
        self.banner_keys = set(banner_keys)
        self.popup = popup_on_product
        self.scrolled = 0
        self.list_page = 0
        self.taps = []
        self.opened = None
        self.sheet_scrolled = 0

    # interface used by the crawler
    def texts(self):
        if self.screen == "product":
            if self.popup:
                return ["领取优惠券", "我知道了"]
            return PRODUCT_SPECS if self.scrolled else PRODUCT_TOP
        if self.screen == "banner":
            return ["活动页"]
        if self.screen == "sheet":
            if self.sheet_scrolled:
                return ["46.5(建议买小一码)", "¥700", "47", "到货提醒"] if self.sheet_scrolled == 1 else ["47", "到货提醒"]
            return SHEET + ["尺码推荐"]
        if self.screen == "chart":
            return CHART
        return [k for k, _, _ in self.cards()]

    def source(self):
        return "<x/>"

    def cards(self):
        if self.screen != "list":
            return []
        return self.all_cards[self.list_page * 2:self.list_page * 2 + 2]

    def has_text(self, t):
        return any(t in x for x in self.texts())

    def tap_text(self, t, timeout=3):
        self.taps.append(t)
        if not self.has_text(t):
            return False
        if t == "我知道了":
            self.popup = False
        elif t == "立即购买":
            self.screen = "sheet"
            self.sheet_scrolled = 0
        elif t == "尺码推荐":
            self.screen = "chart"
        return True

    def tap(self, x, y):
        key = next(k for k, cx, cy in self.cards() if (cx, cy) == (x, y))
        self.opened = key
        self.screen = "banner" if key in self.banner_keys else "product"
        self.scrolled = 0

    def scroll_down(self):
        if self.screen == "list":
            self.list_page += 1
        elif self.screen == "sheet":
            self.sheet_scrolled += 1
        else:
            self.scrolled += 1

    def back(self):
        self.screen = "list"

    def close_sheet(self):
        self.screen = {"chart": "sheet", "sheet": "product"}.get(self.screen, self.screen)

    def screenshot(self, path):
        open(path, "wb").close()


def no_pause(*_):
    pass


def test_scrape_item_full():
    dev = FakeDevice([("a", 1, 1)])
    dev.screen = "product"
    item = scrape_item(dev, pause=no_pause)
    assert item["title"].startswith("Timberland添柏岚")
    assert item["article"] == "10061" and item["brand"] == "Timberland"
    assert len(item["sizes"]) == 14  # 12 on the first screen + 2 after scrolling the sheet
    assert item["sizes"][-1] == {"size": "47", "hint": "", "price_cny": None, "available": False}
    assert item["delivery"][0]["price_cny"] == 512.77
    assert item["size_chart"]["columns"] == ["eu", "note", "us", "foot_cm"]
    assert len(item["size_chart"]["rows"]) == 5
    assert dev.screen == "product"  # both sheets closed again
    assert "scraped_at" in item


def test_crawl_writes_skips_banner_and_resumes(tmp_path):
    cards = [("Timberland|¥512", 10, 10), ("Banner|¥1", 20, 20), ("Nike|¥899", 30, 30)]
    out = tmp_path / "p.jsonl"
    dev = FakeDevice(cards, banner_keys={"Banner|¥1"})
    n = crawl(dev, out, max_items=10, break_every=0, source="boots", errors_dir=tmp_path / "err",
              pause=no_pause, jitter=lambda a, b: 0, log=lambda *_: None)
    lines = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    # Timberland and Nike are the same fake product (same article) -> written once
    assert n == 1 and len(lines) == 1
    assert lines[0]["source"] == "boots" and lines[0]["card_key"] == "Timberland|¥512"
    assert list((tmp_path / "err").glob("*not-product.png"))  # banner diagnosed, not saved

    # resume: nothing new is written, already-seen article is skipped
    dev2 = FakeDevice(cards, banner_keys={"Banner|¥1"})
    n2 = crawl(dev2, out, max_items=10, break_every=0, errors_dir=tmp_path / "err",
               pause=no_pause, jitter=lambda a, b: 0, log=lambda *_: None)
    assert n2 == 0
    assert len(out.read_text(encoding="utf-8").splitlines()) == 1


def test_crawl_closes_popup_on_product_page(tmp_path):
    dev = FakeDevice([("Timberland|¥512", 10, 10)], popup_on_product=True)
    out = tmp_path / "p.jsonl"
    n = crawl(dev, out, max_items=1, break_every=0, errors_dir=tmp_path / "err",
              pause=no_pause, jitter=lambda a, b: 0, log=lambda *_: None)
    assert n == 1 and "我知道了" in dev.taps


def test_crawl_stops_after_three_failures(tmp_path):
    cards = [(f"B{i}|¥1", i, i) for i in range(6)]
    dev = FakeDevice(cards, banner_keys={k for k, _, _ in cards})
    n = crawl(dev, tmp_path / "p.jsonl", max_items=10, break_every=0, errors_dir=tmp_path / "err",
              pause=no_pause, jitter=lambda a, b: 0, log=lambda *_: None)
    assert n == 0 and dev.list_page <= 2
