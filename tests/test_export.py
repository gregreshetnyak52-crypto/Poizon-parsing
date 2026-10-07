import csv
import json

from poizon.export import export


def test_export_rows_per_size_with_chart_and_rub(tmp_path):
    item = {
        "scraped_at": "2026-10-07T10:00:00+00:00", "source": "boots", "article": "10061",
        "brand": "Timberland", "title": "Timberland Martin",
        "sizes": [{"size": "43.5", "hint": "建议买小一码", "price_cny": 512.0, "available": True},
                  {"size": "44", "hint": "", "price_cny": None, "available": False}],
        "size_chart": {"columns": ["eu", "note", "us", "foot_cm"],
                       "rows": [{"eu": "43.5", "note": "建议买小一码", "us": "9.5", "foot_cm": "27.5"}]},
    }
    src = tmp_path / "p.jsonl"
    src.write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")
    header, rows = export(src, tmp_path / "out", rate=12.5, log=lambda *_: None)

    assert header[-3:] == ["chart_note", "chart_us", "chart_foot_cm"]
    assert rows[0]["price_rub"] == 6400.0 and rows[0]["chart_us"] == "9.5"
    assert rows[1]["price_rub"] is None and "chart_us" not in rows[1]

    with open(tmp_path / "out.csv", encoding="utf-8-sig") as f:
        got = list(csv.DictReader(f))
    assert got[0]["title"] == "Timberland Martin" and got[0]["size"] == "43.5"
    assert (tmp_path / "out.xlsx").exists()
