(function(){
if(window.__ssMapLabelsPhoto)return;
window.__ssMapLabelsPhoto=true;
const original=window.ssMapOpen;
if(typeof original!=="function")return;
const norm=x=>String(x||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
const landmarks=new Set(["caucaia","fortaleza","sobral","juazeirodonorte","crato","maracanau","quixada","iguatu","itapipoca","aracati","crateus","russas","pacajus","caninde","tiangua","acarau"]);
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
 controls.innerHTML='<label><input type="checkbox" data-sm-all-names> Exibir todos os nomes</label><span><button type="button" data-sm-plus title="Aproximar">+</button><button type="button" data-sm-minus title="Afastar">−</button><button type="button" data-sm-reset title="Restaurar">↺</button></span>';
 parent.insertBefore(controls,wrapper);
 const labels=[],ns="http://www.w3.org/2000/svg";
 for(const path of [...svg.querySelectorAll("path")]){
  const name=path.querySelector("title")?.textContent?.trim();
  if(!name)continue;
  let box;try{box=path.getBBox()}catch(e){continue}
  const text=document.createElementNS(ns,"text");text.textContent=name;text.classList.add("ss-map-municipio-label");
  text.setAttribute("x",String(box.x+box.width/2));text.setAttribute("y",String(box.y+box.height/2));
  labels.push({text,key:norm(name)});
  path.addEventListener("pointerenter",()=>{tooltip.textContent=name;tooltip.classList.add("visible")});
  path.addEventListener("pointermove",e=>{const rect=wrapper.getBoundingClientRect();tooltip.style.left=Math.max(5,Math.min(rect.width-165,e.clientX-rect.left+13))+"px";tooltip.style.top=Math.max(5,e.clientY-rect.top-40)+"px"});
  path.addEventListener("pointerleave",()=>tooltip.classList.remove("visible"));
 }
 labels.forEach(x=>svg.append(x.text));
 let all=false;const detail=layer.querySelector("[data-sm-detail]");
 function redraw(){
  const title=detail.querySelector(".ss-map-city-banner h2")?.textContent||detail.querySelector(".ss-map-city")?.textContent||"";
  const active=norm(title.replace(/\s+[—-]\s+CE\s*$/,""));
  for(const x of labels){
   x.text.style.display=(all||landmarks.has(x.key)||x.key===active)?"":"none";
   x.text.classList.toggle("active",x.key===active);
   x.text.classList.toggle("all",all&&x.key!==active);
  }
 }
 const obs=new MutationObserver(()=>{decorateCity(layer);redraw()});obs.observe(detail,{childList:true});
 decorateCity(layer);redraw();
 controls.querySelector("[data-sm-all-names]").onchange=e=>{all=e.target.checked;redraw()};
 let v={x:0,y:0,w:690,h:760};
 function zoom(f){
  const w=Math.max(145,Math.min(690,v.w*f)),h=Math.max(160,Math.min(760,v.h*f));
  const mx=v.x+v.w/2,my=v.y+v.h/2;
  v={x:Math.max(0,Math.min(690-w,mx-w/2)),y:Math.max(0,Math.min(760-h,my-h/2)),w,h};
  svg.setAttribute("viewBox",[v.x,v.y,w,h].join(" "));
 }
 controls.querySelector("[data-sm-plus]").onclick=()=>zoom(.78);
 controls.querySelector("[data-sm-minus]").onclick=()=>zoom(1.28);
 controls.querySelector("[data-sm-reset]").onclick=()=>{v={x:0,y:0,w:690,h:760};svg.setAttribute("viewBox","0 0 690 760")};
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