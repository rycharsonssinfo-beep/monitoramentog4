/* Monitor Grupo S&S — alertas v3.53.0 | somente Portal do Contribuinte. */
(function(){
"use strict";
if (window.ssPortalAlerts353) return;
const CONFIG_KEY="ss_portais_alertas_v353", SEEN_KEY="ss_portais_alertas_emitidos_v353";
const DEFAULTS={enabled:true,minutes:10,sound:true,volume:65,repeat:0,recovery:true,autoDismissSeconds:20};
const readJson=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key)||"null")||fallback;}catch(_){return fallback;}};
const options=Object.assign({},DEFAULTS,readJson(CONFIG_KEY,{}));
const seen=readJson(SEEN_KEY,{});
let mascot="",stateFn=null,fetcher=null,detailsFn=null,latest=[],active=null,lastRead=0,bgStarted=false;
const outages=new Map(); // Última queda conhecida por município, inclusive durante recuperação
const pendingRecoveries=[]; // Mantém múltiplos avisos de recuperação até serem exibidos
let ac=null,audioUnlocked=false,bgBusy=false,autoDismissTimer=null;
const html=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ms=v=>{const d=Date.parse(v||"");return Number.isFinite(d)?d:NaN;};
const now=()=>Date.now();
function saveOptions(){try{localStorage.setItem(CONFIG_KEY,JSON.stringify(options));}catch(_){}}
function saveSeen(){
  try{
    const keys=Object.keys(seen).sort((a,b)=>(seen[b]||0)-(seen[a]||0)).slice(0,400);
    const compact={};for(const key of keys)compact[key]=seen[key];
    localStorage.setItem(SEEN_KEY,JSON.stringify(compact));
  }catch(_){}
}
function rowId(row){return String(row.id||row.municipio||"");}
function outageKey(row){return rowId(row)+"|"+String(row.mudou_em||row.inicio_falha||"");}
function state(row){try{return stateFn?stateFn(row):String(row.estado||"");}catch(_){return "nao_verificado";}}
function eligible(row){
  if(!row||!options.enabled||state(row)!=="offline")return false;
  const started=ms(row.mudou_em||row.inicio_falha),verified=ms(row.ultima_verificacao);
  return Number.isFinite(started)&&Number.isFinite(verified)&&verified>=started
    &&verified-started>=Number(options.minutes)*60000
    &&now()-verified>=0&&now()-verified<=180000;
}
function elapsed(row){const t=ms(row.mudou_em||row.inicio_falha);return Number.isFinite(t)?Math.max(0,Math.floor((now()-t)/60000)):0;}
function durationParts(totalMinutes){
  const m=Math.max(0,Math.floor(Number(totalMinutes)||0));
  if(m<60)return {number:String(m),unit:"min"};
  return {number:Math.floor(m/60)+"h",unit:String(m%60).padStart(2,"0")+"min"};
}
function refreshAudioBadge(){
  const el=document.getElementById("ss-portal-alert-v353");
  const slot=el&&el.querySelector(".sspa-slot");
  const badge=slot&&slot.querySelector("[data-sspa-audio]");
  if(!badge)return;
  badge.className=audioUnlocked?"sspa-audio-ok":"sspa-audio-warn";
  badge.textContent=audioUnlocked?"Áudio autorizado neste navegador":"O som depende da permissão do navegador";
}
function refreshDurationDisplay(){
  if(!active||active.type!=="offline")return;
  const el=document.getElementById("ss-portal-alert-v353");
  if(!el||!el.classList.contains("visible"))return;
  const slot=el.querySelector(".sspa-slot");
  const value=slot&&slot.querySelector("[data-sspa-duration-value]");
  const unit=slot&&slot.querySelector("[data-sspa-duration-unit]");
  if(!value||!unit)return;
  const duration=durationParts(elapsed(active.row));
  value.textContent=duration.number;
  unit.textContent=duration.unit;
  const verified=slot.querySelector("[data-sspa-verified]");
  if(verified)verified.textContent=timeLabel(active.row.ultima_verificacao);
}
function timeLabel(date){const t=ms(date);return Number.isFinite(t)?new Date(t).toLocaleString("pt-BR"):"Não informada";}
function playAudio(force){
  if((!options.sound&&!force)||Number(options.volume)<=0)return;
  if(!force&&(!active||active.silent||active.type==="recovery"))return;
  try{
    const AC=window.AudioContext||window.webkitAudioContext;
    if(!AC)return;
    ac=ac||new AC();
    const run=()=>{
      audioUnlocked=ac.state==="running";
      refreshAudioBadge();
      if(!audioUnlocked)return;
      [0,.24,.48].forEach((offset,i)=>{
        const o=ac.createOscillator(),g=ac.createGain(),t=ac.currentTime+offset;
        o.type="sine";o.frequency.value=i===1?660:880;
        g.gain.setValueAtTime(.0001,t);
        g.gain.exponentialRampToValueAtTime(Math.max(.001,Math.min(100,Number(options.volume))/900),t+.025);
        g.gain.exponentialRampToValueAtTime(.0001,t+.18);
        o.connect(g);g.connect(ac.destination);o.start(t);o.stop(t+.2);
      });
    };
    if(ac.state==="suspended")ac.resume().then(run).catch(()=>{audioUnlocked=false;});
    else run();
    if(active&&!force)active.lastSound=now();
  }catch(_){audioUnlocked=false;}
}
const styles=[
"#ss-portal-alert-v353{position:fixed;inset:0;z-index:2147482000;display:none;align-items:center;justify-content:center;padding:14px;box-sizing:border-box;background:rgba(12,32,55,.53);font-family:Arial,Helvetica,sans-serif}",
"#ss-portal-alert-v353.visible{display:flex}",
"#ss-portal-alert-v353 .sspa-card{box-sizing:border-box;width:min(890px,96vw);max-height:94vh;overflow-y:auto;border-radius:23px;border-top:5px solid #d83d48;background:white;color:#173c5c;padding:22px 24px 18px;box-shadow:0 19px 60px #0b25464d}",
"#ss-portal-alert-v353 .sspa-head{display:flex;align-items:center;gap:10px;font-size:clamp(17px,2.3vw,25px);font-weight:800}",
"#ss-portal-alert-v353 .sspa-x{margin-left:auto;border:0;background:transparent;color:#173c5c;font-size:29px;cursor:pointer}",
"#ss-portal-alert-v353 .sspa-body{display:flex;align-items:center;gap:18px;margin:14px 0 10px}",
"#ss-portal-alert-v353 .sspa-mascot{width:34%;max-width:260px;max-height:310px;object-fit:contain}",
"#ss-portal-alert-v353 .sspa-info{flex:1;border-left:1px solid #dce5ef;padding-left:23px}",
"#ss-portal-alert-v353 h2{font-size:clamp(18px,2.3vw,27px);line-height:1.22;margin:0 0 10px}",
"#ss-portal-alert-v353 p{margin:10px 0;line-height:1.5}",
"#ss-portal-alert-v353 .sspa-status{display:inline-block;border-radius:20px;background:#d73540;color:white;font-weight:750;padding:7px 13px}",
"#ss-portal-alert-v353 .sspa-note{font-size:12px;color:#61778b;margin-top:8px}",
"#ss-portal-alert-v353 .sspa-kpi{min-width:0;margin:14px 0 11px;padding:12px 16px;border:1px solid #d7e6f4;border-radius:16px;background:linear-gradient(180deg,#f4f9ff 0%,#ebf4fc 100%)}",
"#ss-portal-alert-v353 .sspa-kpi.sspa-kpi-recovery{border-color:#d3eade;background:linear-gradient(180deg,#f3fbf6 0%,#e8f6ee 100%)}",
"#ss-portal-alert-v353 .sspa-kpi-label{margin-bottom:7px;font-size:12px;font-weight:800;letter-spacing:.075em;color:#58748d;text-transform:uppercase}",
"#ss-portal-alert-v353 .sspa-kpi-row{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px}",
"#ss-portal-alert-v353 .sspa-kpi-value{font-size:clamp(34px,4.5vw,46px);line-height:1.05;font-weight:900;color:#114f7d;font-variant-numeric:tabular-nums}",
"#ss-portal-alert-v353 .sspa-kpi-unit{font-size:clamp(17px,2vw,21px);font-weight:800;color:#2b648d}",
"#ss-portal-alert-v353 .sspa-kpi-recovery .sspa-kpi-value,#ss-portal-alert-v353 .sspa-kpi-recovery .sspa-kpi-unit{color:#147451}",
"#ss-portal-alert-v353 .sspa-meta{font-size:13px;color:#526d84}",
"#ss-portal-alert-v353 .sspa-meta p{margin:5px 0}",
"#ss-portal-alert-v353 .sspa-audio-ok,#ss-portal-alert-v353 .sspa-audio-warn{display:inline-flex;align-items:center;border-radius:999px;padding:6px 10px;font-weight:700;font-size:12px;line-height:1.2}",
"#ss-portal-alert-v353 .sspa-audio-ok{background:#eefaf3;color:#176842;border:1px solid #ccead9}",
"#ss-portal-alert-v353 .sspa-audio-warn{background:#fff8e9;color:#846018;border:1px solid #f0dfb6}",
"#ss-portal-alert-v353 .sspa-actions{display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;margin-top:9px}",
"#ss-portal-alert-v353 button.sspa-btn{cursor:pointer;border:1px solid #a8bfd1;background:white;color:#184d73;border-radius:10px;padding:11px 16px;font-weight:750}",
"#ss-portal-alert-v353 button.sspa-primary{background:#0c5487;color:white;border-color:#0c5487}",
"#ss-portal-alert-v353 .sspa-form{display:grid;grid-template-columns:1fr 1fr;gap:20px 15px;margin:22px 0}",
"#ss-portal-alert-v353 .sspa-form label{display:flex;align-items:center;gap:8px}",
"#ss-portal-alert-v353 .sspa-form input,#ss-portal-alert-v353 .sspa-form select{accent-color:#0c5487}",
"#ss-portal-alert-v353 .sspa-form select{padding:6px;border-radius:7px;border:1px solid #b5c8d8}",
"@media(max-width:650px){#ss-portal-alert-v353 .sspa-card{padding:16px}#ss-portal-alert-v353 .sspa-body{flex-direction:column}#ss-portal-alert-v353 .sspa-mascot{width:42%;max-height:150px}#ss-portal-alert-v353 .sspa-info{width:100%;border-left:0;padding-left:0}#ss-portal-alert-v353 .sspa-form{grid-template-columns:1fr}}"
].join("");
function getModal(){
  let el=document.getElementById("ss-portal-alert-v353");if(el)return el;
  el=document.createElement("div");el.id="ss-portal-alert-v353";
  el.innerHTML="<style>"+styles+"</style><section class='sspa-card' role='dialog' aria-modal='true' aria-labelledby='sspa-title'><div class='sspa-slot'></div></section>";
  document.body.appendChild(el);return el;
}
function hide(){const el=getModal();el.classList.remove("visible");el.querySelector(".sspa-slot").innerHTML="";}
function cancelAutoDismiss(){
  if(autoDismissTimer!==null)clearTimeout(autoDismissTimer);
  autoDismissTimer=null;
}
function scheduleAutoDismiss(){
  cancelAutoDismiss();
  if(!active||active.type==="config")return;
  const seconds=Math.max(8,Math.min(120,Number(options.autoDismissSeconds)||20));
  autoDismissTimer=setTimeout(()=>{
    autoDismissTimer=null;
    if(active&&active.type!=="config")dismiss();
  },seconds*1000);
}
function dismiss(){
  cancelAutoDismiss();
  const previous=active;active=null;hide();
  if(previous&&previous.type==="offline"){seen[previous.key]=now();saveSeen();}
  if(previous&&previous.type==="test")return;
  // Apresenta outro município pendente sem repetir a ocorrência dispensada.
  if(previous&&previous.type!=="config")setTimeout(()=>process(latest),300);
}
function markActive(row,type){
  cancelAutoDismiss();
  active={row:row||{},type:type||"offline",key:outageKey(row||{}),lastSound:0,silent:false,expanded:false};
  if(type==="offline"){seen[active.key]=now();saveSeen();}
  render();
  scheduleAutoDismiss();
  if(type==="offline"||type==="test")playAudio(false);
}
function button(el,selector,fn){const node=el.querySelector(selector);if(node)node.onclick=fn;}
function render(){
  if(!active)return;
  const el=getModal(),slot=el.querySelector(".sspa-slot"),r=active.row||{},type=active.type;
  const config=type==="config",test=type==="test",recovery=type==="recovery";
  const title=config?"Configurações dos alertas":test?"Teste de alerta — simulação":recovery?"Portal restabelecido":"Alerta de indisponibilidade confirmada";
  const logo=mascot?"<img class='sspa-mascot' src='"+html(mascot)+"' alt='Mascote de alerta S&S'>":"<span class='sspa-mascot' aria-hidden='true' style='font-size:74px;text-align:center'>⚠</span>";
  const municipality=html(r.municipio||"Município de teste");
  const duration=durationParts(test?11:recovery?Number(r.__durationMin||0):elapsed(r));
  const kpiLabel=test?"TEMPO SIMULADO DE QUEDA":recovery?"DURAÇÃO DA INDISPONIBILIDADE":"INDISPONÍVEL HÁ";
  const audioBadge="<span data-sspa-audio class='"+(audioUnlocked?"sspa-audio-ok":"sspa-audio-warn")+"'>"+
    (audioUnlocked?"Áudio autorizado neste navegador":"O som depende da permissão do navegador")+"</span>";
  const cfg="<div class='sspa-form'>"
    +"<label><input data-opt='enabled' type='checkbox'> Ativar notificações</label>"
    +"<label>Tempo mínimo <select data-opt='minutes'><option value='5'>5 min</option><option value='10'>10 min</option><option value='15'>15 min</option><option value='30'>30 min</option></select></label>"
    +"<label><input data-opt='sound' type='checkbox'> Sinal sonoro</label>"
    +"<label>Volume <input data-opt='volume' type='range' min='0' max='100' step='5'><span data-volume-label></span></label>"
    +"<label>Repetição <select data-opt='repeat'><option value='0'>Uma vez</option><option value='5'>A cada 5 min</option><option value='10'>A cada 10 min</option></select></label>"
    +"<label><input data-opt='recovery' type='checkbox'> Avisar recuperação</label>"
    +"<label>Duração do aviso <select data-opt='autoDismissSeconds'><option value='10'>10 s</option><option value='15'>15 s</option><option value='20'>20 s</option><option value='30'>30 s</option><option value='45'>45 s</option></select></label></div>"
    +"<p class='sspa-note'>As preferências são salvas neste navegador. Clique em Testar alerta para autorizar o áudio, se necessário.</p>";
  const info="<div class='sspa-body'>"+logo+"<div class='sspa-info'>"
    +"<h2 id='sspa-title'>"+(test?"Simulação visual e sonora":recovery?municipality+" voltou a funcionar":municipality+" está indisponível")+"</h2>"
    +"<span class='sspa-status' "+(recovery?"style='background:#179765'":"")+">"+(test?"MODO DE TESTE":recovery?"Recuperado":"Queda confirmada")+"</span>"
    +"<div class='sspa-kpi"+(recovery?" sspa-kpi-recovery":"")+"'>"
    +"<div class='sspa-kpi-label'>"+kpiLabel+"</div>"
    +"<div class='sspa-kpi-row' role='timer' aria-live='off'><strong class='sspa-kpi-value' data-sspa-duration-value>"+html(duration.number)+"</strong>"
    +"<span class='sspa-kpi-unit' data-sspa-duration-unit>"+html(duration.unit)+"</span></div></div>"
    +"<div class='sspa-meta'><p>Última verificação: <b data-sspa-verified>"+
      html(timeLabel(r.ultima_verificacao||(test?new Date().toISOString():null)))+"</b></p>"
    +(active.expanded?"<p>Identificador: "+html(rowId(r))+"</p><p>Estado HTTP: "+html(r.http_status==null?"Sem resposta":r.http_status)+"</p><p>Detalhe: "+html(r.detalhe||"Não informado")+"</p>":"")
    +"</div><p class='sspa-note'>"+audioBadge+"</p>"
    +"</div></div>";
  slot.innerHTML="<div class='sspa-head'><span style='color:#d73540'>⚠</span><span>"+title+"</span><button class='sspa-x' type='button' aria-label='Fechar alerta'>×</button></div>"
    +(config?cfg:info)
    +"<div class='sspa-actions'>"
    +"<button type='button' class='sspa-btn sspa-primary' data-action='primary'>"+(config?"Salvar configurações":test?"Testar som":recovery?"Fechar":"Ver detalhes")+"</button>"
    +"<button type='button' class='sspa-btn' data-action='secondary'>"+(config?"Testar alerta":test?"Fechar teste":recovery?"OK":"Silenciar / dispensar")+"</button>"
    +"</div>";
  el.classList.add("visible");
  button(slot,".sspa-x",dismiss);
  button(slot,"[data-action='primary']",()=>{
    if(config){saveOptions();dismiss();return;}
    if(test){playAudio(true);return;}
    if(recovery){dismiss();return;}
    active.expanded=!active.expanded;render();
    if(active.expanded&&typeof detailsFn==="function"){/* Os detalhes já estão no próprio aviso. */}
  });
  button(slot,"[data-action='secondary']",()=>{
    if(config){markActive({municipio:"Município de teste"},"test");return;}
    if(active)active.silent=true;dismiss();
  });
  if(config){
    slot.querySelectorAll("[data-opt]").forEach(node=>{
      const k=node.dataset.opt;node[node.type==="checkbox"?"checked":"value"]=options[k];
      node.oninput=()=>{options[k]=node.type==="checkbox"?node.checked:Number(node.value);saveOptions();const vol=slot.querySelector("[data-volume-label]");if(vol)vol.textContent=options.volume+"%";};
    });
    const vol=slot.querySelector("[data-volume-label]");if(vol)vol.textContent=options.volume+"%";
  }
}
function process(rows){
  if(!options.enabled||!Array.isArray(rows))return;
  latest=rows;lastRead=now();
  const recovered=[];
  for(const row of rows){
    const status=state(row),id=rowId(row);
    if(status==="offline"){outages.set(id,row);continue;}
    if(status!=="online")continue; // "recuperando" ainda não confirma disponibilidade
    const prior=outages.get(id);outages.delete(id);
    if(prior&&seen[outageKey(prior)]){
      const start=ms(prior.mudou_em||prior.inicio_falha);
      const end=ms(row.mudou_em||row.ultima_verificacao);
      const duration=Number.isFinite(start)&&Number.isFinite(end)
        ?Math.max(0,Math.floor((end-start)/60000)):0;
      recovered.push(Object.assign({},row,{__durationMin:duration}));
    }
  }
  // A leitura mais recente atualiza o horário de verificação do alerta aberto.
  if(active&&active.type==="offline"){
    const current=rows.find(row=>rowId(row)===rowId(active.row)&&state(row)==="offline");
    if(current)active.row=current;
  }
  // Não perde avisos quando vários municípios voltam a funcionar juntos.
  for(const row of recovered){
    if(!pendingRecoveries.some(queued=>rowId(queued)===rowId(row)))pendingRecoveries.push(row);
  }
  if(active&&active.type==="offline"){
    const restored=recovered.find(row=>rowId(row)===rowId(active.row));
    if(restored){
      const idx=pendingRecoveries.findIndex(row=>rowId(row)===rowId(restored));
      if(idx>=0)pendingRecoveries.splice(idx,1);
      if(options.recovery){active={row:restored,type:"recovery",key:"",silent:true};render();scheduleAutoDismiss();}
      else dismiss();
      return;
    }
  }
  if(active)return;
  if(options.recovery&&pendingRecoveries.length){
    markActive(pendingRecoveries.shift(),"recovery");return;
  }
  if(!options.recovery)pendingRecoveries.length=0;
  for(const row of rows){
    if(!eligible(row))continue;
    const key=outageKey(row);if(seen[key])continue;
    markActive(row,"offline");break;
  }
}
async function refresh(){
  if(!options.enabled||!fetcher||bgBusy)return;
  // Todas as telas consultam Portais mesmo quando outro painel está visível.
  // Evita apenas duplicação imediatamente após uma leitura nova do próprio painel.
  if(now()-lastRead<12000)return;
  bgBusy=true;
  try{const rows=await fetcher();if(Array.isArray(rows))process(rows);}catch(_){/* não apresentar queda se apenas o Supabase falhou */}
  finally{bgBusy=false;}
}
function start(opts){
  opts=opts||{};
  mascot=opts.mascot||mascot;stateFn=opts.state||stateFn;fetcher=opts.fetch||fetcher;detailsFn=opts.details||detailsFn;
  if(bgStarted)return;bgStarted=true;
  // Mesma estratégia do SIM: polling global, independente do painel em exibição.
  setTimeout(refresh,2500);
  setInterval(refresh,15000);
  if(typeof window.addEventListener==="function")window.addEventListener("focus",refresh);
  if(typeof document.addEventListener==="function")document.addEventListener("visibilitychange",()=>{
    if(!document.hidden)refresh();
  });
  setInterval(()=>{refreshDurationDisplay();if(active&&active.type==="offline"&&!active.silent&&Number(options.repeat)>0
    &&now()-active.lastSound>=Number(options.repeat)*60000)playAudio(false);},15000);
}
function mount(host,mascotSource){
  if(mascotSource)mascot=mascotSource;
  if(!host)return;
  const bar=host.querySelector(".portal-head-meta");
  if(!bar||bar.querySelector("[data-sspa-config]"))return;
  const holder=document.createElement("span");holder.style.cssText="display:inline-flex;gap:6px";
  holder.innerHTML="<button type='button' class='portal-report-trigger' data-sspa-config>🔔 Alertas</button>"
    +"<button type='button' class='portal-report-trigger' data-sspa-test>▶ Testar alerta</button>";
  bar.appendChild(holder);
  button(holder,"[data-sspa-config]",()=>markActive({},"config"));
  button(holder,"[data-sspa-test]",()=>markActive({municipio:"Município de teste"},"test"));
}
window.ssPortalAlerts353={start:start,mount:mount,receive:process,eligible:eligible,showTest:()=>markActive({municipio:"Município de teste"},"test")};
})();