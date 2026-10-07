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
Parsing is text-based (`android/parse_screen.py`, tested on real screenshots: `cd common && python -c "import test_parse_screen as t; t.test_sizes(); t.test_title(); t.test_size_chart()"`).
Size chart (尺码助手: EU, note, US, foot length cm) is parsed and scrolled; the link text defaults to 尺码推荐 (unconfirmed, tune with --chart-text). For iPhone use ios/ (below).

## iPhone (Appium + XCUITest, needs a Mac)
One-time setup:
1. Xcode installed; iPhone connected by USB, Developer Mode on (Settings -> Privacy & Security), trusted.
2. `brew install node && npm i -g appium && appium driver install xcuitest`
3. WebDriverAgent must be signed once with your Apple ID: open
   `~/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj`
   in Xcode, set your Team and a unique bundle id for the WebDriverAgentRunner target (free Apple ID: re-sign every 7 days).
4. `appium` (leave running), `pip install -r requirements.txt`.

Run (product page open in the app):
```
python ios/scrape_item_ios.py --udid <UDID>      # UDID: idevice_id -l  or Xcode > Devices
```
Output: `out/item_ios.json` (same format as Android). Bundle id default `com.siwuai.duapp` is unverified; check with `ideviceinstaller -l`.
If texts come back empty (the app draws its own UI), run `python ios/dump_ios.py <UDID>` and inspect `out/ios_source.xml`;
the fallback is screenshot + OCR.

## Automatic crawl (iPhone)
Open a product LIST in the app (category, brand or search results), then:
```
python ios/auto.py --udid <UDID> --max 200
```
For every product on the list it opens the card, reads title + price per size + size chart, goes back
(edge-swipe), scrolls, and continues. Results are appended to `out/products.jsonl` (one JSON per line);
re-running resumes and skips products already saved. It pauses 30-90 s every `--break-every` (30) products
and stops if it cannot find the list after going back. Cards are found by their `¥price` text
(`list_cards` in `ios/auto.py`, unit-tested on a synthetic tree) - tune it from `ios/dump_ios.py` output if your list differs.
