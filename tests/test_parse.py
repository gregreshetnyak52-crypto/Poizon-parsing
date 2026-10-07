"""Parser tests. Texts are transcribed from real Dewu screenshots (Timberland 6-inch boot, 2026)."""
from poizon.parse import (is_product_page, parse_delivery, parse_size_chart, parse_sizes,
                          parse_specs, parse_title)

PAGE = ["假日特惠", "≈", "¥512", "¥669", "直播领券再省¥5", "降价提醒", "1431商家竞价中",
        "Timberland添柏岚 Martin 舒适防水 短筒 户外靴 男款 小麦色 宽版", "8.4", "(956)",
        "刘冠佑同款", "193万人买过同品牌鞋子", "立即购买"]

SHEET = ["¥512.77", "比发售价低¥887", "尺码", "39.5(建议买小一码)", "¥628", "40(建议买小一码)", "¥620",
         "41(建议买小一码)", "¥545", "41.5(建议买小一码)", "¥558", "42(建议买小一码)", "¥566",
         "43(建议买小一码)", "¥543", "43.5(建议买小一码)", "¥512", "44(建议买小一码)", "¥579",
         "44.5(建议买小一码)", "¥621", "45(建议买小一码)", "¥621", "45.5(建议买小一码)", "¥796",
         "46(建议买小一码)", "¥638", "加购配件(可选11件)",
         "≈", "¥512.77", "约1-3天到", "已含税", "保税直发",
         "¥799", "约4-5天到", "顺丰速运", "品牌官方", "¥610"]

CHART = ["尺码助手", "欧码EU", "尺码说明", "US美码", "适合脚长(cm)",
         "39.5", "建议买小一码", "6.5", "24.5", "40", "建议买小一码", "7", "25",
         "41", "建议买小一码", "7.5", "25.5", "推荐", "46", "建议买小一码", "12", "30",
         "47.5", "建议买小一码", "13", "31"]


def test_title_skips_noise_between_price_and_title():
    assert parse_title(PAGE) == "Timberland添柏岚 Martin 舒适防水 短筒 户外靴 男款 小麦色 宽版"


def test_title_none_without_price():
    assert parse_title(["Timberland Martin boot long title"]) is None


def test_sizes_real_sheet():
    r = parse_sizes(SHEET)
    assert len(r) == 12
    assert r[6] == {"size": "43.5", "hint": "建议买小一码", "price_cny": 512.0, "available": True}
    assert r[-1]["size"] == "46" and r[-1]["price_cny"] == 638.0


def test_sizes_split_hint_clothing_and_sold_out():
    r = parse_sizes(["43.5", "(建议买小一码)", "¥512", "2XL", "¥300", "均码", "¥199",
                     "44", "--", "45", "到货提醒", "XS", "¥250"])
    assert r == [
        {"size": "43.5", "hint": "建议买小一码", "price_cny": 512.0, "available": True},
        {"size": "2XL", "hint": "", "price_cny": 300.0, "available": True},
        {"size": "均码", "hint": "", "price_cny": 199.0, "available": True},
        {"size": "44", "hint": "", "price_cny": None, "available": False},
        {"size": "45", "hint": "", "price_cny": None, "available": False},
        {"size": "XS", "hint": "", "price_cny": 250.0, "available": True},
    ]


def test_sizes_ignores_header_price_and_counts():
    # "¥512.77" before any size, and "加购配件(可选11件)" must not create sizes
    assert all(s["size"] != "11" for s in parse_sizes(SHEET))


def test_delivery_options():
    assert parse_delivery(SHEET) == [
        {"price_cny": 512.77, "eta": "约1-3天到", "labels": ["已含税", "保税直发"]},
        {"price_cny": 799.0, "eta": "约4-5天到", "labels": ["顺丰速运", "品牌官方"]},
    ]


def test_size_chart_real():
    cols, rows = parse_size_chart(CHART)
    assert cols == ["eu", "note", "us", "foot_cm"]
    assert [r["eu"] for r in rows] == ["39.5", "40", "41", "46", "47.5"]
    assert rows[0] == {"eu": "39.5", "note": "建议买小一码", "us": "6.5", "foot_cm": "24.5"}


def test_size_chart_ranges_dashes_and_scrolled_page():
    cols, rows = parse_size_chart(["欧码EU", "US美码", "适合脚长(cm)", "40", "-", "25-25.5"])
    assert rows == [{"eu": "40", "us": "-", "foot_cm": "25-25.5"}]
    # header scrolled away: reuse columns learned from the first screen
    _, more = parse_size_chart(["41", "7.5", "25.5"], columns=cols)
    assert more == [{"eu": "41", "us": "7.5", "foot_cm": "25.5"}]


def test_size_chart_clothing():
    cols, rows = parse_size_chart(["尺码", "胸围", "衣长", "M", "108", "70", "XL", "120", "74"])
    assert cols == ["size", "chest", "length"]
    assert rows == [{"size": "M", "chest": "108", "length": "70"},
                    {"size": "XL", "chest": "120", "length": "74"}]


def test_specs():
    texts = ["商品信息", "货号", "10061", "品牌", "Timberland", "发售日期：2020.09", "配色", "小麦色"]
    assert parse_specs(texts) == {"article": "10061", "brand": "Timberland",
                                  "release_date": "2020.09", "colorway": "小麦色"}


def test_product_page_detection():
    assert is_product_page(PAGE)
    assert not is_product_page(["推荐", "¥512", "Nike Dunk"])
