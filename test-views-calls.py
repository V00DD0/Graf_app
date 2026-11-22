import json,math,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    p=browser.new_page(viewport={"width":1400,"height":900})
    p.on("dialog",lambda d:d.accept())
    p.goto(Path("Karta-2.1.html").resolve().as_uri())
    p.wait_for_function("!document.querySelector('#kv2').inert")
    def act(a): p.locator(f'[data-act="{a}"]:visible').first.click()
    def edit(sel,value):
        field=p.locator(sel)
        field.fill(str(value));field.press("Tab")
    source={"version":3,"people":[{"id":str(i),"name":"Узел "+str(i),"phone":"+7900000000"+str(i),"x":50*i,"y":40} for i in range(5)],"links":[]}
    p.locator('#kv2-import').set_input_files({"name":"map.json","mimeType":"application/json","buffer":json.dumps(source).encode()})
    expect(p.locator(".node")).to_have_count(5)
    act("settings")
    p.locator('[data-setting="rings.on"]').check()
    p.locator('[data-setting="rings.individual"]').check()
    edit('[data-setting="rings.count"]',4)
    edit('[data-setting="ringName.0"]',"Близкий круг")
    expect(p.locator(".ring-name")).to_have_text("Близкий круг")
    p.locator("#view-name").fill("Семья");act("save-view")
    edit('[data-setting="ringName.0"]',"Коллеги")
    p.locator("#view-name").fill("Работа");act("save-view")
    p.locator("#view-list").select_option(label="Семья");act("load-view")
    expect(p.locator(".ring-name")).to_have_text("Близкий круг")
    act("close-right");act("group")
    def csv(text):
        p.locator("#call-csv").set_input_files({"name":"totals.csv","mimeType":"text/csv","buffer":text.encode()})
    csv("phone,count\n+79000000000,30\n+79000000001,10\n+79000000002,10\n+79000000003,0")
    act("apply-group");act("close-right")
    values=p.locator(".node").evaluate_all("(els)=>Object.fromEntries(els.map(e=>{const m=e.transform.baseVal.getItem(0).matrix;return [e.dataset.person,Math.round(Math.hypot(m.e,m.f))]}))")
    assert values['0']<values['1']==values['2']<values['3']==values['4'],values
    p.wait_for_timeout(500);p.reload()
    act("settings");expect(p.locator("#view-list option")).to_have_count(2)
    p.locator("#view-list").select_option(label="Работа");act("load-view")
    expect(p.locator(".ring-name")).to_have_text("Коллеги")
    print("PASS: ring names and saved layouts restored; counts 30/10/10/0/unknown mapped to",values)
