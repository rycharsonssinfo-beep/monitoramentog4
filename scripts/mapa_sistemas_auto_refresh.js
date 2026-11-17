/* Atualização automática — Monitor Grupo S&S, Mapa de Sistemas.
 * Consulta somente fontes já autorizadas pelo painel; não executa novas sondagens HTTP.
 * Atualiza os dados sem recriar SVG, zoom ou controles de município.
 */
(function ssMapAutoSyncInstall(){
  if(window.__ssMapAutoSyncInstalled)return;
  const previous=window.ssMapOpen;
  if(typeof previous!=="function")return;
  window.__ssMapAutoSyncInstalled=true;
  const PERIOD=60000;
  const fmt=t=>t?new Date(t).toLocaleTimeString("pt-BR"):"—";
  function attach(layer){
    if(layer.dataset.ssMapAutoSync)return;
    layer.dataset.ssMapAutoSync="1";
    const bar=document.createElement("div");
    bar.className="ss-map-syncbar";
    bar.innerHTML=
      '<div class="ss-map-sync-details">'+
      '<span class="ss-map-sync-dot" data-sync-dot aria-hidden="true"></span>'+
      '<strong>Atualização automática</strong><span class="ss-map-sync-period">a cada 60 segundos</span>'+
      '<small class="ss-map-sync-description" data-sync-description aria-live="polite">Aguardando a primeira leitura…</small></div>'+
      '<div class="ss-map-sync-actions"><span data-sync-clock>Última sincronização: —</span>'+
      '<button type="button" data-sync-now disabled>↻ Atualizar agora</button></div>';
    layer.querySelector(".ss-map-head")?.insertAdjacentElement("afterend",bar);
    const btn=bar.querySelector("[data-sync-now]");
    const desc=bar.querySelector("[data-sync-description]");
    const clock=bar.querySelector("[data-sync-clock]");
    let ready=false,busy=false,lastSuccess=0,next=0,lastErrors=[],timer=null,stopped=false;
    function status(text,tone="idle"){
      desc.textContent=text;
      bar.dataset.syncTone=tone;
    }
    function refreshStatus(){
      if(!layer.isConnected){dispose();return}
      const suffix=ready&&!busy&&next?" · próxima em "+Math.max(0,Math.ceil((next-Date.now())/1000))+"s":"";
      clock.textContent="Última sincronização: "+fmt(lastSuccess)+suffix;
    }
    function onFirstReady(e){
      ready=true;
      lastErrors=e.detail?.errors||[];
      lastSuccess=Date.now();
      next=Date.now()+PERIOD;
      btn.disabled=false;
      status(lastErrors.length?
        "Leitura parcial. Fontes com falha: "+lastErrors.join(", "):
        "Dados sincronizados; mapa, seleção e zoom preservados.",
        lastErrors.length?"warning":"ok");
      refreshStatus();
    }
    async function refresh(manual=false){
      if(!ready||busy||!layer.isConnected||typeof layer.ssMapRefresh!=="function")return;
      if(!manual&&document.hidden)return;
      busy=true;btn.disabled=true;bar.classList.add("working");
      status("Consultando as fontes dos sistemas…");
      try{
        const result=await layer.ssMapRefresh();
        if(!layer.isConnected)return;
        if(!result||result.skipped)throw Error("Atualização não concluída.");
        lastSuccess=result.at||Date.now();
        lastErrors=result.errors||[];
        status(lastErrors.length?
          "Atualização parcial; dados anteriores preservados para "+lastErrors.join(", "):
          "Dados sincronizados com sucesso; seleção e filtros preservados.",
          lastErrors.length?"warning":"ok");
      }catch(err){
        console.warn("Mapa S&S: falha na atualização automática",err);
        status("Falha ao sincronizar. Mantida a última leitura válida. Nova tentativa em 60 segundos.","error");
      }finally{
        busy=false;bar.classList.remove("working");
        next=Date.now()+PERIOD;
        btn.disabled=!ready;
        refreshStatus();
      }
    }
    function tick(){
      if(!layer.isConnected){dispose();return}
      refreshStatus();
      if(ready&&!busy&&next&&Date.now()>=next&&!document.hidden)refresh();
    }
    function visibility(){
      if(!document.hidden&&ready&&!busy&&Date.now()>=next)refresh();
    }
    function dispose(){
      if(stopped)return;stopped=true;
      clearInterval(timer);
      document.removeEventListener("visibilitychange",visibility);
    }
    btn.addEventListener("click",()=>refresh(true));
    layer.addEventListener("ss-map-refresh-ready",onFirstReady);
    document.addEventListener("visibilitychange",visibility);
    timer=setInterval(tick,10000);
    // API de teste e atualização por outras seções do monitor, restrita à camada.
    layer.ssMapRefreshNow=()=>refresh(true);
  }
  window.ssMapOpen=function(host){
    previous(host);
    const layer=host.querySelector("[data-ss-map]");
    if(layer)attach(layer);
  };
})();
