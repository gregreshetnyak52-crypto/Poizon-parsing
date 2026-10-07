import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ios"))
sys.modules.setdefault("appium", type(sys)("appium"))  # auto.py imports appium transitively
for m in ("appium.webdriver", "appium.options", "appium.options.ios", "appium.webdriver.common",
          "appium.webdriver.common.appiumby"):
    sys.modules.setdefault(m, type(sys)(m))
sys.modules["appium"].webdriver = sys.modules["appium.webdriver"]
sys.modules["appium.options.ios"].XCUITestOptions = object
sys.modules["appium.webdriver.common.appiumby"].AppiumBy = object
from auto import list_cards

SRC = """<AppiumAUT><XCUIElementTypeApplication><XCUIElementTypeCollectionView>
<XCUIElementTypeCell>
<XCUIElementTypeStaticText label="Timberland Martin boot" x="10" y="300" width="150" height="20" visible="true"/>
<XCUIElementTypeStaticText label="¥512" x="10" y="330" width="60" height="20" visible="true"/>
</XCUIElementTypeCell>
<XCUIElementTypeCell>
<XCUIElementTypeStaticText label="Nike Dunk Low" x="200" y="300" width="150" height="20" visible="true"/>
<XCUIElementTypeStaticText label="¥899" x="200" y="330" width="60" height="20" visible="true"/>
</XCUIElementTypeCell>
</XCUIElementTypeCollectionView></XCUIElementTypeApplication></AppiumAUT>"""


def test_cards():
    r = list_cards(SRC)
    assert r == [("Timberland Martin boot|¥512", 40, 340), ("Nike Dunk Low|¥899", 230, 340)]
