"""iOS (Appium/XCUITest) helpers: read on-screen texts from page source."""
import xml.etree.ElementTree as ET


def texts_from_source(xml_source):
    """Visible texts in document order. XCUITest exposes them as label/value/name."""
    out = []
    for n in ET.fromstring(xml_source).iter():
        if n.get("visible") == "false":
            continue
        t = n.get("label") or n.get("value") or n.get("name")
        if t and n.tag in ("XCUIElementTypeStaticText", "XCUIElementTypeButton", "XCUIElementTypeOther",
                           "XCUIElementTypeCell"):
            if not out or out[-1] != t:
                out.append(t)
    return out
