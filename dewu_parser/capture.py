"""Open a public Dewu/Poizon page in a real browser and record every JSON XHR response.

We do not forge request signatures: the page's own JS makes the requests, we only
read the responses. Use `discover` first to see which endpoints carry catalog data.
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def capture(url: str, out_dir: str = "out/raw", wait: float = 8.0, scroll: int = 5, headless: bool = True):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved = []

    def on_response(resp):
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            body = resp.json()
        except Exception:
            return
        path = out / f"{len(saved):04d}.json"
        path.write_text(json.dumps({"url": resp.url, "status": resp.status, "body": body},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
        saved.append((resp.url, str(path)))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(locale="zh-CN")
        page = ctx.new_page()
        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60000)
        for _ in range(scroll):  # trigger lazy-loaded listing pages
            page.mouse.wheel(0, 4000)
            time.sleep(wait / max(scroll, 1))
        browser.close()
    return saved
