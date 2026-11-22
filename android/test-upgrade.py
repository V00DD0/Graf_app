"""Install the distributed APK over the original 2.2 APK on the disposable emulator."""
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

package = "local.karta.app"
def adb(*args):
    return subprocess.check_output(["adb", *args], text=True, timeout=40)
def start():
    result=adb("shell","am","start","-W","-n",package+"/local.karta.app.MainActivity")
    if "Error" in result: raise AssertionError(result)
    time.sleep(2)
def find(label):
    limit=time.monotonic()+100
    while time.monotonic()<limit:
        try:
            adb("shell","rm","-f","/sdcard/karta-upgrade.xml")
            adb("shell","uiautomator","dump","/sdcard/karta-upgrade.xml")
            root = ET.fromstring(adb("shell","cat","/sdcard/karta-upgrade.xml"))
        except (subprocess.SubprocessError,ET.ParseError):
            time.sleep(1)
            continue
        for node in root.iter("node"):
            if any(label in node.get(k,"") for k in ("text","content-desc")):
                return node
        time.sleep(.3)
    raise AssertionError("Expected editor control: "+label)
def tap(node):
    left, top, right, bottom = map(int,re.findall(r"\d+",node.attrib["bounds"]))
    adb("shell","input","tap",str((left+right)//2),str((top+bottom)//2))

if __name__ == "__main__":
    downloads=Path(__file__).resolve().parents[1]/"downloads"
    adb("install","--no-incremental","-r",str(downloads/"Karta-2.2-test.apk"))
    start()
    tap(find("＋ Человек"))
    find("1/1 людей")
    time.sleep(1)
    adb("shell","am","force-stop",package)
    adb("install","--no-incremental","-r",str(downloads/"Karta-2.4-test.apk"))
    start()
    find("1/1 людей")
    print("PASS: published 2.2 → 2.4 in-place APK update retained the original graph")
