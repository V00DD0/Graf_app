"""Measure wall-clock UI operations on synthetic graphs, including persisted edits."""
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    for size in (100, 1000, 5000):
        p = browser.new_page(viewport={"width":1280, "height":800})
        p.goto(Path("Karta-2.1.html").resolve().as_uri())
        p.wait_for_function("!document.querySelector('#kv2').inert")
        people = [dict(id=str(i), name=f"Человек {i}", x=i%100*65, y=i//100*65,
                       category="Автоматически") for i in range(size)]
        for n in people[::25]:
            n["docs"] = [{"id":"test","name":"notes.txt","data":"data:text/plain;base64,"+"QUJD"*1024}]
        links=[dict(id=f"e{i}",a=str(i-1),b=str(i),kind="work") for i in range(1,size)]
        def now(): return time.perf_counter()
        start=now()
        p.locator("#kv2-import").set_input_files({"name":"sample.json","mimeType":"application/json","buffer":json.dumps(dict(version=3,people=people,links=links)).encode()})
        p.locator(".node").first.wait_for()
        imported=now()
        p.locator('[data-act=filters]').click()
        p.locator('[data-act=close-right]').click()
        filters=now()
        node=p.locator('[data-person="0"].node').bounding_box()
        x,y=node["x"]+node["width"]/2,node["y"]+12
        p.mouse.move(x,y);p.mouse.down();p.mouse.move(x+55,y+30,steps=5);p.mouse.up()
        p.wait_for_function("""async()=>{const db=await new Promise(r=>{const q=indexedDB.open('karta-svyazey-2.1');q.onsuccess=()=>r(q.result)});
          try{return await new Promise(r=>{const q=db.transaction('graphs').objectStore('graphs').get('current');q.onsuccess=()=>r(JSON.parse(q.result).people[0].x!==0)})}finally{db.close()}}""")
        done=now()
        print(size, "import/filter/drag+save ms",*[round((b-a)*1000) for a,b in [(start,imported),(imported,filters),(filters,done)]],flush=True)
        p.close()
