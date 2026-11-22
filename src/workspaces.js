// The original graph keeps the keys used by versions 2.1–2.3.
let mapId="home", saveError="", switching=false;
const mapNames=new Map([["home","Основная карта"]]), histories=new Map();
const mapKey=(id,key)=>id==="home"?key:"map/"+id+"/"+key;
function saveIndicator(){
 const el=$("save-state");if(!el)return;
 el.textContent=saveError?"Только в памяти · "+saveError:dirty||writesPending?"Сохраняется…":"Сохранено";
 $("rescue").hidden=!saveError;
}
function showTabs(){
 $("map-tabs").innerHTML=[...mapNames].map(([key,name])=>
  `<button class="btn" aria-pressed="${mapId===key}" data-map="${h(key)}">${h(name)}</button>`).join("");
}
async function readMap(id){
 const [stored,revision]=await new Promise((resolve,reject)=>{
  const tx=database.transaction("graphs"),s=tx.objectStore("graphs");
  const content=s.get(mapKey(id,"current")),rev=s.get(mapKey(id,"revision"));
  tx.oncomplete=()=>resolve([content.result,rev.result||0]);
  tx.onabort=tx.onerror=()=>reject(tx.error);
 });
 let key=null,salt=null,graph;
 if(stored&&typeof stored!=="string"){
  const pass=await askSecret("Пароль карты «"+mapNames.get(id)+"»");
  if(pass===null)throw Error("Карта заблокирована");
  salt=stored.salt;key=await internalKey(pass,salt);
  const bytes=await crypto.subtle.decrypt({name:"AES-GCM",iv:stored.iv},key,stored.cipher);
  graph=validate(JSON.parse(new TextDecoder().decode(bytes)));
 }else{
  const source=stored??(id==="home"?(localStorage.getItem(STORAGE)??localStorage.getItem("relationship-map-v1")):null);
  graph=source?validate(JSON.parse(source)):initial();
 }
 return {graph,key,salt,revision};
}
function installMap(id,state){
 mapId=id;data=state.graph;vaultKey=state.key;vaultSalt=state.salt;storageRevision=state.revision;
 const history=histories.get(id);
 undo=history?.undo||[];redo=history?.redo||[];
 if(history&&history.rev!==storageRevision){undo=[];redo=[];}
 dirty=false;saveError="";selected=null;anchor=null;route=[];preview=null;previewInfo=null;
 mode="select";$("kv2-link-btn").classList.remove("active");
 pointer=null;pinch=null;pointers.clear();clearTimeout(longTimer);
 if(pendingFrame){cancelAnimationFrame(pendingFrame);pendingFrame=0;}
 $("kv2-menu").hidden=true;pendingCalls=null;pickerMap=null;searchReturn=false;
 closeSide();closeRight();$("kv2-side-body").replaceChildren();$("kv2-right-body").replaceChildren();showTabs();saveIndicator();updateViewIndicator();
}
async function switchMap(id,name){
 if(switching||id===mapId||!persistentReady)return;
 if(editingBase||pendingCalls||pickerMap){notify("Сначала завершите редактирование или выбор контакта");return;}
 switching=true;root.inert=true;
 try{
  flushSave();await lastWrite;
  if(dirty||saveError)throw Error("Сначала сохраните изменения или скачайте копию");
  if(name){
   await dbRequest("readwrite",s=>s.add(name,"tab/"+id));
   mapNames.set(id,name);
  }
  const next=await readMap(id);
  if(vaultKey)histories.delete(mapId);else histories.set(mapId,{rev:storageRevision,undo,redo});
  installMap(id,next);
 }catch(e){notify(e.message);}finally{root.inert=false;switching=false;}
}
function newMap(){
 const name=prompt("Название новой, пустой карты")?.trim().slice(0,80);
 if(name)switchMap(id(),name);
}
async function renameMap(){
 const name=prompt("Название карты",mapNames.get(mapId))?.trim().slice(0,80);
 if(!name)return;
 const target=mapId;
 try{await dbRequest("readwrite",s=>s.put(name,"tab/"+target));mapNames.set(target,name);showTabs();}
 catch(e){notify(e.message);}
}
async function loadTabNames(){
 const rows=await new Promise((resolve,reject)=>{
  const tx=database.transaction("graphs"),s=tx.objectStore("graphs"),range=IDBKeyRange.bound("tab/","tab/\uffff");
  const keys=s.getAllKeys(range),names=s.getAll(range);
  tx.oncomplete=()=>resolve(keys.result.map((key,i)=>[key.slice(4),names.result[i]]));
  tx.onabort=tx.onerror=()=>reject(tx.error);
 });
 for(const [key,name] of rows)mapNames.set(key,name);
 showTabs();
}
