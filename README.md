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

## 2. Public web pages (Playwright)
```
playwright install chromium
python -m dewu_parser.cli discover "<public listing url>"
python -m dewu_parser.cli export
```
Field names in `dewu_parser/extract.py` are guesses; tune after the first run.
