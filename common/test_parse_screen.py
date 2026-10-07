from parse_screen import parse_sizes, parse_title

SHEET = ["尺码", "39.5(建议买小一码)", "¥628", "40(建议买小一码)", "¥620", "41(建议买小一码)", "¥545",
         "41.5(建议买小一码)", "¥558", "42(建议买小一码)", "¥566", "43(建议买小一码)", "¥543",
         "43.5(建议买小一码)", "¥512", "44(建议买小一码)", "¥579", "44.5(建议买小一码)", "¥621",
         "45(建议买小一码)", "¥621", "45.5(建议买小一码)", "¥796", "46(建议买小一码)", "¥638"]
PAGE = ["¥512", "¥669", "直播领券再省¥5", "Timberland添柏岚 Martin 舒适防水 短筒 户外靴 男款 小麦色 宽版", "8.4 (956)"]


def test_sizes():
    r = parse_sizes(SHEET)
    assert len(r) == 12
    assert r[6] == {"size": "43.5", "hint": "建议买小一码", "price_cny": 512.0}
    assert r[-1]["size"] == "46" and r[-1]["price_cny"] == 638.0


def test_title():
    assert parse_title(PAGE).startswith("Timberland添柏岚 Martin")


def test_size_chart():
    from parse_screen import parse_size_chart
    t = ["尺码助手", "欧码EU", "尺码说明", "US美码", "适合脚长(cm)",
         "39.5", "建议买小一码", "6.5", "24.5", "40", "建议买小一码", "7", "25",
         "推荐", "46", "建议买小一码", "12", "30", "47.5", "建议买小一码", "13", "31"]
    r = parse_size_chart(t)
    assert [x["eu"] for x in r] == ["39.5", "40", "46", "47.5"]
    assert r[0] == {"eu": "39.5", "note": "建议买小一码", "us": "6.5", "foot_cm": 24.5}
    assert r[-1]["foot_cm"] == 31.0
