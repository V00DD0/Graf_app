function validatePresentation(raw,ids){
 const s=initial();
 if(raw.settings&&typeof raw.settings==="object"){
  const x=raw.settings;
  s.settings.bg=validColor(x.bg,"#ffffff");
  for(const key of ["grid","rings","sectors"]){
   const value=x[key];if(!value||typeof value!=="object")continue;
   const base=s.settings[key];
   base.on=!!value.on;base.color=validColor(value.color,base.color);
   base.width=clamp(value.width,base.width,.2,10);base.alpha=clamp(value.alpha,base.alpha,0,1);
   if(key==="grid"){base.dx=clamp(value.dx,100,10,2000);base.dy=clamp(value.dy,100,10,2000);}
   else if(key==="rings"){
    if(value.radii!==undefined&&(!Array.isArray(value.radii)||value.radii.length>128||value.radii.some((r,i)=>!Number.isFinite(r)||r<1||r>100000||(i&&r<=value.radii[i-1]))))throw Error("Некорректный список радиусов окружностей");
    base.radii=value.radii??[];base.names=(Array.isArray(value.names)?value.names:[]).slice(0,128).map(x=>fmt(x).slice(0,80));base.showNames=value.showNames!==false;base.labelColor=validColor(value.labelColor,"#6b503c");base.labelSize=clamp(value.labelSize,14,8,40);
    base.individual=value.individual===true;
    if(base.individual&&!base.radii.length)throw Error("Не указан радиус окружности");
    base.step=clamp(value.step,180,50,2000);base.dash=fmt(value.dash).replace(/[^0-9, .]/g,"").slice(0,30);}
   else {
    base.weights=(Array.isArray(value.weights)?value.weights:[1,1,1,1,1]).slice(0,24).map(z=>clamp(z,1,.1,30));
    if(base.weights.length<2)base.weights=[1,1];
    base.labels=base.weights.map((w,i)=>fmt(value.labels?.[i]||`Сектор ${i+1}`).slice(0,80));
    base.dash=fmt(value.dash).replace(/[^0-9, .]/g,"").slice(0,30);
   }
  }
 }
 const f=raw.filters||{};
 s.filters={...s.filters,
  search:fmt(f.search).slice(0,300),category:fmt(f.category||"all").slice(0,100),
  hops:clamp(f.hops,0,0,6),focus:ids.has(f.focus)?f.focus:null,
  timeline:!!f.timeline,date:/^\d{4}-\d\d-\d\d$/.test(f.date)?f.date:today(),
  layers:Object.fromEntries(Object.keys(s.filters.layers).map(k=>[k,f.layers?.[k]!==false]))
 };
 s.group={sectorBy:["category","city","job","tag"].includes(raw.group?.sectorBy)?raw.group.sectorBy:"category",
  ringBy:["hops","importance","contact","calls","none"].includes(raw.group?.ringBy)?raw.group.ringBy:"hops",
  visibleOnly:raw.group?.visibleOnly===true};
 s.view={x:clamp(raw.view?.x,0,-100000,100000),y:clamp(raw.view?.y,0,-100000,100000),k:clamp(raw.view?.k,1,.12,4)};
 return {settings:s.settings,filters:s.filters,view:s.view,group:s.group};
}
