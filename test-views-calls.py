import json,math,os
from playwright.sync_api import sync_playwright,expect
from test_support import editor_url

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    p=browser.new_page(viewport={"width":1400,"height":900})
    p.on("dialog",lambda d:d.accept())
    p.goto(editor_url())
    p.wait_for_function("!document.querySelector('#kv2').inert")
    def act(a): p.locator(f'[data-act="{a}"]:visible').first.click()
    def edit(sel,value):
        field=p.locator(sel)
        field.fill(str(value));field.press("Tab")
    source={"version":3,"people":[{"id":str(i),"name":"Узел "+str(i),"phone":"+7900000000"+str(i),"x":50*i,"y":40} for i in range(5)],"links":[]}
    p.locator('#kv2-import').set_input_files({"name":"map.json","mimeType":"application/json","buffer":json.dumps(source).encode()})
    expect(p.locator(".node")).to_have_count(5)
    act("settings")
    for section in ["rings","views"]:
        p.locator(f'[data-appearance-section="{section}"] summary').first.click()
    p.locator('[data-setting="rings.on"]').check()
    p.locator('[data-setting="rings.individual"]').check()
    edit('[data-setting="rings.count"]',4)
    p.locator('[data-appearance-section="ring-style-0"] summary').click()
    p.locator('[data-setting="ringStyle.0.dash"]').select_option("dashed")
    edit('[data-setting="ringName.0"]',"Близкий круг")
    expect(p.locator(".ring-name")).to_have_text("Близкий круг")
    expect(p.get_by_role("button",name="Сохранить тему",exact=True)).to_be_visible()
    p.locator("#view-name").fill("Семья");act("save-view")
    p.locator('[data-setting="ringStyle.0.dash"]').select_option("solid")
    edit('[data-setting="ringName.0"]',"Коллеги")
    p.locator("#view-name").fill("Работа");act("save-view")
    p.locator("#view-list").select_option(label="Семья");act("load-view")
    expect(p.locator(".ring-name")).to_have_text("Близкий круг")
    expect(p.locator(".guide-ring").first).to_have_attribute("stroke-dasharray","8 5")
    act("close-right");act("group")
    def csv(text):
        p.locator("#call-csv").set_input_files({"name":"totals.csv","mimeType":"text/csv","buffer":text.encode()})
    csv("phone,count\n+79000000000,30\n+79000000001,10\n+79000000002,10\n+79000000003,0")
    act("apply-group");act("close-right")
    values=p.locator(".node").evaluate_all("(els)=>Object.fromEntries(els.map(e=>{const m=e.transform.baseVal.getItem(0).matrix;return [e.dataset.person,Math.round(Math.hypot(m.e,m.f))]}))")
    assert values['0']<values['1']==values['2']<values['3']==values['4'],values
    p.wait_for_timeout(500);p.reload()
    act("settings");p.locator('[data-appearance-section="views"] summary').click();expect(p.locator("#view-list option")).to_have_count(2)
    p.locator("#view-list").select_option(label="Работа");act("load-view")
    expect(p.locator("#view-list")).to_have_value("1")
    expect(p.locator(".ring-name")).to_have_text("Коллеги")
    assert p.locator(".guide-ring").first.get_attribute("stroke-dasharray") is None
    print("PASS: ring names and saved layouts restored; counts 30/10/10/0/unknown mapped to",values)
    act("close-right");act("group")
    csv("phone,count,start,end\n0079000000000,3,2026-02-01,2026-02-28")
    act("apply-group");act("close-right");act("directory")
    p.locator("#directory-query").fill("Узел 0");p.locator("#directory-query").press("Enter")
    expect(p.locator("#kv2-side-body")).to_contain_text("2026-02-01 — 2026-02-28")
    expect(p.locator("#kv2-side-body")).to_contain_text("CSV")
    p.keyboard.press("Escape");act("close-right");act("group")
    csv("phone,count,start,end\n+79000000000,99,2026-02-01,2026-02-31")
    expect(p.locator("#kv2-toast")).to_contain_text("Проверьте период")
    print("PASS: explicit CSV period, international prefix equivalence, invalid calendar dates")
