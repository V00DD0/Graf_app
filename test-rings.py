import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as driver:
    browser = driver.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(Path(__file__).with_name("Karta-2.1.html").resolve().as_uri())
    def setting(name):
        return page.locator(f'[data-setting="{name}"]')
    def edit(name, value):
        field = setting(name)
        field.fill(str(value))
        field.press("Tab")
    def action(name):
        page.locator(f'[data-act="{name}"]:visible').first.click()
    action("settings")
    setting("rings.on").check()
    setting("rings.individual").check()
    edit("rings.count", 4)
    for i, radius in enumerate([65, 145, 225, 345]):
        edit("radius."+str(i), radius)
    circles = page.locator(".guide-ring")
    assert circles.evaluate_all("(els)=>els.map(e=>Number(e.getAttribute('r')))")==[65,145,225,345]
    edit("radius.1", 30)
    expect(setting("radius.1")).to_have_value("145")
    edit("rings.count", 2)
    expect(circles).to_have_count(2)
    action("undo")
    expect(circles).to_have_count(4)
    page.wait_for_timeout(400)
    page.reload()
    action("settings")
    expect(setting("radius.3")).to_have_value("345")
    setting("rings.individual").uncheck()
    expect(setting("rings.step")).to_be_visible()
    setting("rings.individual").check()
    expect(setting("radius.0")).to_have_value("65")
    action("close-right")
    action("more")
    action("demo")
    action("close-right")
    action("group")
    setting("rings.individual").check()
    edit("rings.count",1)
    edit("radius.0",95)
    action("preview-group")
    action("apply-group")
    coords=page.locator(".node").evaluate_all("(els)=>els.map(e=>{const m=e.transform.baseVal.getItem(0).matrix;return Math.hypot(m.e,m.f)})")
    assert any(abs(x-95)<.01 for x in coords),coords
    print("PASS: exact radii, invalid input, count, undo, persistence, mode switch, grouping")
