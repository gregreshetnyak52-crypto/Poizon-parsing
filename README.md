# Poizon-parsing

Free tools for collecting Dewu (Poizon) catalog data. Status: **scaffold, untested against the live app/site**.

## 1. Android emulator (app data)
Reads what the real app renders (UI automation). The app makes its own signed requests;
nothing here bypasses SSL pinning, request signing or anti-bot checks.

1. Run an Android emulator (Android Studio AVD / Genymotion), install Dewu, log in, open a category list.
2. `pip install -r requirements.txt`
3. `mkdir -p out && python android/dump.py` and tune `android/selectors.json` from `out/hierarchy.xml`.
4. `python android/scrape.py --max 500` -> `out/app_products.json|csv`.

The app may detect emulators or limit accounts; use at your own risk and respect Dewu's terms.

### Real phone (recommended over an emulator)
1. On the phone: Settings -> About -> tap Build number 7 times -> Developer options -> enable USB debugging.
2. Connect by USB, accept the prompt, check `adb devices` (or `python -m uiautomator2 init`).
3. Open the product list in the app, then `python android/scrape.py --serial <id from adb devices>`.

### Sizes and specs
`python android/scrape.py --details` opens each new card, reads `detail_fields` from
`android/selectors.json` (tune them with `dump.py` on a product page), and goes back.
It pauses 30-90 s every `--break-every` products (default 100) to keep load low.

## 2. Public web pages (Playwright)
```
playwright install chromium
python -m dewu_parser.cli discover "<public listing url>"
python -m dewu_parser.cli export
```
Field names in `dewu_parser/extract.py` are guesses; tune after the first run.

## One product: title, price per size, size chart
Open a product page on an **Android** device, then `python android/scrape_item.py`.
Parsing is text-based (`android/parse_screen.py`, tested on real screenshots: `cd android && python -c "import test_parse_screen as t; t.test_sizes(); t.test_title()"`).
Size chart (尺码助手: EU, note, US, foot length cm) is parsed and scrolled; the link text defaults to 尺码推荐 (unconfirmed, tune with --chart-text). iPhone is not supported by uiautomator2.
