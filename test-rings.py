import os
from playwright.sync_api import sync_playwright, expect
from test_support import editor_url

with sync_playwright() as driver:
    browser = driver.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(editor_url())
    def setting(name):
        return page.locator(f'[data-setting="{name}"]')
    def edit(name, value):
        field = setting(name)
        field.fill(str(value))
        field.press("Tab")
    def action(name):
        page.locator(f'[data-act="{name}"]:visible').first.click()
    action("settings")
    for section in ("grid", "sectors", "rings"):
        page.locator(f'[data-appearance-section="{section}"] summary').first.click()
    for key, value in {"grid.dx": "50", "grid.dy": "50", "grid.color": "#969696", "grid.alpha": "0.5",
                       "sectors.width": "2", "sectors.alpha": "1", "rings.width": "2",
                       "radius.0": "300", "radius.1": "600", "radius.2": "900"}.items():
        expect(setting(key)).to_have_value(value)
    setting("rings.on").check()
    setting("rings.individual").check()
    edit("rings.count", 4)
    for i, radius in enumerate([65, 145, 225, 345]):
        edit("radius."+str(i), radius)
    circles = page.locator(".guide-ring")
    assert circles.evaluate_all("(els)=>els.map(e=>Number(e.getAttribute('r')))")==[65,145,225,345]
    page.locator('[data-appearance-section="ring-style-1"] summary').click()
    setting("ringStyle.1.dash").select_option("dashed")
    setting("ringStyle.1.color").fill("#336699")
    edit("ringStyle.1.width", 4)
    edit("ringStyle.1.alpha", 0)
    expect(circles.nth(0)).to_have_attribute("stroke-width", "2")
    expect(circles.nth(1)).to_have_attribute("stroke-dasharray", "8 5")
    expect(circles.nth(1)).to_have_attribute("stroke", "#336699")
    expect(circles.nth(1)).to_have_attribute("stroke-width", "4")
    expect(circles.nth(1)).to_have_attribute("stroke-opacity", "0")
    edit("radius.1", 30)
    expect(setting("radius.1")).to_have_value("145")
    edit("rings.count", 2)
    expect(circles).to_have_count(2)
    action("undo")
    expect(circles).to_have_count(4)
    page.wait_for_timeout(400)
    page.reload()
    action("settings")
    page.locator('[data-appearance-section="rings"] summary').first.click()
    expect(setting("radius.3")).to_have_value("345")
    expect(circles.nth(1)).to_have_attribute("stroke-width", "4")
    expect(circles.nth(1)).to_have_attribute("stroke-opacity", "0")
    page.locator('[data-appearance-section="ring-style-1"] summary').click()
    setting("ringStyle.1.dash").select_option("solid")
    assert circles.nth(1).get_attribute("stroke-dasharray") is None
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
    print("PASS: guide defaults, per-ring styles, exact radii, undo, persistence and grouping")
