import sys
from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "android"))
sys.modules.setdefault("uiautomator2", type(sys)("uiautomator2"))
spec = importlib.util.spec_from_file_location("android_auto", ROOT / "android" / "auto.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # unique name: ios/auto.py is also called auto
list_cards = mod.list_cards

SRC = """<hierarchy><node text="" bounds="[0,0][1080,2400]">
<node text="" bounds="[0,500][540,900]">
<node text="Timberland Martin boot" bounds="[10,700][500,740]"/>
<node text="¥512" bounds="[10,760][110,800]"/></node>
<node text="" bounds="[540,500][1080,900]">
<node text="Nike Dunk Low" bounds="[550,700][1000,740]"/>
<node text="¥899" bounds="[550,760][650,800]"/></node></node></hierarchy>"""


def test_cards():
    assert list_cards(SRC) == [("Timberland Martin boot|¥512", 60, 780), ("Nike Dunk Low|¥899", 600, 780)]
