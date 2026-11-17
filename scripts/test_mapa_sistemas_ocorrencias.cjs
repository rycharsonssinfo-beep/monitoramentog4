/* Regressão — diagnósticos municipais usam apenas eventos e datas gravadas. */
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const source=fs.readFileSync("scripts/mapa_sistemas_ocorrencias.js","utf8");
const win={ssMapOpen(){},ssMapOperationalState(row){
 const at=Date.parse(row.ultima_verificacao||"");
 if(!Number.isFinite(at))return"sem_leitura";
 if(Date.now()-at>900000)return"desatualizado";
 return row.estado==="offline"?"offline":row.estado==="online"?"online":"observacao";
}};
vm.runInNewContext(source,{window:win,Date,console},{filename:"mapa_sistemas_ocorrencias.js"});
const iso=n=>new Date(Date.now()-n*60000).toISOString();
const city={name:"Caucaia",systems:{
 portais:[{id:"portais_caucaia",name:"Portal",estado:"online",ultima_verificacao:iso(1)}],
 fluxus:[{id:"fluxus_caucaia",name:"Fluxus",estado:"suspeita_falha",ultima_verificacao:iso(4)}],
 veiculos:[
  {id:"veiculos_caucaia",name:"IPM <script>alert(1)</script>",estado:"offline",ultima_verificacao:iso(2),
   inicio_falha:iso(45),http_status:503,latencia_ms:1785,detalhe:"Tempo <b>esgotado</b>",
   url:"https://example.invalid/monitor"},
  {id:"veiculos_caucaia2",name:"Câmara",estado:"offline",ultima_verificacao:iso(22),
   inicio_falha:iso(40)}
 ]
}};
const obj=win.ssMapIncidentsCurrent(city);
assert.equal(obj.offline,1);
assert.equal(obj.attention,1);
assert.equal(obj.stale,1);
assert.equal(obj.active,2);
assert.match(obj.html,/HTTP 503/);
assert.match(obj.html,/1785 ms/);
assert.match(obj.html,/Desde a falha/);
assert.match(obj.html,/Tempo &lt;b&gt;esgotado&lt;\/b&gt;/);
assert.doesNotMatch(obj.html,/<script>/);
assert.match(obj.html,/IPM &lt;script&gt;/);
assert.match(obj.html,/Há 1 ambiente\(s\) sem verificação recente/);
const ev=win.ssMapIncidentsEvents([
 {mode:"veiculos",rows:[
  {portal_id:"veiculos_caucaia",municipio:"Caucaia",estado_anterior:"online",estado_atual:"offline",
   ocorrido_em:iso(45),codigo_http:503,detalhe:"Falha no serviço"},
  {portal_id:"veiculos_caucaia",municipio:"Caucaia",estado_anterior:"offline",estado_atual:"online",
   ocorrido_em:iso(3),codigo_http:200,detalhe:"Recuperado"}
 ]},
 {mode:"portais",rows:[],error:"Falha na consulta"}
],city);
assert.match(ev,/Indisponibilidade registrada/);
assert.match(ev,/Recuperado/);
assert.match(ev,/IPM &lt;script&gt;/);
assert.match(ev,/Histórico parcialmente indisponível/);
assert.match(source,/ssMapLoadCityEvents/);
assert.match(source,/ss-map-data-ready/);
assert.match(source,/ss-map-city-selected/);
assert.match(source,/ss-map-snapshot-updated/);
console.log("OK: diagnóstico, latência, HTTP, histórico real, leitura vencida e HTML seguro");
