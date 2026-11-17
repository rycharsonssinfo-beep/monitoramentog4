/* Mapa de Sistemas — filtros operacionais clicáveis por município.
   Um indicador mede ambientes; o mapa destaca municípios com pelo menos um ambiente correspondente. */
(function installMapStatusFilters(){
  if(window.__ssMapStatusFiltersInstalled)return;
  const previous=window.ssMapOpen;
  if(typeof previous!=="function")return;
  window.__ssMapStatusFiltersInstalled=true;
  const MODES=["portais","fluxus","veiculos"];
  const STATES={
    online:{title:"online",color:"#0fa778"},
    offline:{title:"indisponíveis",color:"#e64858"},
    observacao:{title:"em observação",color:"#e4b143"},
    desatualizado:{title:"desatualizados",color:"#ce902c"},
    sem_leitura:{title:"sem leitura",color:"#8c9cae"}
  };
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const stateFor=(row,now=Date.now())=>{
    if(typeof window.ssMapOperationalState==="function")return window.ssMapOperationalState(row,now);
    const time=Date.parse(row?.ultima_verificacao||"");
    if(!Number.isFinite(time)||time>now+300000)return"sem_leitura";
    if(now-time>900000)return"desatualizado";
    if(row.estado==="online")return"online";
    if(row.estado==="offline")return"offline";
    return ["suspeita_falha","recuperando","verificacao_bloqueada"].includes(row.estado)?"observacao":"sem_leitura";
  };
  function matchingCities(cities,status,modes=[],now=Date.now()){
    if(!Object.prototype.hasOwnProperty.call(STATES,status))return[];
    const considered=modes.length?modes:MODES;
    return (cities||[]).filter(c=>modes.every(m=>(c.systems?.[m]||[]).length>0))
      .map(c=>{
        let count=0;
        for(const mode of considered)for(const row of c.systems?.[mode]||[]){
          if(stateFor(row,now)===status)count++;
        }
        return {name:c.name,key:c.key,count};
      }).filter(c=>c.count>0)
      .sort((a,b)=>String(a.name).localeCompare(String(b.name),"pt-BR"));
  }
  function attach(layer){
    if(layer.dataset.ssStatusFilter)return;
    layer.dataset.ssStatusFilter="1";
    const strip=layer.querySelector(".ss-map-ops-strip");
    const container=strip?.querySelector("[data-map-ops-values]");
    if(!strip||!container)return;
    let cities=null,selected="",observer=null,timer=null;
    const info=document.createElement("div");
    info.className="ss-map-status-results";
    info.hidden=true;
    strip.appendChild(info);
    strip.querySelector(".ss-map-ops-strip-head small").textContent=
      "Clique em um status para destacar os municípios · verificação recente até 15 min";
    const selectedModes=()=>[...layer.querySelectorAll("[data-sm-mode]:checked")]
      .map(e=>e.dataset.smMode).filter(m=>MODES.includes(m));
    function restoreCount(){
      if(!cities)return;
      const modes=selectedModes();
      const qualified=cities.filter(c=>modes.every(m=>(c.systems?.[m]||[]).length>0));
      const count=modes.length?qualified.length:cities.filter(c=>MODES.some(m=>(c.systems?.[m]||[]).length)).length;
      const elem=layer.querySelector("[data-sm-filter-count]");
      if(elem)elem.textContent=count+(modes.length?" municípios com a combinação selecionada":" municípios atendidos");
    }
    function paint(){
      if(!cities)return;
      const paths=layer.querySelectorAll("svg.ss-map-svg path[data-ss-city]");
      const buttons=container.querySelectorAll("button[data-map-status]");
      buttons.forEach(b=>{
        const active=selected===b.dataset.mapStatus;
        b.classList.toggle("active",active);
        b.setAttribute("aria-pressed",String(active));
      });
      if(!selected){
        paths.forEach(p=>{
          p.style.removeProperty("fill");
          p.style.opacity=p.dataset.ssFiltermatch==="0"?".53":"1";
          p.classList.remove("ss-map-status-match","ss-map-status-dim");
        });
        info.hidden=true;
        restoreCount();
        return;
      }
      const modes=selectedModes();
      const found=matchingCities(cities,selected,modes);
      const keys=new Set(found.map(c=>c.key));
      for(const path of paths){
        const match=keys.has(path.dataset.ssCity);
        path.style.setProperty("fill",match?STATES[selected].color:"#718398");
        path.style.setProperty("opacity",match?"1":".38");
        path.classList.toggle("ss-map-status-match",match);
        path.classList.toggle("ss-map-status-dim",!match);
      }
      const count=found.reduce((n,c)=>n+c.count,0);
      const limit=14;
      info.hidden=false;
      info.innerHTML='<div class="ss-map-status-result-head">'+
        '<strong>'+found.length+' município'+(found.length===1?"":"s")+
        ' com ambientes '+STATES[selected].title+'</strong>'+
        '<small>'+count+' ambiente'+(count===1?"":"s")+
          (modes.length?" nos sistemas selecionados":"")+'</small></div>'+
        (found.length?'<div class="ss-map-status-towns">'+found.slice(0,limit).map(c=>
          '<button type="button" data-map-city="'+esc(c.key)+'" title="Selecionar '+esc(c.name)+'">'+
          esc(c.name)+' <b>'+c.count+'</b></button>').join("")+'</div>':
          '<p class="ss-map-status-empty">Nenhum município com este status'+
            (modes.length?" na combinação de sistemas selecionada":"")+'.</p>')+
        (found.length>limit?'<small class="ss-map-status-more">Mostrando os primeiros '+
          limit+' municípios; os demais permanecem destacados no mapa.</small>':'')+
        '<button type="button" class="ss-map-status-clear" data-map-status-clear="1">Limpar destaque</button>';
      const counter=layer.querySelector("[data-sm-filter-count]");
      if(counter)counter.textContent=found.length+" município"+(found.length===1?"":"s")+
        " com ambientes "+STATES[selected].title;
    }
    function convertIndicators(){
      // O módulo operacional redesenha os contadores periodicamente.
      // Convertemos os elementos originais em botões sem interferir no cálculo.
      const spans=container.querySelectorAll("span.ss-map-ops-chip");
      for(const span of spans){
        const state=Object.keys(STATES).find(s=>span.classList.contains(s));
        if(!state)continue;
        const btn=document.createElement("button");
        btn.type="button";
        btn.className=span.className+" ss-map-status-button";
        btn.dataset.mapStatus=state;
        btn.innerHTML=span.innerHTML;
        btn.title="Destacar no mapa municípios com ambientes "+STATES[state].title;
        btn.setAttribute("aria-label",btn.title+"; número exibido representa ambientes.");
        span.replaceWith(btn);
      }
      if(cities)paint();
    }
    container.addEventListener("click",e=>{
      const button=e.target.closest("button[data-map-status]");
      if(!button||!container.contains(button))return;
      selected=selected===button.dataset.mapStatus?"":button.dataset.mapStatus;
      paint();
    });
    info.addEventListener("click",e=>{
      if(e.target.closest("[data-map-status-clear]")){
        selected="";paint();return;
      }
      const b=e.target.closest("button[data-map-city]");
      if(!b)return;
      const city=cities?.find(c=>c.key===b.dataset.mapCity);
      const search=layer.querySelector("[data-sm-search]");
      if(city&&search){
        search.value=city.name;
        search.dispatchEvent(new Event("change",{bubbles:true}));
      }
    });
    layer.addEventListener("ss-map-data-ready",e=>{
      cities=e.detail?.cities||[];
      convertIndicators();
    });
    layer.addEventListener("ss-map-filter-change",()=>{if(selected)paint()});
    observer=new MutationObserver(()=>{
      if(!layer.isConnected){observer.disconnect();clearInterval(timer);return}
      if(container.querySelector("span.ss-map-ops-chip"))convertIndicators();
    });
    observer.observe(container,{childList:true});
    convertIndicators();
    timer=setInterval(()=>{
      if(!layer.isConnected){observer.disconnect();clearInterval(timer);return}
      if(selected)paint();
    },60000);
  }
  window.ssMapMatchedStatusCities=matchingCities;
  window.ssMapOpen=function(host){
    previous(host);
    const layer=host.querySelector("[data-ss-map]");
    if(layer)attach(layer);
  };
})();