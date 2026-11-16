(function(){
if(window.__ssMapLabelsPhoto)return;
window.__ssMapLabelsPhoto=true;
const original=window.ssMapOpen;
if(typeof original!=="function")return;
const norm=x=>String(x||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
const noSystemColor="#8995a8"; // cor dos municípios sem sistema no mapa inicial
const cache=new Map();
async function photo(name){
 const key=norm(name);if(cache.has(key))return cache.get(key);
 let info=null;
 try{
  const isCaucaia=key==="caucaia";
  const p=new URLSearchParams({action:"query",format:"json",origin:"*",redirects:"1"});
  if(isCaucaia){p.set("prop","imageinfo");p.set("titles","File:Caucaia 05.jpg");p.set("iiprop","url");p.set("iiurlwidth","800")}
  else{p.set("prop","pageimages");p.set("titles",name+" (Ceará)");p.set("pithumbsize","800")}
  const api=isCaucaia?"https://commons.wikimedia.org/w/api.php":"https://pt.wikipedia.org/w/api.php";
  const r=await fetch(api+"?"+p);if(!r.ok)throw Error("HTTP "+r.status);
  const pages=Object.values((await r.json()).query?.pages||{});
  const page=pages.find(x=>isCaucaia?x.imageinfo?.length:x.thumbnail?.source);
  if(page){
   const imageTitle=String(page.pageimage||"");
   if(!isCaucaia&&/flag|bandeira|bras[aã]o|mapa|map|logo|escudo/i.test(imageTitle))throw Error("Não é fotografia");
   const url=isCaucaia?(page.imageinfo[0].thumburl||page.imageinfo[0].url):page.thumbnail.source;
   const source=isCaucaia?"https://commons.wikimedia.org/wiki/File:Caucaia_05.jpg":"https://pt.wikipedia.org/wiki/"+encodeURIComponent(page.title.replace(/ /g,"_"));
   if(url&&url.startsWith("https://"))info={url,source,credit:isCaucaia?"Joelkaula / Wikimedia Commons":"Wikipédia / Wikimedia Commons"};
  }
 }catch(e){console.debug("Foto indisponível: "+name)}
 cache.set(key,info);return info;
}
function decorateCity(layer){
 const el=layer.querySelector("[data-sm-detail]");
 const h=el?.querySelector(":scope > .ss-map-city");
 if(!h)return;
 const name=h.textContent.replace(/\s+[—-]\s+CE\s*$/,"").trim();
 const id=h.nextElementSibling;
 const banner=document.createElement("div");banner.className="ss-map-city-banner";banner.dataset.city=norm(name);
 const overlay=document.createElement("div");overlay.className="ss-map-city-banner-overlay";
 const title=document.createElement("h2");title.textContent=name+" — CE";
 const sub=document.createElement("p");sub.textContent=id?.textContent||"";
 overlay.append(title,sub);banner.append(overlay);h.replaceWith(banner);if(id)id.remove();
 photo(name).then(f=>{
  if(!f||!banner.isConnected||banner.dataset.city!==norm(name))return;
  const img=new Image();img.alt="Fotografia de "+name;img.referrerPolicy="no-referrer";
  img.onload=()=>{
   if(!banner.isConnected)return;
   banner.prepend(img);
   const credit=document.createElement("a");credit.className="ss-map-city-credit";credit.href=f.source;credit.target="_blank";credit.rel="noopener noreferrer";credit.textContent="Foto: "+f.credit;banner.append(credit);
  };
  img.src=f.url;
 });
}
function labels(layer,svg){
 if(svg.dataset.ssNamesReady)return;
 svg.dataset.ssNamesReady="1";
 const parent=svg.parentElement,wrapper=document.createElement("div");wrapper.className="ss-map-svg-wrapper";
 parent.replaceChild(wrapper,svg);wrapper.append(svg);
 const tooltip=document.createElement("div");tooltip.className="ss-map-hover-name";wrapper.append(tooltip);
 const controls=document.createElement("div");controls.className="ss-map-name-controls";
 controls.innerHTML='<label><input type="checkbox" data-sm-all-names> Exibir todos os municípios atendidos</label><span><button type="button" data-sm-plus title="Aproximar">+</button><button type="button" data-sm-minus title="Afastar">−</button><button type="button" data-sm-reset title="Restaurar">↺</button></span>';
 parent.insertBefore(controls,wrapper);
 const labels=[],ns="http://www.w3.org/2000/svg";
 for(const path of [...svg.querySelectorAll("path")]){
  const name=path.querySelector("title")?.textContent?.trim();
  if(!name)continue;
  let box;try{box=path.getBBox()}catch(e){continue}
  const text=document.createElementNS(ns,"text");text.textContent=name;text.classList.add("ss-map-municipio-label");
  text.setAttribute("x",String(box.x+box.width/2));text.setAttribute("y",String(box.y+box.height/2));
  const registered=String(path.getAttribute("fill")||"").toLowerCase()!==noSystemColor;
  labels.push({text,key:norm(name),registered});
  path.addEventListener("pointerenter",()=>{tooltip.textContent=name;tooltip.classList.add("visible")});
  path.addEventListener("pointermove",e=>{const rect=wrapper.getBoundingClientRect();tooltip.style.left=Math.max(5,Math.min(rect.width-165,e.clientX-rect.left+13))+"px";tooltip.style.top=Math.max(5,e.clientY-rect.top-40)+"px"});
  path.addEventListener("pointerleave",()=>tooltip.classList.remove("visible"));
 }
 labels.forEach(x=>svg.append(x.text));
 let all=false;const detail=layer.querySelector("[data-sm-detail]");
 function redraw(){
  const title=detail.querySelector(".ss-map-city-banner h2")?.textContent||detail.querySelector(".ss-map-city")?.textContent||"";
  const active=norm(title.replace(/\s+[—-]\s+CE\s*$/,""));
  // Evita sobreposição na visualização padrão. Ao aproximar, mais nomes cabem.
  const placed=[];
  const zoom=690/(Number(svg.viewBox.baseVal.width)||690);
  const candidates=labels.filter(x=>x.registered)
    .sort((a,b)=>Number(b.key===active)-Number(a.key===active)
      ||Number(b.text.textContent.length<13)-Number(a.text.textContent.length<13));
  for(const x of labels){x.text.style.display="none";x.text.classList.toggle("active",x.key===active);x.text.classList.toggle("all",all&&x.key!==active)}
  for(const x of candidates){
   if(all){x.text.style.display="";continue}
   const px=Number(x.text.getAttribute("x")),py=Number(x.text.getAttribute("y"));
   const size=x.key===active?13:10, width=(x.text.textContent.length*size*.56+10)/zoom;
   const height=(size+5)/zoom;
   const box={x:px-width/2,y:py-height/2,w:width,h:height};
   if(x.key!==active && placed.some(v=>box.x<v.x+v.w && box.x+box.w>v.x && box.y<v.y+v.h && box.y+box.h>v.y))continue;
   x.text.style.display="";
   placed.push(box);
  }
 }
 const obs=new MutationObserver(()=>{decorateCity(layer);redraw()});obs.observe(detail,{childList:true});
 decorateCity(layer);redraw();
 controls.querySelector("[data-sm-all-names]").onchange=e=>{all=e.target.checked;redraw()};
 let v={x:0,y:0,w:690,h:760};
 const WIDTH=690,HEIGHT=760,MIN_W=85;
 const activePointers=new Map();
 let dragStart=null,pinchDistance=0,dragged=false,suppressClick=false;
 function clampView(x,y,w,h){
   w=Math.min(WIDTH,Math.max(MIN_W,w));
   h=HEIGHT*w/WIDTH;
   return {x:Math.max(0,Math.min(WIDTH-w,x)),y:Math.max(0,Math.min(HEIGHT-h,y)),w,h};
 }
 function renderView(){
   svg.setAttribute("viewBox",[v.x,v.y,v.w,v.h].map(n=>Number(n.toFixed(3))).join(" "));
   redraw();
 }
 function coordinate(clientX,clientY){
   const rect=svg.getBoundingClientRect();
   // SVG preserveAspectRatio=xMidYMid meet: descontar margens internas se necessário.
   const factor=Math.min(rect.width/v.w,rect.height/v.h);
   const vw=v.w*factor,vh=v.h*factor;
   const ox=rect.left+(rect.width-vw)/2,oy=rect.top+(rect.height-vh)/2;
   return {x:Math.max(0,Math.min(1,(clientX-ox)/vw)),y:Math.max(0,Math.min(1,(clientY-oy)/vh))};
 }
 function zoom(f,clientX,clientY){
   const r=svg.getBoundingClientRect();
   const at=coordinate(clientX??r.left+r.width/2,clientY??r.top+r.height/2);
   const w=Math.min(WIDTH,Math.max(MIN_W,v.w*f)),h=HEIGHT*w/WIDTH;
   const worldX=v.x+at.x*v.w,worldY=v.y+at.y*v.h;
   v=clampView(worldX-at.x*w,worldY-at.y*h,w,h);
   renderView();
 }
 controls.querySelector("[data-sm-plus]").onclick=()=>zoom(.78);
 controls.querySelector("[data-sm-minus]").onclick=()=>zoom(1.28);
 controls.querySelector("[data-sm-reset]").onclick=()=>{
   v={x:0,y:0,w:WIDTH,h:HEIGHT};renderView();
 };
 // A roda do mouse aplica zoom sobre o local do cursor, sem rolar o painel.
 svg.addEventListener("wheel",e=>{
   if(!e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey){
     e.preventDefault();
     const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?420:1);
     zoom(Math.exp(Math.max(-150,Math.min(150,delta))*.00175),e.clientX,e.clientY);
   }
 },{passive:false});
 function distance(a,b){return Math.hypot(a.x-b.x,a.y-b.y)}
 svg.addEventListener("pointerdown",e=>{
   if(e.button!==0 && e.pointerType==="mouse")return;
   activePointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
   try{svg.setPointerCapture(e.pointerId)}catch(_){}
   if(activePointers.size===1){
     dragStart={x:e.clientX,y:e.clientY,view:{...v}};dragged=false;
     svg.classList.add("ss-map-dragging");
   }else if(activePointers.size===2){
     pinchDistance=distance(...activePointers.values());dragStart=null;
   }
 });
 svg.addEventListener("pointermove",e=>{
   if(!activePointers.has(e.pointerId))return;
   activePointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
   if(activePointers.size===2){
     const points=[...activePointers.values()];
     const d=distance(points[0],points[1]);
     const mid={x:(points[0].x+points[1].x)/2,y:(points[0].y+points[1].y)/2};
     if(pinchDistance>0&&d>0){zoom(pinchDistance/d,mid.x,mid.y);dragged=true}
     pinchDistance=d;return;
   }
   if(!dragStart)return;
   const dx=e.clientX-dragStart.x,dy=e.clientY-dragStart.y;
   if(Math.abs(dx)+Math.abs(dy)>5)dragged=true;
   if(!dragged)return;
   const rect=svg.getBoundingClientRect();
   const scale=Math.min(rect.width/v.w,rect.height/v.h);
   v=clampView(v.x-dx/scale,v.y-dy/scale,v.w,v.h);
   dragStart={x:e.clientX,y:e.clientY,view:{...v}};
   renderView();
 });
 function finishPointer(e){
   if(!activePointers.has(e.pointerId))return;
   activePointers.delete(e.pointerId);
   if(dragged){
     suppressClick=true;
     setTimeout(()=>{suppressClick=false},150);
   }
   if(activePointers.size===1){
     const p=[...activePointers.values()][0];
     dragStart={x:p.x,y:p.y,view:{...v}};
     pinchDistance=0;
   }else if(activePointers.size===0){
     dragStart=null;pinchDistance=0;
     svg.classList.remove("ss-map-dragging");
   }
 }
 svg.addEventListener("pointerup",finishPointer);
 svg.addEventListener("pointercancel",finishPointer);
 svg.addEventListener("lostpointercapture",finishPointer);
 svg.addEventListener("click",e=>{
   if(suppressClick){e.preventDefault();e.stopImmediatePropagation();suppressClick=false}
 },true);
 svg.addEventListener("dblclick",e=>{e.preventDefault();zoom(.7,e.clientX,e.clientY)});

}
function begin(layer){
 const watcher=new MutationObserver(()=>{
  const svg=layer.querySelector(".ss-map-svg");if(svg){watcher.disconnect();labels(layer,svg)}
 });
 watcher.observe(layer,{childList:true,subtree:true});
 const svg=layer.querySelector(".ss-map-svg");if(svg){watcher.disconnect();labels(layer,svg)}
}
window.ssMapOpen=function(host){
 original(host);
 const layer=host.querySelector("[data-ss-map]");
 if(layer&&!layer.dataset.ssEnhanced){layer.dataset.ssEnhanced="1";begin(layer)}
};
})();