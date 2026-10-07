"""Save page source + screenshot of the current iPhone screen (to debug empty/odd text trees)."""
import sys
from pathlib import Path
from appium import webdriver
from appium.options.ios import XCUITestOptions

udid, bundle = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "com.siwuai.duapp")
o = XCUITestOptions()
o.udid, o.bundle_id, o.no_reset = udid, bundle, True
d = webdriver.Remote("http://127.0.0.1:4723", options=o)
Path("out").mkdir(exist_ok=True)
Path("out/ios_source.xml").write_text(d.page_source, encoding="utf-8")
d.save_screenshot("out/ios_screen.png")
d.quit()
print("saved out/ios_source.xml, out/ios_screen.png")
