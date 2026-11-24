"""Exercise installation-wide themes and per-map guides through the editor UI."""
import os
from playwright.sync_api import sync_playwright, expect
from test_support import editor_url

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    context = browser.new_context(viewport={"width":1280, "height":800})
    page = context.new_page()
    url = editor_url()
    def settings(p):
        p.locator('[data-act="settings"]').click()
    page.goto(url)
    settings(page)
    canvas = page.locator("#kv2-view")
    expect(canvas).to_have_css("background-color","rgb(255, 255, 255)")
    for name in ["Малахит","Бордо","Слоновая кость","Ночной сапфир"]:
        preset=page.get_by_role("button",name=name,exact=True)
        preset.click()
        expect(preset).to_have_attribute("aria-pressed","true")
    base=page.get_by_label("Основной цвет",exact=True)
    accent=page.get_by_label("Акцентный цвет",exact=True)
    expect(base).to_have_value("#192a43")
    expect(page.locator(".bar")).to_have_css("background-color","rgb(25, 42, 67)")
    expect(canvas).to_have_css("background-color","rgb(255, 255, 255)")
    for key in ("grid","rings","sectors"):
        page.locator(f'[data-appearance-section="{key}"] summary').click()
        page.locator(f'[data-setting="{key}.on"]').check()
    other=context.new_page()
    other.goto(url)
    settings(other)
    base.fill("#234567")
    accent.fill("#ffffff")
    expect(page.locator('.theme-choice[aria-pressed=true]')).to_have_count(0)
    expect(other.get_by_label("Основной цвет",exact=True)).to_have_value("#234567")
    expect(page.locator(".primary").first).to_have_css("color","rgb(0, 0, 0)")
    page.get_by_label("Анимация панелей").uncheck()
    page.reload()
    settings(page)
    expect(base).to_have_value("#234567")
    expect(accent).to_have_value("#ffffff")
    expect(page.get_by_label("Анимация панелей")).not_to_be_checked()
    expect(page.locator("#kv2-right")).to_have_css("animation-name","none")
    for key in ("grid","rings","sectors"):
        expect(page.locator(f'[data-setting="{key}.on"]')).to_be_checked()
    page.set_viewport_size({"width":390,"height":844})
    page.emulate_media(reduced_motion="reduce")
    page.get_by_label("Анимация панелей").check()
    expect(page.locator("#kv2-right")).to_have_css("animation-name","none")
    page.get_by_role("button",name="Малахит",exact=True).click()
    assert page.locator("#kv2-right").evaluate("p=>p.scrollWidth<=p.clientWidth")
    if os.environ.get("THEME_SCREENSHOT"):
        page.screenshot(path=os.environ["THEME_SCREENSHOT"])
    print("PASS: four presets, custom colors, contrast, shared preference, reload, canvas guides and reduced motion on mobile")
