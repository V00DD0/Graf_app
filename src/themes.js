// Interface preferences belong to this installation; graph appearance belongs to the map.
const interfacePalettes=[
 {name:"Слоновая кость",base:"#f4eee2",accent:"#80552c"},
 {name:"Ночной сапфир",base:"#192a43",accent:"#b5cff3"},
 {name:"Малахит",base:"#183b34",accent:"#d6b879"},
 {name:"Бордо",base:"#442834",accent:"#edc4ac"}
];
const openedAppearanceSections=new Set();
const themeStorage="karta-interface-theme-v1";
function readInterfaceTheme(){
 let saved;
 try{saved=JSON.parse(localStorage.getItem(themeStorage));}catch{}
 return {base:validColor(saved?.base,interfacePalettes[0].base),accent:validColor(saved?.accent,interfacePalettes[0].accent),motion:saved?.motion!==false};
}
let interfaceTheme=readInterfaceTheme();
function channels(hex){return [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));}
function blend(a,b,amount){
 const target=channels(b);
 return "#"+channels(a).map((c,i)=>Math.round(c+(target[i]-c)*amount).toString(16).padStart(2,"0")).join("");
}
function inkOn(color){
 const linear=channels(color).map(v=>{const c=v/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4;});
 return .2126*linear[0]+.7152*linear[1]+.0722*linear[2]>.179?"#000000":"#ffffff";
}
function applyInterfaceTheme(){
 const {base,accent,motion}=interfaceTheme,baseInk=inkOn(base),light=baseInk==="#000000";
 const surface=blend(base,light?"#ffffff":"#000000",light ? .55 : .22);
 const card=blend(surface,light?"#ffffff":"#000000",.25);
 const ink=inkOn(surface);
 const tokens={base,accent,surface,card,ink,"base-ink":baseInk,"accent-ink":inkOn(accent),
  muted:blend(surface,ink,.78),line:blend(surface,ink,.27),soft:blend(surface,accent,.12),
  danger:light?"#8c213a":"#ffb5bc"};
 const style=document.documentElement.style;
 for(const [key,value] of Object.entries(tokens))style.setProperty("--ui-"+key,value);
 root.dataset.motion=motion?"on":"off";
 root.style.colorScheme=light?"light":"dark";
}
function themeControls(){
 return `<section class="theme-section" aria-labelledby="ui-heading"><h3 id="ui-heading">Интерфейс</h3>
 <div class="theme-presets" role="group" aria-label="Готовые темы">${interfacePalettes.map((p,i)=>
  `<button type="button" data-palette="${i}" aria-label="${p.name}" aria-pressed="${p.base===interfaceTheme.base&&p.accent===interfaceTheme.accent}" class="theme-choice">
  <span class="theme-sample" aria-hidden="true" style="--sample-base:${p.base};--sample-accent:${p.accent}"></span>${p.name}</button>`).join("")}</div>
 <div class="pair">${[["base","Основной цвет"],["accent","Акцентный цвет"]].map(([key,label])=>
  `<label class="field">${label}<input type="color" data-interface="${key}" value="${interfaceTheme[key]}"></label>`).join("")}</div>
 <label><input type="checkbox" data-interface="motion" ${interfaceTheme.motion?"checked":""}> Анимация панелей</label>
 <p class="muted">Эти настройки действуют во всех картах на этом устройстве.</p></section>`;
}
function refreshThemeControls(){
 for(const button of right.querySelectorAll("[data-palette]")){
  const p=interfacePalettes[Number(button.dataset.palette)];
  button.setAttribute("aria-pressed",String(p.base===interfaceTheme.base&&p.accent===interfaceTheme.accent));
 }
 for(const field of right.querySelectorAll("[data-interface]")){
  const key=field.dataset.interface;
  if(key==="motion")field.checked=interfaceTheme.motion;
  else field.value=interfaceTheme[key];
 }
}
function saveInterfaceTheme(patch){
 Object.assign(interfaceTheme,patch);
 applyInterfaceTheme();refreshThemeControls();
 try{localStorage.setItem(themeStorage,JSON.stringify(interfaceTheme));}
 catch{notify("Оформление применено на этот сеанс. Сохранение на устройстве недоступно.");}
}
window.addEventListener("storage",e=>{
 if(e.key===themeStorage||e.key===null){interfaceTheme=readInterfaceTheme();applyInterfaceTheme();refreshThemeControls();}
});
applyInterfaceTheme();
