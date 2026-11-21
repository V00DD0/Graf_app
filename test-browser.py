from playwright.sync_api import sync_playwright
from pathlib import Path
import json,time,os,shutil,tempfile
os.chdir(Path(__file__).resolve().parent)
tmp=tempfile.TemporaryDirectory()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),args=['--no-sandbox'])
 p=b.new_page(viewport={'width':1280,'height':800},accept_downloads=True)
 errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.accept())
 p.goto(Path('Karta-2.1.html').resolve().as_uri());p.wait_for_function('!document.querySelector("#kv2").inert')
 def act(k):p.locator('[data-act="'+k+'"]:visible').first.click()
 def person():p.locator('.node text',has_text='Кузнецова Анна').first.click()
 def state():
  p.wait_for_timeout(300)
  return p.evaluate("""async () => {
   const db=await new Promise(resolve=>{const req=indexedDB.open('karta-svyazey-2.1');req.onsuccess=()=>resolve(req.result)});
   const value=await new Promise(resolve=>{const req=db.transaction('graphs').objectStore('graphs').get('current');req.onsuccess=()=>resolve(req.result)});
   db.close();return JSON.parse(value)
  }""")
 act('more');act('demo');act('close-right');person()
 assert p.locator('[data-act=edit-profile]').is_visible()
 act('edit-profile');f=p.locator('[data-person-field=name]');f.fill('Черновик');f.press('Tab')
 assert state()['people'][0]['name']=='Анна'
 act('cancel-profile');assert 'Черновик' not in p.locator('#kv2-side-body').inner_text()
 act('edit-profile');p.locator('[data-person-field=name]').fill('Проверка');p.locator('[data-person-field=pinned]').check();act('save-profile')
 assert state()['people'][0]['name']=='Проверка' and state()['people'][0]['pinned']
 act('close-side');p.reload();p.wait_for_function('!document.querySelector("#kv2").inert');assert 'Проверка' in p.locator('svg').text_content()
 act('group');act('preview-group');act('cancel-group');act('preview-group');act('apply-group')
 assert state()['people'][0]['x']==0
 act('close-right');act('more');act('checks')
 print('selfcheck',p.locator('#kv2-toast').inner_text())
 before=state()
 def upload(raw):
  p.locator('#kv2-import').set_input_files({'name':'graph.json','mimeType':'application/json','buffer':json.dumps(raw).encode()})
  p.wait_for_timeout(120)
 for broken in ['coordinates','link','duplicate']:
  v=json.loads(json.dumps(before))
  if broken=='coordinates':del v['people'][0]['x']
  elif broken=='link':v['links'][0]['a']='missing'
  else:v['people'][1]['id']=v['people'][0]['id']
  upload(v);assert state()==before
 with p.expect_download() as down:act('html')
 html_copy=Path(tmp.name)/'roundtrip.html';down.value.save_as(html_copy)
 q=b.new_page();q.goto(html_copy.as_uri());q.locator('[data-act=more]').click()
 with q.expect_download() as again:q.locator('[data-act=html]').click()
 print('second export',again.value.suggested_filename)
 v={'version':1,'nodes':[{'id':i,'x':x,'y':0,'profile':{'first':i,'profession':'Мастер'},'family':(['b'] if i=='a' else [])} for i,x in [('a',0),('b',100)]],'edges':[{'id':'w','from':'a','to':'b','style':'wave','end':True}],'texts':[]}
 upload(v);s=state();assert len(s['links'])==2 and s['people'][0]['job']=='Мастер' and s['links'][0]['style']=='curve'
 for count in [100,1000,5000]:
  v={'version':2,'people':[{'id':str(i),'x':(i%100)*62,'y':(i//100)*62} for i in range(count)],'links':[{'id':'e'+str(i),'a':str(i-1),'b':str(i)} for i in range(1,count)]}
  t=time.monotonic();upload(v);assert len(state()['people'])==count
  print(count,'import+read ms',round((time.monotonic()-t)*1000),'rendered',p.locator('.node').count())
 assert not errors,errors
 print('PASS')
