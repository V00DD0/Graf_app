function chooseContacts(rows,title="Добавить из контактов",confirmLabel="Добавить"){
 const dialog=document.createElement("dialog"),selected=new Set(),pageSize=100;
 dialog.className="contacts-picker";
 dialog.setAttribute("aria-labelledby","contacts-title");
 dialog.innerHTML=`<form method="dialog">
  <h3 id="contacts-title">${h(title)}</h3>
  <label>Поиск по имени или номеру<input type="search" id="contacts-search"></label>
  <div class="contacts-controls"><button type="button" id="contacts-all" autofocus>Выбрать все</button><button type="button" id="contacts-clear">Снять выбор</button></div>
  <div role="status" id="contacts-count"></div>
  <div class="contacts-list" id="contacts-list"></div>
  <div class="contacts-controls" id="contacts-pages"><button type="button" id="contacts-prev">Назад</button><span id="contacts-page"></span><button type="button" id="contacts-next">Вперёд</button></div>
  <div class="contacts-controls"><button value="add" id="contacts-add">${h(confirmLabel)}</button><button value="cancel">Отмена</button></div>
 </form>`;
 const el=id=>dialog.querySelector("#"+id),list=el("contacts-list");
 let results=rows,page=0;
 function updateCount(){
  el("contacts-count").textContent=`Выбрано: ${selected.size} из ${rows.length}`;
  el("contacts-add").disabled=!selected.size;
  el("contacts-clear").disabled=!selected.size;
  el("contacts-all").disabled=selected.size===rows.length;
 }
 function renderPage(){
  const count=Math.max(1,Math.ceil(results.length/pageSize));
  el("contacts-pages").hidden=count===1;
  el("contacts-prev").disabled=page===0;
  el("contacts-next").disabled=page+1===count;
  el("contacts-page").textContent=`${page+1} / ${count}`;
  list.replaceChildren();
  if(!results.length)list.textContent="Контакты не найдены";
  for(const row of results.slice(page*pageSize,(page+1)*pageSize)){
   const label=document.createElement("label"),input=document.createElement("input"),info=document.createElement("span");
   input.type="checkbox";input.checked=selected.has(row);
   input.onchange=()=>{if(input.checked)selected.add(row);else selected.delete(row);updateCount();};
   info.textContent=row.name||row.phone;
   if(row.name&&row.phone){const number=document.createElement("small");number.textContent=row.phone;info.append(number);}
   label.append(input,info);list.append(label);
  }
  list.scrollTop=0;
  updateCount();
 }
 el("contacts-search").oninput=e=>{
  const query=e.target.value.trim().toLocaleLowerCase("ru"),digits=query.replace(/\D/g,"");
  results=rows.filter(row=>row.name.toLocaleLowerCase("ru").includes(query)||row.phone.includes(query)||
   (digits&&/^[+\d ()-]+$/.test(query)&&row.phone.includes(digits)));
  page=0;renderPage();
 };
 el("contacts-all").onclick=()=>{for(const row of rows)selected.add(row);renderPage();};
 el("contacts-clear").onclick=()=>{selected.clear();renderPage();};
 el("contacts-prev").onclick=()=>{page--;renderPage();};
 el("contacts-next").onclick=()=>{page++;renderPage();};
 renderPage();
 return new Promise(resolve=>{
  dialog.onclose=()=>{dialog.remove();resolve(dialog.returnValue==="add"?rows.filter(row=>selected.has(row)):[]);};
  document.body.append(dialog);dialog.showModal();
 });
}
function addContacts(rows){
 const phones=new Set(),names=new Set(),add=[];
 const nameKey=name=>name.trim().replace(/\s+/g," ").toLocaleLowerCase("ru");
 for(const n of data.people){
  const key=phoneKey(n.phone);
  if(key)phones.add(key);else names.add(nameKey([n.surname,n.name,n.middle].filter(Boolean).join(" ")));
 }
 const capacity=10000-data.people.length;
 let duplicates=0,overLimit=0;
 for(const row of rows){
  const phone=phoneKey(row.phone),name=row.name.trim(),key=nameKey(name),seen=phone?phones:names;
  if(seen.has(phone||key)){duplicates++;continue;}
  if(add.length>=capacity){overLimit++;continue;}
  seen.add(phone||key);add.push({name:name||phone,phone});
 }
 if(add.length){
  const columns=Math.ceil(Math.sqrt(add.length)),spacing=160,span=columns*spacing;
  const right=Math.max(0,...data.people.map(n=>n.x)),left=Math.min(0,...data.people.map(n=>n.x));
  const startX=!data.people.length?-span/2:right+span<=100000?right+spacing:Math.max(-100000,left-span);
  remember(`Добавлены контакты (${add.length})`);
  add.forEach(({name,phone},i)=>{
   const n=person(startX+(i%columns)*spacing,Math.floor(i/columns)*90);
   n.name=name;n.phone=phone;data.people.push(n);
  });
  preview=null;previewInfo=null;closeRight();fit();
 }
 notify(`Добавлено контактов: ${add.length}${duplicates?`. Пропущено повторов: ${duplicates}`:""}${overLimit?`. Не поместилось на карту: ${overLimit}`:""}`);
}
let phonebookCalls=false;
function pickContacts(withCalls){
 requestContactPicker(()=>{
  phonebookCalls=withCalls;
  window.KartaFiles.pickContacts();
 });
}
window.kartaContactsReady=async error=>{
 if(!pickerMap)return;
 const target=pickerMap,graph=data,withCalls=phonebookCalls;
 let chosen=[];
 try{
  if(error)throw Error(error);
  const response=await fetch("/contacts",{cache:"no-store"});
  if(!response.ok)throw Error("Не удалось прочитать телефонную книгу");
  const contacts=await response.json();
  if(!contacts.length){notify("Телефонная книга пуста");return;}
  chosen=await chooseContacts(contacts,withCalls?"Добавить и учесть звонки":"Добавить из контактов",withCalls?"Добавить и подсчитать":"Добавить");
 }catch(e){notify(e.message);}
 finally{pickerMap=null;}
 if(!chosen.length||target!==mapId||graph!==data||editingBase)return;
 addContacts(chosen);
 if(withCalls){
  const numbers=new Set(chosen.map(row=>phoneKey(row.phone)));
  refreshCalls(phoneRows().filter(row=>numbers.has(row.phone)));
 }
};
