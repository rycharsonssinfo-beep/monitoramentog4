/* Grupo S&S — Operação do Mapa: inteligência de disponibilidade, histórico e gestão.
   Dados da sessão autenticada do Monitor. Não cria históricos nem percentuais de uptime fictícios. */
(function installSsMapOperations(){
  if(window.__ssMapOpsInstalled)return;
  const previous=window.ssMapOpen;
  if(typeof previous!=="function")return;
  window.__ssMapOpsInstalled=true;
  const FRESH_MS=15*60*1000;
  const FUTURE_MS=5*60*1000;
  const MODES=[
    {key:"portais",label:"Portal do Contribuinte",table:"portais_monitor_eventos"},
    {key:"fluxus",label:"Fluxus",table:"fluxus_monitor_eventos"},
    {key:"veiculos",label:"Veículos",table:"veiculos_monitor_eventos"}
  ];
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const fmtDate=value=>{
    const n=Date.parse(String(value||""));
    return Number.isFinite(n)?new Date(n).toLocaleString("pt-BR"):"Não informada";
  };
  const num=n=>Number(n||0).toLocaleString("pt-BR");
  const pct=(numerator,denominator)=>denominator?(100*numerator/denominator).toLocaleString("pt-BR",{maximumFractionDigits:1})+"%":"—";
  function liveState(row, now=Date.now()){
    if(!row||!row.ultima_verificacao)return"sem_leitura";
    const at=Date.parse(row.ultima_verificacao);
    if(!Number.isFinite(at)||at>now+FUTURE_MS)return"sem_leitura";
    if(now-at>FRESH_MS)return"desatualizado";
    const status=String(row.estado||"").toLowerCase();
    if(status==="online")return"online";
    if(status==="offline")return"offline";
    if(["suspeita_falha","recuperando","verificacao_bloqueada"].includes(status))return"observacao";
    return"sem_leitura";
  }
  const statusText={
    online:"Online · verificação recente",
    offline:"Indisponível · verificação recente",
    observacao:"Em observação · verificação recente",
    desatualizado:"Leitura desatualizada",
    sem_leitura:"Sem verificação válida"
  };
  function analyze(cities,now=Date.now()){
    const out={
      municipalities:cities.length,covered:0,systems:{},distribution:[0,0,0,0],
      envs:0,online:0,offline:0,observacao:0,desatualizado:0,sem_leitura:0,
      currentCities:0, latestCheck:0
    };
    MODES.forEach(m=>out.systems[m.key]={municipalities:0,envs:0,online:0,offline:0,observacao:0,desatualizado:0,sem_leitura:0,onlineMunicipalities:0});
    for(const city of cities){
      let registered=0, hasFresh=false;
      for(const m of MODES){
        const rows=city.systems?.[m.key]||[];
        if(rows.length){registered++;out.systems[m.key].municipalities++}
        let hasOnline=false;
        for(const row of rows){
          const state=liveState(row,now);
          out[state]++;out.envs++;
          out.systems[m.key][state]++;
          out.systems[m.key].envs++;
          if(state==="online")hasOnline=true;
          if(["online","offline","observacao"].includes(state))hasFresh=true;
          const dt=Date.parse(row.ultima_verificacao||"");
          if(Number.isFinite(dt)&&dt<=now+FUTURE_MS)out.latestCheck=Math.max(out.latestCheck,dt);
        }
        if(hasOnline)out.systems[m.key].onlineMunicipalities++;
      }
      out.distribution[registered]++;
      if(registered>0)out.covered++;
      if(hasFresh)out.currentCities++;
    }
    return out;
  }
  function safeId(raw){
    const id=String(raw||"");
    return /^[a-zA-Z0-9_:-]{2,150}$/.test(id)?id:"";
  }
  async function loadCityEvents(city,days){
    const since=new Date(Date.now()-days*86400000).toISOString();
    const batches=await Promise.all(MODES.map(async mode=>{
      const ids=[...new Set((city.systems?.[mode.key]||[]).map(r=>safeId(r.id)).filter(Boolean))];
      if(!ids.length)return {mode:mode.key,rows:[],missing:true};
      if(typeof portalFetchTable!=="function")return {mode:mode.key,rows:[],error:"Consulta de eventos indisponível."};
      // IDs do coletor são alfanuméricos: nenhum valor livre entra na expressão PostgREST.
      const query="portal_id=in.("+ids.join(",")+")&ocorrido_em=gte."+
        encodeURIComponent(since)+"&order=ocorrido_em.desc&limit=100";
      try{
        const rows=await portalFetchTable(mode.table,
          "evento_id,portal_id,municipio,ocorrido_em,estado_anterior,estado_atual,codigo_http,detalhe",query);
        if(!Array.isArray(rows))throw Error("Retorno inválido.");
        return {mode:mode.key,rows:rows.slice(0,100),truncated:rows.length===100};
      }catch(err){
        console.warn("Histórico do Mapa: "+mode.key,err);
        return {mode:mode.key,rows:[],error:"Falha na consulta ou permissão de leitura."};
      }
    }));
    return batches;
  }
  function renderSmartStatuses(layer,city,now){
    if(!city)return;
    for(const mode of MODES){
      const rows=city.systems?.[mode.key]||[];
      const entries=layer.querySelectorAll(".ss-map-detail .ss-map-service-"+mode.key+" .ss-map-service-entry");
      entries.forEach((node,i)=>{
        const record=rows[i];if(!record)return;
        const state=liveState(record,now);
        const label=node.querySelector(".ss-map-read-status");
        if(!label)return;
        label.className="ss-map-read-status ss-map-ops-"+state;
        label.textContent=statusText[state];
        label.title="Última verificação: "+fmtDate(record.ultima_verificacao);
        let age=node.querySelector(".ss-map-ops-lastcheck");
        if(!age){age=document.createElement("small");age.className="ss-map-ops-lastcheck";label.after(age)}
        age.textContent="Última verificação: "+fmtDate(record.ultima_verificacao);
      });
    }
  }
  function createHistory(layer,city){
    const detail=layer.querySelector("[data-sm-detail]");
    if(!detail)return;
    const h3=detail.querySelector("h3");
    if(!h3)return;
    const section=document.createElement("details");
    section.className="ss-map-history";
    section.innerHTML=
      '<summary><span class="ss-map-history-icon" aria-hidden="true">◷</span>'+
      '<span><strong>Histórico do município</strong><small>Ocorrências registradas por sistema</small></span>'+
      '<span class="ss-map-history-chevron" aria-hidden="true">⌄</span></summary>'+
      '<div class="ss-map-history-body">'+
      '<div class="ss-map-history-toolbar" role="group" aria-label="Período do histórico">'+
      '<button type="button" data-history-days="1">24 horas</button>'+
      '<button type="button" data-history-days="7" class="active">7 dias</button>'+
      '<button type="button" data-history-days="30">30 dias</button></div>'+
      '<div class="ss-map-history-content" aria-live="polite">Selecione um período para consultar os eventos.</div>'+
      '</div>';
    h3.insertAdjacentElement("beforebegin",section);
    const content=section.querySelector(".ss-map-history-content");
    let request=0,days=7;
    async function reload(){
      const thisRequest=++request;
      content.innerHTML='<p class="ss-map-history-loading">Consultando os eventos registrados…</p>';
      const groups=await loadCityEvents(city,days);
      if(thisRequest!==request||!section.isConnected||!section.open)return;
      const all=[];
      const errors=[],limitations=[];
      groups.forEach(group=>{
        const mode=MODES.find(m=>m.key===group.mode);
        if(group.error)errors.push(mode.label);
        if(group.missing&&(city.systems?.[group.mode]||[]).length)limitations.push(mode.label);
        if(group.truncated)limitations.push(mode.label+" (limite de 100 eventos por sistema)");
        for(const e of group.rows)all.push({...e,mode:group.mode,label:mode.label});
      });
      all.sort((a,b)=>Date.parse(b.ocorrido_em||"")-Date.parse(a.ocorrido_em||""));
      const shown=all.slice(0,45);
      let html='<div class="ss-map-history-total"><b>'+num(all.length)+'</b> evento(s) encontrado(s)'+
        (all.length>45?' · exibindo os 45 mais recentes':'')+'</div>';
      if(errors.length)html+='<p class="ss-map-history-error">Não foi possível consultar: '+esc(errors.join(", "))+
        '. Confira a rede e as permissões de leitura.</p>';
      if(limitations.length)html+='<p class="ss-map-history-error">Cobertura parcial: '+esc(limitations.join("; "))+'.</p>';
      if(!shown.length)html+='<p class="ss-map-history-empty">Nenhuma mudança de estado registrada neste período para os ambientes identificados.</p>';
      else html+='<ol class="ss-map-history-list">'+shown.map(e=>{
        const at=fmtDate(e.ocorrido_em);
        const before=String(e.estado_anterior||"sem informação").replaceAll("_"," ");
        const after=String(e.estado_atual||"sem informação").replaceAll("_"," ");
        const detail=String(e.detalhe||"").trim().slice(0,140);
        return '<li><div><span class="ss-map-history-system">'+esc(e.label)+'</span>'+
          '<time>'+esc(at)+'</time></div>'+
          '<strong>'+esc(before)+' → '+esc(after)+'</strong>'+
          (e.codigo_http?'<small>HTTP '+esc(e.codigo_http)+'</small>':'')+
          (detail?'<p>'+esc(detail)+'</p>':'')+'</li>';
      }).join("")+'</ol>';
      html+='<p class="ss-map-history-note">Fonte: eventos gravados pelos coletores. Não representa o total de verificações nem calcula percentual de uptime.</p>';
      content.innerHTML=html;
    }
    section.addEventListener("toggle",()=>{if(section.open)reload();else request++});
    section.querySelectorAll("[data-history-days]").forEach(btn=>
      btn.addEventListener("click",()=>{
        days=Number(btn.dataset.historyDays);
        section.querySelectorAll("[data-history-days]").forEach(b=>b.classList.toggle("active",b===btn));
        if(section.open)reload();
      }));
  }
  function managerialMarkup(cities,stats,errors){
    const dist=stats.distribution;
    const bars=MODES.map(mode=>{
      const v=stats.systems[mode.key],share=stats.municipalities?100*v.municipalities/stats.municipalities:0;
      return '<div class="ss-map-mgmt-line">'+
        '<div class="ss-map-mgmt-line-title"><strong>'+esc(mode.label)+'</strong><span>'+
        num(v.municipalities)+' municípios · '+num(v.envs)+' ambientes</span></div>'+
        '<div class="ss-map-mgmt-progress"><div style="width:'+Math.max(0,Math.min(100,share))+'%"></div></div>'+
        '<small>'+pct(v.municipalities,stats.municipalities)+' de municípios do CE</small></div>';
    }).join("");
    const distRows=dist.map((v,n)=>{
      const size=stats.municipalities?100*v/stats.municipalities:0;
      return '<div class="ss-map-mgmt-distribution-row"><span>'+n+' sistema'+(n!==1?'s':'')+'</span>'+
        '<div class="ss-map-mgmt-progress"><div style="width:'+Math.max(0,Math.min(100,size))+'%"></div></div>'+
        '<strong>'+num(v)+'</strong></div>';
    }).join("");
    const quality=[
      ["Online recente",stats.online,"online"],
      ["Indisponível recente",stats.offline,"offline"],
      ["Em observação",stats.observacao,"observacao"],
      ["Leitura desatualizada",stats.desatualizado,"desatualizado"],
      ["Sem leitura válida",stats.sem_leitura,"sem_leitura"]
    ].map(([label,value,color])=>'<div class="ss-map-mgmt-quality '+color+'"><span>'+esc(label)+'</span><b>'+num(value)+'</b></div>').join("");
    const best=[...cities].filter(c=>MODES.every(m=>(c.systems?.[m.key]||[]).length))
      .sort((a,b)=>a.name.localeCompare(b.name,"pt-BR")).slice(0,16);
    return '<div class="ss-map-mgmt-intro"><span>VISÃO GERENCIAL · CEARÁ</span>'+
      '<h2>Painel Gerencial de Cobertura</h2>'+
      '<p>Distribuição territorial e qualidade das últimas verificações dos sistemas cadastrados.</p></div>'+
      (errors?.length?'<p class="ss-map-mgmt-warn">Fonte(s) não consultada(s): '+esc(errors.join(", "))+'. Indicadores cadastrais podem estar incompletos.</p>':'')+
      '<div class="ss-map-mgmt-kpis">'+
      [['Municípios do CE',stats.municipalities],['Municípios atendidos',stats.covered],
        ['Cobertura territorial',pct(stats.covered,stats.municipalities)],
        ['Ambientes cadastrados',stats.envs],
        ['Online recente',stats.online],
        ['Leitura desatualizada',stats.desatualizado]].map(([label,n])=>
          '<div class="ss-map-mgmt-kpi"><b>'+esc(n)+'</b><small>'+esc(label)+'</small></div>').join("")+
      '</div>'+
      '<div class="ss-map-mgmt-sections">'+
      '<section class="ss-map-mgmt-box"><h3>Cobertura por sistema</h3>'+
        '<p>Municípios com pelo menos um ambiente de cada sistema.</p>'+bars+'</section>'+
      '<section class="ss-map-mgmt-box"><h3>Quantidade de sistemas por município</h3>'+
        '<p>Cada município é contado uma única vez.</p>'+distRows+'</section>'+
      '<section class="ss-map-mgmt-box"><h3>Confiabilidade da última leitura</h3>'+
        '<p>Quantidade de ambientes por situação operacional.</p>'+quality+'</section>'+
      '<section class="ss-map-mgmt-box"><h3>Municípios com os 3 sistemas</h3>'+
        '<p>'+num(dist[3])+' municípios com Portal, Fluxus e Veículos.</p>'+
        '<div class="ss-map-mgmt-town-list">'+(best.length?best.map(c=>'<span>'+esc(c.name)+'</span>').join(""):'Nenhum município identificado.')+'</div>'+
        (dist[3]>best.length?'<small>Exibindo os 16 primeiros por ordem alfabética.</small>':'')+'</section></div>'+
      '<p class="ss-map-mgmt-note">Critério: leitura recente = última verificação há no máximo 15 minutos. Estes indicadores não equivalem a disponibilidade contínua; mudanças históricas de contrato não são inferidas a partir dos eventos.</p>';
  }
  function renderManager(layer,cities,errors){
    layer.querySelector(".ss-map-mgmt-backdrop")?.remove();
    const overlay=document.createElement("div");
    overlay.className="ss-map-mgmt-backdrop";
    overlay.innerHTML='<section role="dialog" aria-modal="true" aria-label="Painel Gerencial de Cobertura" class="ss-map-mgmt-window">'+
      '<div class="ss-map-mgmt-top"><strong>Painel Gerencial</strong>'+
      '<button type="button" class="ss-map-mgmt-close" aria-label="Fechar painel">✕</button></div>'+
      '<div class="ss-map-mgmt-body">'+managerialMarkup(cities,analyze(cities),errors)+'</div></section>';
    layer.append(overlay);
    const close=()=>overlay.remove();
    overlay.querySelector(".ss-map-mgmt-close").onclick=close;
    overlay.addEventListener("click",e=>{if(e.target===overlay)close()});
    overlay.addEventListener("keydown",e=>{if(e.key==="Escape"){e.stopPropagation();close()}});
    overlay.querySelector(".ss-map-mgmt-close").focus();
  }
  function attach(host){
    const layer=host.querySelector("[data-ss-map]");
    if(!layer||layer.dataset.ssMapOperations)return;
    layer.dataset.ssMapOperations="1";
    const store={cities:null,errors:[],current:null};
    const actions=layer.querySelector(".ss-map-report-actions")||layer.querySelector(".ss-map-head");
    const manager=document.createElement("button");
    manager.type="button";manager.className="ss-map-mgmt-open";manager.textContent="▥ Painel Gerencial";
    manager.disabled=true;manager.title="Indicadores e gráficos da cobertura municipal";
    actions.prepend(manager);
    manager.onclick=()=>{
      if(store.cities)renderManager(layer,store.cities,store.errors);
    };
    const stats=layer.querySelector(".ss-map-stats");
    const strip=document.createElement("section");
    strip.className="ss-map-ops-strip";
    strip.setAttribute("role","status");
    strip.setAttribute("aria-live","polite");
    strip.innerHTML='<div class="ss-map-ops-strip-head"><strong><span class="ss-map-ops-dot"></span>Disponibilidade recente</strong>'+
      '<small>Considera a última verificação de até 15 min</small></div>'+
      '<div class="ss-map-ops-values" data-map-ops-values>Carregando verificações…</div>';
    stats.after(strip);
    function repaint(){
      if(!store.cities)return;
      const q=analyze(store.cities);
      const chips=[
        ["Online",q.online,"online"],["Indisponíveis",q.offline,"offline"],
        ["Observação",q.observacao,"observacao"],["Desatualizados",q.desatualizado,"desatualizado"],
        ["Sem leitura",q.sem_leitura,"sem_leitura"]
      ];
      strip.querySelector("[data-map-ops-values]").innerHTML=chips.map(([label,value,key])=>
        '<span class="ss-map-ops-chip '+key+'"><b>'+num(value)+'</b> '+label+'</span>').join("")+
        '<small class="ss-map-ops-last">Última verificação registrada: '+
          esc(q.latestCheck?new Date(q.latestCheck).toLocaleString("pt-BR"):"não informada")+'</small>';
      if(q.envs && !q.online && !q.offline && !q.observacao){
        strip.classList.add("ss-map-ops-alert");
        strip.querySelector(".ss-map-ops-strip-head small").textContent=
          "Nenhuma verificação recente. Os estados anteriores não são confirmados como atuais.";
      }else{
        strip.classList.remove("ss-map-ops-alert");
        strip.querySelector(".ss-map-ops-strip-head small").textContent=
          "Considera a última verificação de até 15 min";
      }
      MODES.forEach(mode=>{
        const elem=layer.querySelector("[data-sm-online-"+mode.key+"]");
        if(elem)elem.textContent=q.systems[mode.key].onlineMunicipalities+
          " municípios online com leitura recente";
      });
      if(store.current)renderSmartStatuses(layer,store.current,Date.now());
    }
    layer.addEventListener("ss-map-data-ready",e=>{
      store.cities=e.detail?.cities||[];
      store.errors=e.detail?.errors||[];
      manager.disabled=false;
      repaint();
      if(store.errors.length){
        const warn=document.createElement("p");
        warn.className="ss-map-ops-warning";
        warn.textContent="Atenção: falha na atualização de "+store.errors.join(", ")+
          ". Os indicadores podem estar incompletos ou desatualizados.";
        strip.after(warn);
      }
    });
    layer.addEventListener("ss-map-city-selected",e=>{
      if(!store.cities)return;
      store.current=store.cities.find(c=>c.key===e.detail?.key)||null;
      renderSmartStatuses(layer,store.current,Date.now());
      if(store.current)createHistory(layer,store.current);
    });
    const timer=setInterval(()=>{if(!layer.isConnected){clearInterval(timer);return}repaint()},60000);
  }
  window.ssMapOperationalState=liveState;
  window.ssMapAnalyzeCoverage=analyze;
  window.ssMapOpen=function(host){previous(host);attach(host)};
})();
