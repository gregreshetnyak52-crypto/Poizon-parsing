"""Save a screenshot + UI hierarchy of the current emulator screen (to tune selectors)."""
import sys
import uiautomator2 as u2

d = u2.connect(sys.argv[1] if len(sys.argv) > 1 else None)
d.screenshot("out/screen.png")
open("out/hierarchy.xml", "w", encoding="utf-8").write(d.dump_hierarchy())
print("saved out/screen.png, out/hierarchy.xml")
