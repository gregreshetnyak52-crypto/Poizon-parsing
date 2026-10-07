"""Flatten out/products.jsonl into a table: one row per product x size. Writes CSV (opens in
Excel with Chinese text intact) and XLSX when openpyxl is installed."""
import csv
import json
from pathlib import Path

BASE = ["scraped_at", "source", "article", "brand", "title", "size", "hint", "available", "price_cny"]


def rows_from_jsonl(path, rate=None):
    rows, extra = [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        chart = item.get("size_chart") or {}
        cols = chart.get("columns") or []
        by_size = {r.get(cols[0]): r for r in chart.get("rows", [])} if cols else {}
        for c in cols[1:]:
            if c not in extra:
                extra.append(c)
        for s in item.get("sizes") or [{}]:
            row = {k: item.get(k) for k in BASE[:5]}
            row.update(size=s.get("size"), hint=s.get("hint"), available=s.get("available"),
                       price_cny=s.get("price_cny"))
            if rate:
                row["price_rub"] = round(s["price_cny"] * rate, 2) if s.get("price_cny") is not None else None
            for c, v in by_size.get(s.get("size"), {}).items():
                if c != cols[0]:
                    row[f"chart_{c}"] = v
            rows.append(row)
    header = BASE + (["price_rub"] if rate else []) + [f"chart_{c}" for c in extra]
    return header, rows


def export(src="out/products.jsonl", dst="out/products", rate=None, log=print):
    header, rows = rows_from_jsonl(src, rate)
    csv_path = Path(f"{dst}.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:  # BOM: Excel reads UTF-8
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    written = [str(csv_path)]
    try:
        from openpyxl import Workbook
    except ImportError:
        log("openpyxl not installed: skipped .xlsx (pip install openpyxl)")
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "products"
        ws.append(header)
        for r in rows:
            ws.append([r.get(h) for h in header])
        ws.freeze_panes = "A2"
        wb.save(f"{dst}.xlsx")
        written.append(f"{dst}.xlsx")
    log(f"{len(rows)} rows -> {', '.join(written)}")
    return header, rows
