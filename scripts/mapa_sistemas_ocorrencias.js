/* Mapa de Sistemas — diagnóstico de ocorrências por município.
 * Usa exclusivamente os dados consolidados e eventos reais do Supabase.
 */
(function ssMapIncidentPanelInstall(){
  if(window.__ssMapIncidentPanelInstalled)return;
  const previous=window.ssMapOpen;
  if(typeof previous!=="function")return;
  window.__ssMapIncidentPanelInstalled=true;
  const SYSTEMS=[
    {key:"portais",name:"Portal do Contribuinte"},
    {key:"fluxus",name:"Fluxus"},
    {key:"veiculos",name:"Veículos"}
  ];
  const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const date=x=>{const t=Date.parse(x||"");return Number.isFinite(t)?new Date(t).toLocaleString("pt-BR"):"Não informada"};
  const status=row=>window.ssMapOperationalState?.(row)||"sem_leitura";
  const statusNames={online:"Online",offline:"Indisponível",observacao:"Em observação",desatualizado:"Leitura desatualizada",sem_leitura:"Sem leitura válida"};
  function ongoing(city){
    const all=[];
    if(!city)return all;
    for(const mode of SYSTEMS){
      for(const row of city.systems?.[mode.key]||[]){
        const state=status(row);
        if(state==="online")continue;
        all.push({mode:mode.name,modeKey:mode.key,row,state});
      }
    }
    const order={offline:0,observacao:1,desatualizado:2,sem_leitura:3};
    return all.sort((a,b)=>(order[a.state]??5)-(order[b.state]??5)||
      String(a.row.name).localeCompare(String(b.row.name),"pt-BR"));
  }
  function elapsed(start,now=Date.now()){
    const t=Date.parse(start||"");
    if(!Number.isFinite(t)||t>now)return"";
    const minutes=Math.floor((now-t)/60000);
    const h=Math.floor(minutes/60),m=minutes%60;
    if(h>=24)return Math.floor(h/24)+"d "+h%24+"h";
    return h? h+"h "+m+"min":m+" min";
  }
  function currentMarkup(city){
    const rows=ongoing(city);
    const offline=rows.filter(r=>r.state==="offline").length;
    const attention=rows.filter(r=>r.state==="observacao").length;
    const stale=rows.filter(r=>r.state==="desatualizado"||r.state==="sem_leitura").length;
    let html='<div class="ss-map-incidents-kpis">'+
      '<span class="offline"><b>'+offline+'</b> Indisponíveis</span>'+
      '<span class="attention"><b>'+attention+'</b> Em observação</span>'+
      '<span class="stale"><b>'+stale+'</b> Sem leitura recente</span></div>';
    const active=rows.filter(r=>r.state==="offline"||r.state==="observacao");
    if(!active.length)html+='<p class="ss-map-incidents-empty">Nenhuma indisponibilidade recente confirmada nos ambientes deste município.</p>';
    else html+='<div class="ss-map-incidents-list">'+active.map(({mode,row,state})=>{
      const hasCode=Number.isFinite(row.http_status)&&row.http_status>0;
      const duration=state==="offline"?elapsed(row.inicio_falha):"";
      const detail=String(row.detalhe||"").trim().slice(0,210);
      return '<article class="ss-map-incident-item '+state+'">'+
        '<div class="ss-map-incident-title"><strong>'+esc(row.name||mode)+'</strong>'+
        '<span>'+esc(statusNames[state])+'</span></div>'+
        '<small>'+esc(mode)+'</small>'+
        '<div class="ss-map-incident-meta">'+
          '<span>Última verificação: '+esc(date(row.ultima_verificacao))+'</span>'+
          (hasCode?'<span>HTTP '+esc(row.http_status)+'</span>':'')+
          (Number.isFinite(row.latencia_ms)&&row.latencia_ms>0?'<span>'+esc(Math.round(row.latencia_ms))+' ms</span>':'')+
          (duration?'<span>Desde a falha: '+esc(duration)+'</span>':'')+
        '</div>'+
        (detail?'<p>'+esc(detail)+'</p>':'')+
        (row.url?'<a href="'+esc(row.url)+'" target="_blank" rel="noopener noreferrer">Acessar ambiente</a>':'')+
      '</article>';
    }).join("")+'</div>';
    if(stale)html+='<p class="ss-map-incidents-caution">Há '+stale+' ambiente(s) sem verificação recente. O último estado conhecido não comprova indisponibilidade atual.</p>';
    return {html,offline,attention,stale,active:active.length};
  }
  function eventsMarkup(groups,city){
    const failures=[],errors=[];
    let truncated=false;
    for(const group of groups||[]){
      if(group.error)errors.push(group.mode);
      if(group.truncated)truncated=true;
      const mode=SYSTEMS.find(s=>s.key===group.mode);
      const byId=new Map((city.systems?.[group.mode]||[]).map(r=>[String(r.id),r]));
      for(const ev of group.rows||[]){
        const newer=String(ev.estado_atual||"").toLowerCase();
        const older=String(ev.estado_anterior||"").toLowerCase();
        if(!["offline","suspeita_falha","recuperando","verificacao_bloqueada"].includes(newer) &&
           !(newer==="online"&&older!=="online"))continue;
        failures.push({ev,mode:mode?.name||group.mode,env:byId.get(String(ev.portal_id))});
      }
    }
    failures.sort((a,b)=>Date.parse(b.ev.ocorrido_em||"")-Date.parse(a.ev.ocorrido_em||""));
    let html='<div class="ss-map-incidents-events-head"><strong>Eventos registrados (7 dias)</strong>'+
      '<small>'+failures.length+' ocorrência(s) ou recuperação(ões) na amostra</small></div>';
    if(errors.length)html+='<p class="ss-map-incidents-caution">Histórico parcialmente indisponível: '+esc(errors.join(", "))+'.</p>';
    if(!failures.length)html+='<p class="ss-map-incidents-empty">Sem alterações de estado registradas neste período para os ambientes identificados.</p>';
    else html+='<ol class="ss-map-incidents-timeline">'+failures.slice(0,7).map(({ev,mode,env})=>{
      const newer=String(ev.estado_atual||"").toLowerCase();
      const recovered=newer==="online";
      const label=recovered?"Recuperado":newer==="offline"?"Indisponibilidade registrada":"Mudança de estado";
      const http=Number(ev.codigo_http);
      const detail=String(ev.detalhe||"").slice(0,160);
      return '<li class="'+(recovered?"recovered":"failure")+'">'+
        '<div><strong>'+esc(label)+'</strong><time>'+esc(date(ev.ocorrido_em))+'</time></div>'+
        '<small>'+esc(mode)+' · '+esc(env?.name||ev.municipio||"Ambiente")+
        (Number.isFinite(http)&&http>0?' · HTTP '+esc(http):'')+'</small>'+
        (detail?'<p>'+esc(detail)+'</p>':'')+'</li>';
    }).join("")+'</ol>';
    if(truncated||failures.length>7)html+='<p class="ss-map-incidents-caution">Mostrando eventos recentes; abra Histórico do município para mais detalhes.</p>';
    return html;
  }
  function attach(layer){
    if(layer.dataset.ssMapIncidents)return;
    layer.dataset.ssMapIncidents="1";
    let cities=[],key="",loadToken=0,loadTime=0,loadedKey="",events=null;
    const current=()=>cities.find(c=>c.key===key)||null;
    function insert(city){
      const detail=layer.querySelector("[data-sm-detail]");
      if(!detail||!city)return;
      const history=detail.querySelector(".ss-map-history");
      const heading=detail.querySelector("h3");
      if(!heading)return;
      const panel=document.createElement("details");
      panel.className="ss-map-incidents";
      panel.innerHTML='<summary><span class="ss-map-incidents-icon" aria-hidden="true">!</span>'+
        '<span><strong>Ocorrências do município</strong>'+
        '<small data-incidents-summary>Diagnóstico das últimas verificações</small></span>'+
        '<span class="ss-map-incidents-arrow" aria-hidden="true">⌄</span></summary>'+
        '<div class="ss-map-incidents-body"><div data-incidents-current></div>'+
        '<div data-incidents-events></div>'+
        '<button type="button" class="ss-map-incidents-reload" data-incidents-reload>↻ Atualizar ocorrências</button>'+
        '<p class="ss-map-incidents-note">Fonte: cadastros e eventos do Monitor S&S. Duração somente quando a data de início da falha está registrada.</p></div>';
      if(history)history.before(panel);else heading.before(panel);
      const refresh=()=>update(false);
      panel.querySelector("[data-incidents-reload]").addEventListener("click",()=>update(true));
      panel.addEventListener("toggle",()=>{if(panel.open)refresh()});
      const summary=currentMarkup(city);
      panel.open=summary.active>0;
      renderCurrent(panel,city);
      if(panel.open)refresh();
    }
    function renderCurrent(panel,city){
      const result=currentMarkup(city);
      panel.querySelector("[data-incidents-current]").innerHTML=result.html;
      panel.querySelector("[data-incidents-summary]").textContent=
        result.active?result.active+" ambiente(s) em ocorrência":
          result.stale?result.stale+" ambiente(s) sem leitura recente":"Nenhuma indisponibilidade recente";
      panel.classList.toggle("has-failures",result.offline>0);
    }
    async function update(force=false){
      const city=current();
      const panel=layer.querySelector(".ss-map-incidents");
      if(!panel||!city)return;
      renderCurrent(panel,city);
      if(!panel.open)return;
      const now=Date.now();
      if(!force&&events&&loadedKey===city.key&&now-loadTime<120000){
        panel.querySelector("[data-incidents-events]").innerHTML=eventsMarkup(events,city);
        return;
      }
      const token=++loadToken;
      const slot=panel.querySelector("[data-incidents-events]");
      slot.innerHTML='<p class="ss-map-incidents-loading">Consultando eventos registrados…</p>';
      try{
        if(typeof window.ssMapLoadCityEvents!=="function")throw Error("Consulta de eventos não disponível.");
        const result=await window.ssMapLoadCityEvents(city,7);
        if(token!==loadToken||!panel.isConnected||city.key!==key)return;
        events=result;loadedKey=city.key;loadTime=Date.now();
        slot.innerHTML=eventsMarkup(result,city);
      }catch(err){
        if(token!==loadToken||!panel.isConnected)return;
        console.warn("Ocorrências municipais:",err);
        slot.innerHTML='<p class="ss-map-incidents-caution">Não foi possível consultar os eventos. Os estados atuais permanecem disponíveis.</p>';
      }
    }
    layer.addEventListener("ss-map-data-ready",e=>{
      cities=e.detail?.cities||[];
      if(key)update(false);
    });
    layer.addEventListener("ss-map-city-selected",e=>{
      key=e.detail?.key||"";
      loadToken++;events=null;loadedKey="";
      insert(current());
    });
    layer.addEventListener("ss-map-snapshot-updated",()=>{
      if(key)update(false);
    });
    layer.ssMapIncidentRefresh=()=>update(true);
  }
  window.ssMapIncidentsCurrent=currentMarkup;
  window.ssMapIncidentsEvents=eventsMarkup;
  window.ssMapOpen=function(host){
    previous(host);
    const layer=host.querySelector("[data-ss-map]");
    if(layer)attach(layer);
  };
})();
