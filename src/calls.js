const phoneCache=new Map();
function phoneKey(s){
 const raw=fmt(s).trim().replace(/[ ()\-.]/g,"").replace(/^00/,"+");
 if(!/^\+?\d{5,15}$/.test(raw))return "";
 if(!window.KartaFiles?.normalizePhone)return raw;
 if(!phoneCache.has(raw))phoneCache.set(raw,window.KartaFiles.normalizePhone(raw));
 return phoneCache.get(raw);
}
function isoDate(v){return typeof v==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v;}
function callCount(n){return n.calls&&n.calls.phone===phoneKey(n.phone)?n.calls.count:null;}
function phoneRows(){
 const rows=data.people.map(n=>({id:n.id,phone:phoneKey(n.phone)})).filter(r=>/^\+?\d{5,15}$/.test(r.phone));
 const seen=new Set(),duplicates=new Set();
 for(const row of rows){if(seen.has(row.phone))duplicates.add(row.phone);seen.add(row.phone);}
 return rows.filter(r=>!duplicates.has(r.phone));
}
function applyCounts(rows,totals,meta){
 remember("Обновлена статистика звонков");
 const phones=new Map(rows.map(r=>[r.id,r.phone]));
 for(const n of data.people){
  delete n.calls;
  if(phones.get(n.id)!==phoneKey(n.phone)||!Object.hasOwn(totals,n.id))continue;
  const count=totals[n.id];
  if(Number.isSafeInteger(count)&&count>=0)n.calls={phone:phoneKey(n.phone),count,asOf:today(),...meta};
 }
 data.group.ringBy="calls";finish();openRight("group");groupPreview();
}
let pendingCalls=null,pickerMap=null;
function requestContactPicker(open){
 if(pickerMap||pendingCalls)return notify("Выбор или подсчёт уже начат");
 if(editingBase||switching||!persistentReady)return notify("Сначала завершите работу с текущей картой");
 pickerMap=mapId;try{open();}catch(e){pickerMap=null;notify(e.message);}
}
window.kartaPickCancelled=()=>{pickerMap=null;};
function refreshCalls(){
 if(pendingCalls)return notify("Подсчёт уже идёт");
 const rows=phoneRows();
 if(!rows.length)return notify("Нужен хотя бы один уникальный номер в карточках");
 const token=id();pendingCalls={token,rows,graph:data};
 window.KartaFiles.analyzeCalls(token,JSON.stringify(rows));
}
function countSummary(counts,meta){
 const matched=Object.keys(counts).length, lost=data.people.filter(n=>n.calls&&!Object.hasOwn(counts,n.id)).length;
 return "Совпавших карточек: "+matched+". Период: "+(meta.start?meta.start+" — "+meta.end:"не указан")+". Прежние итоги будут удалены у "+lost+" карточек.";
}
window.kartaCallTotals=(token,counts,start,end)=>{
 const request=pendingCalls;if(!request||request.token!==token)return;
 if(!counts||request.graph!==data||editingBase){pendingCalls=null;return;}
 const meta={source:"device",start:isoDate(start)?start:"",end:isoDate(end)?end:""};
 const dialog=document.createElement("dialog");
 dialog.innerHTML='<form method="dialog"><h3>Обновление статистики звонков</h3><p></p><button value="apply" id="accept-totals">Обновить и посмотреть размещение</button> <button value="cancel">Отмена</button></form>';
 dialog.querySelector("p").textContent=countSummary(counts,meta);
 dialog.onclose=()=>{
  pendingCalls=null;dialog.remove();
  if(dialog.returnValue==="apply"&&request.graph===data&&!editingBase)applyCounts(request.rows,counts,meta);
 };
 document.body.append(dialog);dialog.showModal();
};
window.kartaPickedPhone=(name,phone,analyze)=>{
 const target=pickerMap;pickerMap=null;if(target&&target!==mapId)return;
 if(editingBase||!persistentReady||!phoneKey(phone))return;
 const matches=data.people.filter(n=>phoneKey(n.phone)===phoneKey(phone));
 if(matches.length>1)return notify("Номер уже указан у нескольких людей");
 let n=matches[0];
 if(!n){
  if(data.people.length>=10000)return notify("Достигнут лимит людей");
  remember("Добавлен контакт");n=person();n.name=name||phone;n.phone=phone;data.people.push(n);finish();
 }
 if(analyze)refreshCalls();else openSide("person",n.id);
};
async function importCounts(file){
 if(!file)return;
 const target=mapId;
 try{
  if(file.size>2*1024*1024)throw Error("Максимум 2 МБ");
  const lines=(await file.text()).trim().split(/\r?\n/);
  if(target!==mapId||switching)throw Error("Активная карта изменилась");
  const header=lines.shift()?.trim().toLowerCase().replaceAll(";",",");
  const dated=header==="phone,count,start,end",meta={source:"csv",start:"",end:""};
  if(!dated&&header!=="phone,count")throw Error("Нужен заголовок phone,count или phone,count,start,end");
  const byPhone=new Map();
  for(const [i,line] of lines.entries()){
   if(!line.trim())continue;
   const parts=line.split(/[,;]/),key=phoneKey(parts[0]),count=Number(parts[1]);
   if(dated){const [start,end]=parts.slice(2);if(!isoDate(start)||!isoDate(end)||start>end||(meta.start&&(meta.start!==start||meta.end!==end)))throw Error("Проверьте период в строке "+(i+2));Object.assign(meta,{start,end});}
   if(parts.length!==(dated?4:2)||!/^\+?\d{5,15}$/.test(key)||!/^\d+$/.test(parts[1].trim())||!Number.isSafeInteger(count)||byPhone.has(key))throw Error("Проверьте строку "+(i+2));
   byPhone.set(key,count);
  }
  const rows=phoneRows(),counts=Object.create(null);
  for(const r of rows)if(byPhone.has(r.phone))counts[r.id]=byPhone.get(r.phone);
  const matched=Object.keys(counts).length;
  if(!matched)throw Error("Нет однозначных совпадений с номерами в карточках");
  if(confirm(countSummary(counts,meta)+" Применить?"))applyCounts(rows,counts,meta);
 }catch(e){notify(e.message);}
}
