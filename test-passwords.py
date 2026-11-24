"""Exercise password setup, encrypted export/import and local unlock in the browser."""
import base64
import json
import os
from pathlib import Path
from playwright.sync_api import expect, sync_playwright
from test_support import editor_url

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    page = browser.new_page(accept_downloads=True)
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(editor_url())

    def act(name):
        page.locator(f'[data-act="{name}"]:visible').first.click()

    dialog = page.locator("dialog")
    password = dialog.locator('[name="secret"]')
    confirmation = dialog.locator('[name="confirmation"]')
    submit = dialog.get_by_role("button", name="Продолжить")
    valid = "Яблоко7!"
    act("new"); act("close-side"); act("more"); act("encrypted-export")
    for invalid, reason in [("Яблок7!","8"), ("яблоко7!","заглавная"), ("ЯБЛОКО7!","строчная"),
                            ("Яблочко!","цифра"), ("Яблоко77","спецсимвол"), ("Яблоко7 ","спецсимвол")]:
        password.fill(invalid); confirmation.fill(invalid); submit.click()
        expect(dialog.get_by_role("alert")).to_contain_text(reason)
    password.fill(valid); confirmation.fill(valid+"x"); submit.click()
    expect(dialog.get_by_role("alert")).to_have_text("Пароли не совпадают.")
    confirmation.fill(valid)
    toggle = dialog.get_by_role("checkbox")
    toggle.check()
    for field in [password, confirmation]:
        expect(field).to_have_attribute("type","text")
        expect(field).to_have_value(valid)
    toggle.uncheck()
    expect(confirmation).to_have_attribute("type","password")
    with page.expect_download() as encrypted:
        submit.click()
    backup=Path(encrypted.value.path()).read_bytes()
    def restore(payload, secret):
        page.locator("#kv2-import").set_input_files({"name":"copy.json","mimeType":"application/json","buffer":payload})
        expect(confirmation).to_have_count(0)
        password.fill(secret); submit.click()
    restore(backup, "wrong password")
    expect(page.locator("#kv2-toast")).to_contain_text("Пароль неверен или резервная копия повреждена")
    damaged = json.loads(backup)
    cipher = bytearray(base64.b64decode(damaged["data"]))
    cipher[-1] ^= 1
    damaged["data"] = base64.b64encode(cipher).decode()
    restore(json.dumps(damaged).encode(), valid)
    expect(page.locator("#kv2-toast")).to_contain_text("Пароль неверен или резервная копия повреждена")
    expect(page.locator(".node")).to_have_count(1)
    restore(backup, valid)
    expect(page.locator("#kv2-toast")).to_contain_text("Загружено")
    act("more"); act("protect-local")
    password.fill(valid); confirmation.fill(valid); submit.click()
    expect(page.locator("#kv2-toast")).to_contain_text("Карта зашифрована")
    page.reload(); expect(confirmation).to_have_count(0)
    password.fill(valid); submit.click()
    expect(page.locator(".node")).to_have_count(1)
    print("PASS: password validation, backup roundtrip, wrong password, damaged backup and local unlock")
