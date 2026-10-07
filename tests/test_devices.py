from poizon.devices import android_cards, android_texts, ios_cards, ios_texts

ANDROID = """<hierarchy><node text="" bounds="[0,0][1080,2400]">
<node text="" bounds="[0,500][540,900]">
<node text="Timberland Martin boot" bounds="[10,700][500,740]"/>
<node text="¥512" bounds="[10,760][110,800]"/></node>
<node text="" bounds="[540,500][1080,900]">
<node text="Nike Dunk Low" bounds="[550,700][1000,740]"/>
<node text="¥899" bounds="[550,760][650,800]"/></node>
<node text="" content-desc="立即购买" bounds="[0,0][1,1]"/></node></hierarchy>"""

IOS = """<AppiumAUT><XCUIElementTypeApplication><XCUIElementTypeCollectionView>
<XCUIElementTypeCell>
<XCUIElementTypeStaticText label="Timberland Martin boot" x="10" y="300" width="150" height="20" visible="true"/>
<XCUIElementTypeStaticText label="¥512" x="10" y="330" width="60" height="20" visible="true"/>
</XCUIElementTypeCell>
<XCUIElementTypeCell>
<XCUIElementTypeStaticText label="Nike Dunk Low" x="200" y="300" width="150" height="20" visible="true"/>
<XCUIElementTypeStaticText label="¥899" x="200" y="330" width="60" height="20" visible="true"/>
<XCUIElementTypeStaticText label="hidden" visible="false"/>
</XCUIElementTypeCell>
<XCUIElementTypeButton name="立即购买" visible="true"/>
</XCUIElementTypeCollectionView></XCUIElementTypeApplication></AppiumAUT>"""


def test_android_cards():
    assert android_cards(ANDROID) == [("Timberland Martin boot|¥512", 60, 780), ("Nike Dunk Low|¥899", 600, 780)]


def test_android_texts_include_content_desc():
    assert android_texts(ANDROID)[-1] == "立即购买"


def test_ios_cards():
    assert ios_cards(IOS) == [("Timberland Martin boot|¥512", 40, 340), ("Nike Dunk Low|¥899", 230, 340)]


def test_ios_texts():
    assert ios_texts(IOS) == ["Timberland Martin boot", "¥512", "Nike Dunk Low", "¥899", "立即购买"]
