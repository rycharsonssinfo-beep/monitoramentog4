/* Monitor S&S — Portal alerts v3.53.0. Scope: Portal do Contribuinte only. */
(function(){
'use strict';
const STORE='ss_portais_alertas_v353',ACK='ss_portais_alertas_confirmados_v353';
const opts=Object.assign({enabled:true,minutes:10,sound:true,volume:65,repeat:0,recovery:true},JSON.parse(localStorage.getItem(STORE)||'{}'));
let seen={};try{seen=JSON.parse(localStorage.getItem(ACK)||'{}')||{};}catch(e){}
let audio=null,active='',lastSound={};
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const save=()=>{try{localStorage.setItem(STORE,JSON.stringify(opts));}catch(e){}};
function sound(){if(!opts.sound)return;try{
const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;audio=audio||new AC();audio.resume().then(()=>{
[0,.24,.48].forEach((delay,i)=>{const o=audio.createOscillator(),g=audio.createGain(),t=audio.currentTime+delay;
o.type='sine';o.frequency.value=i===1?660:880;g.gain.setValueAtTime(.0001,t);
g.gain.exponentialRampToValueAtTime(Math.max(.001,opts.volume/900),t+.025);
g.gain.exponentialRampToValueAtTime(.0001,t+.19);o.connect(g);g.connect(audio.destination);o.start(t);o.stop(t+.2);});});}catch(e){}
}
function modal(){
let el=document.getElementById('ss-portal-alert-modal');if(el)return el;
el=document.createElement('div');el.id='ss-portal-alert-modal';
el.innerHTML='<style>'+
'#ss-portal-alert-modal{position:fixed;inset:0;z-index:2147483000;display:none;align-items:center;justify-content:center;padding:18px;background:#132d4a85;box-sizing:border-box}'+
'#ss-portal-alert-modal.show{display:flex}#ss-portal-alert-modal article{width:min(880px,96vw);max-height:90vh;overflow:auto;border-radius:22px;border-top:5px solid #e43d47;background:#fff;color:#163b60;padding:25px;box-shadow:0 18px 65px #16345055;font-family:inherit}'+
'#ss-portal-alert-modal header{display:flex;align-items:center;gap:12px;font-size:clamp(18px,2vw,25px);font-weight:850}#ss-portal-alert-modal .pa-close{margin-left:auto;background:transparent;color:#163b60;border:0;font-size:25px;cursor:pointer}'+
'#ss-portal-alert-modal .pa-body{display:flex;align-items:center;gap:25px;margin:18px 0}#ss-portal-alert-modal .pa-mascot{width:32%;max-height:325px;object-fit:contain}#ss-portal-alert-modal .pa-copy{flex:1;border-left:1px solid #dae6f1;padding-left:23px}'+
'#ss-portal-alert-modal h2{font-size:clamp(20px,2.4vw,29px);margin:0 0 12px;line-height:1.2}#ss-portal-alert-modal .pa-pill{display:inline-block;border-radius:20px;background:#d62c35;color:white;padding:7px 14px;font-weight:800}'+
'#ss-portal-alert-modal p{line-height:1.45}#ss-portal-alert-modal footer{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-end}#ss-portal-alert-modal .pa-btn{border-radius:9px;padding:11px 16px;cursor:pointer;font-weight:800;border:1px solid #9ab6cc;background:white;color:#205074}#ss-portal-alert-modal .pa-main{background:#095184;border-color:#095184;color:white}'+
'#ss-portal-alert-modal .pa-grid{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin:18px 0}#ss-portal-alert-modal .pa-grid label{display:flex;align-items:center;gap:9px}'+
'@media(max-width:650px){#ss-portal-alert-modal .pa-body{flex-direction:column}#ss-portal-alert-modal .pa-mascot{width:45%;max-height:150px}#ss-portal-alert-modal .pa-copy{border-left:0;padding-left:0}#ss-portal-alert-modal .pa-grid{grid-template-columns:1fr}}'+
'</style><article role="dialog" aria-modal="true"><div class="pa-content"></div></article>';
document.body.appendChild(el);return el;
}
function close(){modal().classList.remove('show');active='';}
function acknowledge(row){const k=key(row);seen[k]=Date.now();try{localStorage.setItem(ACK,JSON.stringify(Object.fromEntries(Object.entries(seen).sort((a,b)=>b[1]-a[1]).slice(0,250))));}catch(e){}}
function key(row){return 'offline:'+String(row.id||row.municipio)+':'+String(row.mudou_em||row.inicio_falha||'');}
function show(row={},type='offline',mascot=''){
const el=modal(),test=type==='test',config=type==='config',recovered=type==='recovered';
active=type+':'+(row.id||row.municipio||'settings');
const name=esc(row.municipio||'Município de teste'),ts=Date.parse(row.mudou_em||row.inicio_falha||'');
const min=test?11:Number.isFinite(ts)?Math.max(0,Math.floor((Date.now()-ts)/60000)):0;
const title=config?'Configurações dos alertas':test?'Teste de alerta — simulação':recovered?'Portal restabelecido':'Alerta de indisponibilidade confirmada';
const mascotHtml=mascot?'<img class="pa-mascot" src="'+esc(mascot)+'" alt="Mascote de alerta S&S">':'<span class="pa-mascot" aria-hidden="true" style="font-size:85px;text-align:center">⚠</span>';
const settingHtml='<div class="pa-grid"><label><input type="checkbox" data-opt="enabled"> Alertas automáticos</label>'+
'<label>Tempo mínimo <select data-opt="minutes"><option value="5">5 minutos</option><option value="10">10 minutos</option><option value="15">15 minutos</option><option value="30">30 minutos</option></select></label>'+
'<label><input type="checkbox" data-opt="sound"> Sinal sonoro</label><label>Volume <input type="range" min="0" max="100" step="5" data-opt="volume"> <span data-vol></span></label>'+
'<label>Repetir <select data-opt="repeat"><option value="0">Uma vez</option><option value="5">A cada 5 min</option><option value="10">A cada 10 min</option></select></label>'+
'<label><input type="checkbox" data-opt="recovery"> Notificar recuperação</label></div>';
el.querySelector('.pa-content').innerHTML='<header><span style="color:#e53943">⚠</span>'+title+'<button class="pa-close" type="button" aria-label="Fechar">×</button></header>'+
(config?settingHtml:'<div class="pa-body">'+mascotHtml+'<div class="pa-copy"><h2>'+(test?'Simulação visual e sonora (sem alterar municípios)':recovered?name+' está disponível novamente':name+' está indisponível há mais de '+opts.minutes+' minutos')+'</h2>'+
'<span class="pa-pill" style="'+(recovered?'background:#179d68':'')+'">'+(test?'MODO DE TESTE':recovered?'Recuperado':'Queda confirmada')+'</span>'+
'<p>Tempo de queda: <b>'+min+' min</b></p><p>Última verificação: '+new Date(row.ultima_verificacao||Date.now()).toLocaleTimeString('pt-BR')+'</p>'+
'<p>Áudio: '+(opts.sound?'habilitado (conforme permissão do navegador)':'desligado')+'</p></div></div>')+
'<footer><button class="pa-btn pa-main" data-action="primary">'+(config?'Salvar':test?'Repetir som':'Ver detalhes')+'</button>'+
'<button class="pa-btn" data-action="secondary">'+(config?'Testar alerta':test?'Fechar teste':'Silenciar / dispensar')+'</button></footer>';
el.classList.add('show');
el.querySelector('.pa-close').onclick=()=>{if(type==='offline')acknowledge(row);close();};
el.querySelector('[data-action="primary"]').onclick=()=>{if(config){save();close();}else if(test)sound();else{close();if(typeof portalChooseService==='function')portalChooseService('portais');}};
el.querySelector('[data-action="secondary"]').onclick=()=>{if(config)show({municipio:'Município de teste'},'test',mascot);else{if(type==='offline')acknowledge(row);close();}};
if(config){el.querySelectorAll('[data-opt]').forEach(node=>{const k=node.dataset.opt;node[node.type==='checkbox'?'checked':'value']=opts[k];node.oninput=()=>{opts[k]=node.type==='checkbox'?node.checked:Number(node.value);el.querySelector('[data-vol]').textContent=opts.volume+'%';save();};});el.querySelector('[data-vol]').textContent=opts.volume+'%';}
else if(!recovered)sound();
}
function check(rows,mascot){
if(!opts.enabled||active||!Array.isArray(rows))return;
for(const row of rows){if(typeof portalState==='function'?portalState(row)!=='offline':row.estado!=='offline')continue;
const start=Date.parse(row.mudou_em||row.inicio_falha||''),verified=Date.parse(row.ultima_verificacao||'');
if(!Number.isFinite(start)||!Number.isFinite(verified)||verified-start<opts.minutes*60000)continue;
const k=key(row);if(seen[k])continue;const recent=lastSound[k]||0;
if(recent&&(!opts.repeat||Date.now()-recent<opts.repeat*60000))continue;
lastSound[k]=Date.now();show(row,'offline',mascot);break;
}}
function mount(host,mascot){
const bar=host.querySelector('.portal-head-meta');if(!bar||bar.querySelector('[data-pa-test]'))return;
const container=document.createElement('span');container.style.cssText='display:inline-flex;gap:5px';
container.innerHTML='<button type="button" class="portal-report-trigger" data-pa-config>🔔 Alertas</button><button type="button" class="portal-report-trigger" data-pa-test>▶ Testar alerta</button>';
bar.appendChild(container);container.querySelector('[data-pa-config]').onclick=()=>show({},'config',mascot);
container.querySelector('[data-pa-test]').onclick=()=>show({municipio:'Município de teste'},'test',mascot);
}
window.ssPortalAlerts353={mount,check,show};
})();