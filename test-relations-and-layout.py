"""Check ancestry, undo and filtered grouping through the editor on a touch screen."""
import json
import os
from playwright.sync_api import expect, sync_playwright
from test_support import editor_url


def graph(page):
    return page.evaluate("""async () => {
      const db=await new Promise(resolve=>{
        const q=indexedDB.open('karta-svyazey-2.1');q.onsuccess=()=>resolve(q.result);
      });
      const transaction=db.transaction('graphs');
      const q=transaction.objectStore('graphs').get('current');
      return await new Promise(resolve=>{
        transaction.oncomplete=()=>{db.close();resolve(JSON.parse(q.result));};
      });
    }""")


with sync_playwright() as driver:
    browser = driver.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    page = browser.new_page(viewport={"width": 412, "height": 850}, has_touch=True, is_mobile=True)
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(editor_url())
    page.wait_for_function("!document.querySelector('#kv2').inert")

    def action(name):
        page.locator(f'[data-act="{name}"]:visible').first.tap()

    people = [
        {"id": "p", "name": "Пётр", "sex": "m", "x": -80, "y": -70, "category": "Семья"},
        {"id": "a", "name": "Анна", "sex": "f", "x": -70, "y": 40, "category": "Семья"},
        {"id": "b", "name": "Борис", "sex": "m", "x": 70, "y": 40, "category": "Семья"},
        {"id": "c", "name": "Катя", "sex": "f", "x": 80, "y": -70, "category": "Друзья"},
    ]
    links = [
        {"id": "pa", "a": "p", "b": "a", "kind": "parent"},
        {"id": "pb", "a": "p", "b": "b", "kind": "parent"},
        {"id": "ac", "a": "a", "b": "c", "kind": "parent"},
    ]
    page.locator("#kv2-import").set_input_files({"name": "map.json", "mimeType": "application/json",
                                               "buffer": json.dumps({"version": 3, "people": people, "links": links}).encode()})
    expect(page.locator(".node")).to_have_count(4)
    page.locator('.node[data-person="p"] circle').first.tap()
    expect(page.locator("#kv2-side-body")).to_contain_text("дочь")
    action("edit-profile")
    page.locator("#kv2-family-other").select_option("c")
    page.locator("#kv2-family-role").select_option("mother")
    action("add-family")
    expect(page.locator("#kv2-toast")).to_contain_text("цикл родителей и детей")
    action("cancel-profile")
    action("close-side")
    action("path")
    page.locator("#kv2-path-family").check()
    for source, target, relation in [("a", "b", "брат"), ("b", "a", "сестра"), ("c", "b", "дядя"), ("b", "c", "племянница")]:
        page.locator("#kv2-path-a").select_option(source)
        page.locator("#kv2-path-b").select_option(target)
        action("find-path")
        expect(page.locator("#kv2-path-result")).to_contain_text(f"Определение: {relation}.")
    action("close-right")
    action("filters")
    page.locator('[data-filter="category"]').select_option("Семья")
    action("close-right")
    action("group")
    page.locator('[data-group="visibleOnly"]').check()
    action("preview-group")
    action("cancel-group")
    before = graph(page)
    action("preview-group")
    action("apply-group")
    expect(page.locator("#save-state")).to_have_text("Сохранено")
    after = graph(page)
    assert before["people"][3] == after["people"][3], "Filtered-out person moved"
    assert before["links"] == after["links"], "Grouping changed relations"
    assert before["people"][0]["x"] != after["people"][0]["x"], "Grouping did not move visible people"
    action("close-right")
    action("undo")
    expect(page.locator("#save-state")).to_have_text("Сохранено")
    assert graph(page)["people"] == before["people"]
    print("PASS: touch controls, inferred relations, ancestry cycles, filtered grouping and undo")
