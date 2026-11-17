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
  /* Uma seção, duas finalidades:
     - Situação atual: estado operacional e diagnóstico dos ambientes.
     - Histórico: todos os eventos do período, consultados pelo componente original.
     O histórico não é duplicado na aba de situação atual. */
  function attach(layer){
    if(layer.dataset.ssMapIncidents)return;
    layer.dataset.ssMapIncidents="1";
    let cities=[],key="";
    const tabByCity=new Map();
    const periodByCity=new Map();
    const expandedByCity=new Map();
    const current=()=>cities.find(c=>c.key===key)||null;

    function renderCurrent(panel,city){
      const result=currentMarkup(city);
      const slot=panel.querySelector("[data-incidents-current]");
      if(slot)slot.innerHTML=result.html;
      const subtitle=panel.querySelector("[data-incidents-summary]");
      if(subtitle)subtitle.textContent=
        result.active?result.active+" ambiente(s) em ocorrência":
          result.stale?result.stale+" ambiente(s) sem leitura recente":
          "Situação atual e histórico de eventos";
      panel.classList.toggle("has-failures",result.offline>0);
    }

    function activateTab(panel,tab,remember=true){
      if(tab!=="current"&&tab!=="history")tab="current";
      if(remember&&key)tabByCity.set(key,tab);
      for(const button of panel.querySelectorAll("[data-monitor-tab]")){
        const selected=button.dataset.monitorTab===tab;
        button.classList.toggle("active",selected);
        button.setAttribute("aria-selected",String(selected));
        button.tabIndex=selected?0:-1;
      }
      for(const view of panel.querySelectorAll("[data-monitor-view]")){
        view.hidden=view.dataset.monitorView!==tab;
      }
      // Abre o histórico somente quando sua aba estiver visível:
      // mantém 24h/7d/30d e evita requisições duplicadas ao Supabase.
      const historical=panel.querySelector(".ss-map-history");
      if(historical)historical.open=panel.open&&tab==="history";
      if(tab==="current")renderCurrent(panel,current());
    }

    function insert(city){
      const detail=layer.querySelector("[data-sm-detail]");
      if(!detail||!city)return;
      const oldHistory=detail.querySelector(".ss-map-history");
      const heading=detail.querySelector("h3");
      if(!heading)return;
      const panel=document.createElement("details");
      panel.className="ss-map-incidents ss-map-monitor";
      panel.innerHTML=
        '<summary><span class="ss-map-incidents-icon" aria-hidden="true">◷</span>'+
        '<span><strong>Monitoramento do Município</strong>'+
        '<small data-incidents-summary>Situação atual e histórico de eventos</small></span>'+
        '<span class="ss-map-incidents-arrow" aria-hidden="true">⌄</span></summary>'+
        '<div class="ss-map-incidents-body ss-map-monitor-body">'+
          '<div class="ss-map-monitor-tabs" role="tablist" aria-label="Informações do município">'+
            '<button type="button" role="tab" id="ss-map-monitor-current-tab" aria-controls="ss-map-monitor-current-panel" aria-selected="true" tabindex="0" class="active" data-monitor-tab="current">Situação atual</button>'+
            '<button type="button" role="tab" id="ss-map-monitor-history-tab" aria-controls="ss-map-monitor-history-panel" aria-selected="false" tabindex="-1" data-monitor-tab="history">Histórico</button>'+
          '</div>'+
          '<section role="tabpanel" id="ss-map-monitor-current-panel" aria-labelledby="ss-map-monitor-current-tab" data-monitor-view="current" class="ss-map-monitor-view">'+
            '<div data-incidents-current></div>'+
            '<button type="button" class="ss-map-incidents-reload" data-incidents-reload>↻ Atualizar situação</button>'+
            '<p class="ss-map-incidents-note">Informações da última verificação. A duração depende da data de início da falha registrada.</p>'+
          '</section>'+
          '<section role="tabpanel" id="ss-map-monitor-history-panel" aria-labelledby="ss-map-monitor-history-tab" data-monitor-view="history" class="ss-map-monitor-view" hidden>'+
            '<div data-monitor-history></div>'+
            '<button type="button" class="ss-map-incidents-reload" data-monitor-history-reload>↻ Atualizar histórico</button>'+
          '</section>'+
        '</div>';
      heading.before(panel);
      const historyContainer=panel.querySelector("[data-monitor-history]");
      if(oldHistory){
        historyContainer.appendChild(oldHistory);
        // O seletor e a consulta do histórico antigo são preservados.
        const savedPeriod=periodByCity.get(city.key)||"7";
        if(savedPeriod!=="7"){
          oldHistory.querySelector('[data-history-days="'+savedPeriod+'"]')?.click();
        }
        oldHistory.open=false;
      }else{
        historyContainer.textContent="Histórico temporariamente indisponível para este município.";
      }
      const tabs=panel.querySelectorAll("[data-monitor-tab]");
      tabs.forEach(button=>{
        button.addEventListener("click",()=>activateTab(panel,button.dataset.monitorTab));
        button.addEventListener("keydown",event=>{
          const index=[...tabs].indexOf(button);
          let next=-1;
          if(event.key==="ArrowRight")next=(index+1)%tabs.length;
          if(event.key==="ArrowLeft")next=(index+tabs.length-1)%tabs.length;
          if(event.key==="Home")next=0;
          if(event.key==="End")next=tabs.length-1;
          if(next>=0){
            event.preventDefault();
            const nextButton=tabs[next];
            activateTab(panel,nextButton.dataset.monitorTab);
            nextButton.focus();
          }
        });
      });
      panel.addEventListener("click",event=>{
        const days=event.target.closest?.("[data-history-days]");
        if(days&&panel.contains(days)&&["1","7","30"].includes(days.dataset.historyDays)){
          periodByCity.set(key,days.dataset.historyDays);
        }
      });
      panel.querySelector("[data-incidents-reload]").addEventListener("click",()=>{
        if(typeof layer.ssMapRefreshNow==="function")layer.ssMapRefreshNow();
        else renderCurrent(panel,current());
      });
      panel.querySelector("[data-monitor-history-reload]").addEventListener("click",()=>{
        const history=panel.querySelector(".ss-map-history");
        const active=history?.querySelector("[data-history-days].active");
        if(active)active.click();
      });
      panel.addEventListener("toggle",()=>{
        expandedByCity.set(city.key,panel.open);
        activateTab(panel,tabByCity.get(city.key)||"current",false);
      });
      const status=currentMarkup(city);
      panel.open=expandedByCity.has(city.key)?expandedByCity.get(city.key):status.active>0;
      renderCurrent(panel,city);
      activateTab(panel,tabByCity.get(city.key)||"current",false);
    }

    function update(){
      const panel=layer.querySelector(".ss-map-monitor");
      const city=current();
      if(panel&&city)renderCurrent(panel,city);
    }
    layer.addEventListener("ss-map-data-ready",event=>{
      cities=event.detail?.cities||[];
      update();
    });
    layer.addEventListener("ss-map-city-selected",event=>{
      key=event.detail?.key||"";
      insert(current());
    });
    layer.addEventListener("ss-map-snapshot-updated",update);
    layer.ssMapIncidentRefresh=()=>{
      if(typeof layer.ssMapRefreshNow==="function")return layer.ssMapRefreshNow();
      return update();
    };
  }
  window.ssMapIncidentsCurrent=currentMarkup;
  window.ssMapIncidentsEvents=eventsMarkup;
  window.ssMapOpen=function(host){
    previous(host);
    const layer=host.querySelector("[data-ss-map]");
    if(layer)attach(layer);
  };
})();
