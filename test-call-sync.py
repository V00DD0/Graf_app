"""Check selective call totals, cancel, and bulk import with the Android bridge mocked."""
import json
import os
from playwright.sync_api import expect, sync_playwright
from test_support import editor_url

numbers = {"Аня": "+12025550101", "Борис": "+12025550102", "Вера": "+12025550103", "Глеб": "+12025550104"}
people = [{"id": n, "name": n, "phone": phone, "x": 120*i, "y": 0,
           "calls": {"phone": phone, "count": 8+i, "asOf": "2026-11-01", "source": "csv"}}
          for i, (n, phone) in enumerate(list(numbers.items())[:3])]
phonebook = [{"name": n, "phone": numbers[n]} for n in ("Аня", "Глеб")]

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM"))
    page = browser.new_page(viewport={"width": 900, "height": 800})
    page.add_init_script("""(book => {
      const fetch = window.fetch;
      window.fetch = (...args) => args[0] === '/contacts' ? Promise.resolve(new Response(JSON.stringify(book))) : fetch(...args);
      window.qaRequests = [];
      window.KartaFiles = {
        pickPhone(){}, normalizePhone(value){return value}, pickContacts(){window.kartaContactsReady(null)},
        analyzeCalls(token,input){
          const rows=JSON.parse(input);window.qaRequests.push(rows.map(row=>row.phone));
          const counts=Object.fromEntries(rows.map(row=>[row.id,row.phone.endsWith('101')?2:0]));
          queueMicrotask(()=>window.kartaCallTotals(token,counts,'2026-08-26','2026-11-24'));
        }
      };
    })(""" + json.dumps(phonebook, ensure_ascii=False) + ")")
    page.goto(editor_url())
    page.locator('#kv2-import').set_input_files({"name":"map.json", "mimeType":"application/json", "buffer":json.dumps({"version":3,"people":people,"links":[]}).encode()})
    expect(page.locator('.node')).to_have_count(3)
    def action(name):
        page.locator(f'[data-act="{name}"]:visible').first.click()
    def sync_picker():
        action("group")
        action("refresh-calls")
        expect(page.get_by_role("dialog", name="Синхронизировать журнал вызовов")).to_be_visible()
    def totals():
        expect(page.locator('#save-state')).to_have_text('Сохранено')
        return page.evaluate("""async () => {
          const db=await new Promise(resolve=>{const r=indexedDB.open('karta-standalone-2.5');r.onsuccess=()=>resolve(r.result)});
          const raw=await new Promise(resolve=>{const r=db.transaction('graphs').objectStore('graphs').get('current');r.onsuccess=()=>resolve(r.result)});
          db.close();return Object.fromEntries(JSON.parse(raw).people.map(n=>[n.name,n.calls?.count]));
        }""")
    sync_picker()
    page.get_by_role('button', name='Выбрать все').click()
    page.get_by_role('button', name='Подсчитать').click()
    expect(page.locator('dialog li')).to_have_count(3)
    assert page.evaluate('window.qaRequests[0]') == list(numbers.values())[:3]
    page.get_by_role('button', name='Отмена', exact=True).click()
    assert totals() == {"Аня":8,"Борис":9,"Вера":10}
    sync_picker()
    page.get_by_role('dialog').get_by_role('checkbox', name='Аня').check()
    page.get_by_role('dialog').get_by_role('checkbox', name='Борис').check()
    page.get_by_role('button', name='Подсчитать').click()
    expect(page.locator('dialog li')).to_have_text(['Аня — 2','Борис — 0'])
    page.locator('#accept-totals').click()
    expect(page.locator('[data-act=apply-group]')).to_be_visible()
    assert totals() == {"Аня":2,"Борис":0,"Вера":10}
    action('more')
    action('pick-calls')
    page.get_by_role('button', name='Выбрать все').click()
    page.get_by_role('button', name='Добавить и подсчитать').click()
    expect(page.locator('dialog li')).to_have_text(['Аня — 2','Глеб — 0'])
    page.locator('#accept-totals').click()
    expect(page.locator('[data-act=apply-group]')).to_be_visible()
    assert totals() == {"Аня":2,"Борис":0,"Вера":10,"Глеб":0}
    print('PASS: select all, cancellation, scoped updates, zero calls and bulk phonebook sync')
