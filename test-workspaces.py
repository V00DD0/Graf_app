"""Exercise real editor controls, two browser windows and IndexedDB."""
import json
import os
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    ctx = browser.new_context(accept_downloads=True, viewport={"width": 1050, "height": 760})
    page = ctx.new_page()
    url = Path("Karta-2.1.html").resolve().as_uri()
    page.on("dialog", lambda d: d.accept("Коллеги") if d.type == "prompt" else d.accept())
    def act(name):
        page.locator(f'[data-act="{name}"]:visible').first.click()
    def tab(name):
        page.get_by_role("button", name=name, exact=True).click()
        expect(page.locator('[data-map][aria-pressed=true]')).to_have_text(name)
    page.goto(url)
    act("new"); act("close-side")
    act("new-map")
    expect(page.locator('[aria-pressed=true][data-map]')).to_have_text("Коллеги")
    expect(page.locator(".node")).to_have_count(0)
    act("new"); act("close-side"); act("new"); act("close-side")
    tab("Основная карта"); expect(page.locator(".node")).to_have_count(1)
    tab("Коллеги"); act("undo"); expect(page.locator(".node")).to_have_count(1)
    act("redo"); expect(page.locator(".node")).to_have_count(2)
    page.reload()
    expect(page.locator('[data-map][aria-pressed=true]')).to_have_text("Коллеги")
    act("close-map"); expect(page.locator(".node")).to_have_count(1)
    page.locator("#closed-maps").select_option(label="Коллеги")
    expect(page.locator(".node")).to_have_count(2)
    act("directory"); page.locator("#directory-query").fill("Новый")
    page.locator("#directory-query").press("Enter")
    expect(page.locator("#kv2-side-body")).to_contain_text("Новый человек")
    page.keyboard.press("Escape"); expect(page.locator("#directory-query")).to_be_focused()
    act("close-right")
    tab("Основная карта")
    second = ctx.new_page(); second.goto(url)
    second.wait_for_function("!document.querySelector('#kv2').inert")
    act("new"); act("close-side"); expect(page.locator("#save-state")).to_have_text("Сохранено")
    second.locator('[data-act="new"]').first.click()
    expect(second.locator("#rescue")).to_be_visible()
    with second.expect_download() as saved:
        second.locator("#rescue").click()
    assert len(json.loads(Path(saved.value.path()).read_text())["people"]) == 2
    second.close()
    page.set_viewport_size({"width":390,"height":844})
    tab("Коллеги")
    expect(page.locator(".node")).to_have_count(2)
    print("PASS: separate graphs, reload, per-tab undo/redo, search focus, mobile switching, conflict recovery")
