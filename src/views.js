function updateViewIndicator(){
 const v=data.savedViews.find(v=>v.name===data.activeView);
 const changed=v&&(["view","group","filters","settings"].some(k=>JSON.stringify(data[k])!==JSON.stringify(v[k]))||
 v.positions.length!==data.people.length||data.people.some((n,i)=>{const p=v.positions[i];return !p||p[0]!==n.id||p[1]!==n.x||p[2]!==n.y;}));
 $("view-state").textContent=v?"Тема «"+v.name+"»"+(changed?" · изменена":""):"";
}
function manageView(action){
 const index=Number($("view-list")?.value??-1),view=data.savedViews[index];
 if(action==="save"||action==="update"){
  const name=action==="update"?data.activeView:$("view-name").value.trim().slice(0,80);
  if(!name)return notify("Введите название темы");
  const i=data.savedViews.findIndex(v=>v.name===name);
  if(i<0&&data.savedViews.length>=32)return notify("Можно сохранить до 32 тем");
  if(i>=0&&!confirm("Обновить тему «"+name+"»?"))return;
  remember("Сохранена тема "+name);
  data.activeView=name;data.savedViews[i<0?data.savedViews.length:i]={name,settings:clone(data.settings),filters:clone(data.filters),group:clone(data.group),view:clone(data.view),positions:data.people.map(n=>[n.id,n.x,n.y])};
 }else if(view){
  if(action==="remove"&&!confirm("Удалить тему «"+view.name+"»?"))return;
  remember((action==="remove"?"Удалена тема ":"Открыта тема ")+view.name);
  if(action==="remove"){data.savedViews.splice(index,1);if(view.name===data.activeView)data.activeView=null;}
  else{
   data.activeView=view.name;for(const key of ["settings","filters","group","view"])data[key]=clone(view[key]);
   if(!get(data.filters.focus))data.filters.focus=null;
   const coords=new Map(view.positions.map(([id,x,y])=>[id,[x,y]]));
   for(const n of data.people)if(coords.has(n.id))[n.x,n.y]=coords.get(n.id);
   route=[];closeSide();
  }
 }else return;
 preview=null;previewInfo=null;finish();renderRight();
}
