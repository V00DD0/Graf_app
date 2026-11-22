function ringLevels(){return data.settings.rings.individual?data.settings.rings.radii.length:5;}
function callRanks(levels){
 const rank=new Map();

  const counts=data.people.map(callCount),positive=[...new Set(counts.filter(c=>c>0))].sort((a,b)=>b-a);
  const outer=counts.some(c=>!(c>0))?Math.max(1,levels-1):levels;
  positive.forEach((c,i)=>rank.set(c,1+Math.floor(i*(outer-1)/Math.max(1,positive.length-1))));
 return rank;
}
function callRingReason(n,rank=callRanks(ringLevels()),shared=null){
 if(n.pinned)return "Позиция закреплена";
 const count=callCount(n),phone=phoneKey(n.phone);
 const duplicate=phone&&(shared?shared.has(phone):data.people.filter(p=>phoneKey(p.phone)===phone).length>1);
 const i=rank.get(count)??ringLevels(),name=data.settings.rings.names[i-1];
 return "Кольцо "+i+(name?" «"+name+"»":"")+" · "+(duplicate?"общий номер":count===null?"нет данных":"разговоров: "+count);
}
function groupPreview(){
 if(!data.people.length){notify("Нет людей для группировки");return;}
 const selectedId=data.filters.focus||(selected?.kind==="person"?selected.id:null)||data.people[0].id;
 const dist=data.group.ringBy==="hops"?hopDistances(selectedId):null;
 const by=data.group.sectorBy,rb=data.group.ringBy;
 const categoryOf=by==="category"?categoryIndex():null;
 const keyFor=n=>by==="city"?(n.city||"Город неизвестен"):
  by==="job"?(n.job||"Профессия неизвестна"):
  by==="tag"?(n.tags[0]||"Без тегов"):categoryOf(n);
 const counts=new Map();
 for(const n of data.people){
  const key=keyFor(n);counts.set(key,(counts.get(key)||0)+1);
 }
 const sorted=[...counts].sort((a,b)=>b[1]-a[1]).map(x=>x[0]);
 const categories=sorted.length>10?[...sorted.slice(0,9),"Прочие категории"]:sorted;
 if(categories.length===1)categories.push("Остальные");
 const catMap=n=>{const key=keyFor(n);return categories.includes(key)?key:"Прочие категории";};
 const recent=n=>{
  const a=n.contacts.map(c=>c.date).filter(Boolean).sort().at(-1);
  const days=dateDays(a);
  return days<=30?1:days<=180?2:days<=365?3:4;
 };
 const levels=ringLevels(),rank=rb==="calls"?callRanks(levels):null;
 const requestedRing=n=>rb==="calls"?(rank.get(callCount(n))??levels):rb==="hops"?Math.min(5,dist.has(n.id)?Math.max(1,dist.get(n.id)):5):
  rb==="importance"?Math.max(1,6-n.importance):rb==="contact"?recent(n):1;
 const guides=data.settings.rings;
 const ring=n=>guides.individual?Math.min(requestedRing(n),guides.radii.length):requestedRing(n);
 const maxRing=Math.max(1,...data.people.map(ring));
 const weights=categories.map(()=>1),step=data.settings.rings.step;
 const bins=new Map();
 const rootPerson=rb==="hops"?selectedId:null;
 for(const n of data.people){
  if(n.id===rootPerson||n.pinned)continue;
  const ci=categories.indexOf(catMap(n)),ri=ring(n);
  const key=ci+"|"+ri;
  if(!bins.has(key))bins.set(key,[]);
  bins.get(key).push(n);
 }
 const positions=Object.create(null);
 if(rootPerson&&!get(rootPerson).pinned)positions[rootPerson]={x:0,y:0};
 for(const [key,members] of bins){
  const [ci,ri]=key.split("|").map(Number),arc=2*Math.PI/categories.length;
  const minAngle=-Math.PI/2+ci*arc,baseRadius=guides.individual?guides.radii[ri-1]:ri*step;
  const space=guides.individual?Math.min(baseRadius-(guides.radii[ri-2]??0),(guides.radii[ri]??2*baseRadius)-baseRadius):step;
  const maxSize=Math.max(...members.map(n=>n.size))+18;
  const capacity=rb==="calls"?members.length:Math.max(1,Math.floor(baseRadius*(arc*.85)/maxSize));
  const lanes=Math.ceil(members.length/capacity);
  
  members.sort((a,b)=>full(a).localeCompare(full(b),"ru")||a.id.localeCompare(b.id));
  members.forEach((n,i)=>{
   const lane=Math.floor(i/capacity),index=i%capacity;
   const inLane=Math.min(capacity,members.length-lane*capacity);
   const angle=minAngle+arc*(.08+.84*(index+.5)/inLane);
   const laneOffset=(lane-(lanes-1)/2)*Math.min(maxSize*.9,space/(lanes+1));
   const radius=rb==="calls"?baseRadius:Math.max(guides.individual?1:25,baseRadius+laneOffset);
   positions[n.id]={x:Math.cos(angle)*radius,y:Math.sin(angle)*radius};
  });
 }
 const cells=new Map(), crowded=new Set();
 const cellSize=Math.max(1,...data.people.map(n=>n.size));
 for(const n of data.people){
  const p=positions[n.id]||n,cx=Math.floor(p.x/cellSize),cy=Math.floor(p.y/cellSize);
  for(let x=cx-1;x<=cx+1;x++)for(let y=cy-1;y<=cy+1;y++){
   for(const other of cells.get(x+","+y)||[]){
    if(Math.hypot(other.x-p.x,other.y-p.y)<(n.size+other.size)/2){
     crowded.add(n.id);crowded.add(other.id);
    }
   }
  }
  const key=cx+","+cy;
  if(!cells.has(key))cells.set(key,[]);
  cells.get(key).push({id:n.id,size:n.size,x:p.x,y:p.y});
 }
 const collisions=crowded.size;
 let reasons=null;
 if(rank){
  const seen=new Set(),shared=new Set();
  for(const n of data.people){const k=phoneKey(n.phone);if(seen.has(k))shared.add(k);seen.add(k);}
  reasons=new Map(data.people.map(n=>[n.id,callRingReason(n,rank,shared)]));
 }
 preview={positions};previewInfo={labels:categories,weights,maxRing,collisions,reasons};
 notify(collisions?`Предпросмотр: возможны наложения у ${collisions} людей. Увеличьте шаг окружностей.`:"Предпросмотр готов. Примените или отмените.");
 draw();if(pane==="group")renderRight();
}
