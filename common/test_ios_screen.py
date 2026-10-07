import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ios"))
from ios_screen import texts_from_source

SRC = """<AppiumAUT><XCUIElementTypeApplication><XCUIElementTypeOther>
<XCUIElementTypeStaticText label="43.5(建议买小一码)" visible="true"/>
<XCUIElementTypeStaticText label="¥512" visible="true"/>
<XCUIElementTypeStaticText label="hidden" visible="false"/>
<XCUIElementTypeButton name="立即购买" visible="true"/>
</XCUIElementTypeOther></XCUIElementTypeApplication></AppiumAUT>"""


def test_texts():
    assert texts_from_source(SRC) == ["43.5(建议买小一码)", "¥512", "立即购买"]
