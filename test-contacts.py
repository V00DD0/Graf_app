"""Exercise selection across pages and searches, cancellation, and one-step undo."""
import json
import os
from playwright.sync_api import expect, sync_playwright
from test_support import editor_url

contacts = [{"name": f"Тест {i:03d}", "phone": f"+1202555{i:04d}"} for i in range(202)]
contacts += [{"name": "Повтор", "phone": contacts[0]["phone"]}, {"name": "Без номера", "phone": ""}]

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    page = browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    page.add_init_script("""(rows => {
      const fetch = window.fetch;
      window.fetch = (...args) => args[0] === '/contacts' ? Promise.resolve(new Response(JSON.stringify(rows))) : fetch(...args);
      window.KartaFiles = {pickPhone(){}, normalizePhone(value){return value}, pickContacts(){window.kartaContactsReady(null)}};
    })(""" + json.dumps(contacts, ensure_ascii=False) + ")")
    page.goto(editor_url())
    def action(name):
        page.locator(f'[data-act="{name}"]:visible').first.tap()
    def open_picker():
        action("more")
        action("pick-contacts")
        expect(page.get_by_role("dialog", name="Добавить из контактов")).to_be_visible()
    count = page.locator("#contacts-count")
    search = page.locator("#contacts-search")
    status = page.locator("#kv2-status")
    open_picker()
    page.get_by_label("Тест 000", exact=False).check()
    page.get_by_role("button", name="Вперёд").tap()
    page.get_by_label("Тест 100", exact=False).check()
    search.fill("Без номера")
    page.get_by_label("Без номера", exact=True).check()
    expect(count).to_have_text("Выбрано: 3 из 204")
    page.get_by_role("button", name="Добавить", exact=True).tap()
    expect(status).to_contain_text("3 людей")
    open_picker()
    page.get_by_role("button", name="Выбрать все").tap()
    page.get_by_role("button", name="Отмена", exact=True).tap()
    expect(status).to_contain_text("3 людей")
    action("close-right")
    action("undo")
    expect(status).to_contain_text("0 людей")
    open_picker()
    search.fill("Тест 000")
    page.get_by_role("button", name="Выбрать все").tap()
    expect(count).to_have_text("Выбрано: 204 из 204")
    page.get_by_role("button", name="Снять выбор").tap()
    expect(page.get_by_role("button", name="Добавить", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Выбрать все").tap()
    page.get_by_role("button", name="Добавить", exact=True).tap()
    expect(status).to_contain_text("203 людей")
    expect(page.locator("#kv2-toast")).to_contain_text("Пропущено повторов: 1")
    expect(page.locator("#save-state")).to_have_text("Сохранено")
    print("PASS: paginated contacts, selection across searches, select all, clear, cancel, deduplication and undo")
