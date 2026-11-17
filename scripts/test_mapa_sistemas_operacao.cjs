/* Testes de regressão do Mapa Gerencial: indicadores, fontes de eventos e proteção contra dados vencidos. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const src=fs.readFileSync("scripts/mapa_sistemas_operacao.js","utf8");
const marker="  window.ssMapOperationalState=liveState;";
assert.equal(src.split(marker).length,2,"Ponto de instrumentação não é único.");
const instrumented=src.replace(marker,"  window.__testOps={liveState,analyze,safeId,loadCityEvents,managerialMarkup};\n"+marker);
const requested=[];
const api=async(table,cols,query)=>{
 requested.push({table,cols,query});
 assert.match(query,/portal_id=in\.\(/,"Filtro do histórico deve utilizar ID do ambiente");
 assert.match(query,/ocorrido_em=gte\./,"Histórico deve limitar período");
 return [{portal_id:table.startsWith("veiculos")?"veiculos_caucaia":"portais_caucaia",
  ocorrido_em:new Date().toISOString(),estado_anterior:"suspeita_falha",estado_atual:"online",
  codigo_http:200,detalhe:"Recuperado"}];
};
const win={ssMapOpen(){}};
const context={window:win,portalFetchTable:api,Date,console};
vm.runInNewContext(instrumented,context,{filename:"mapa_sistemas_operacao.js"});
const t=win.__testOps;
assert(t,"Helpers não instrumentados");
const now=Date.now(),iso=delta=>new Date(now-delta).toISOString();
assert.equal(t.liveState({estado:"online",ultima_verificacao:iso(2*60000)},now),"online");
assert.equal(t.liveState({estado:"offline",ultima_verificacao:iso(2*60000)},now),"offline");
assert.equal(t.liveState({estado:"suspeita_falha",ultima_verificacao:iso(2*60000)},now),"observacao");
assert.equal(t.liveState({estado:"online",ultima_verificacao:iso(16*60000)},now),"desatualizado");
assert.equal(t.liveState({estado:"online",ultima_verificacao:""},now),"sem_leitura");
assert.equal(t.liveState({estado:"online",ultima_verificacao:iso(-30*60000)},now),"sem_leitura");
assert.equal(t.safeId("veiculos_caucaia"),"veiculos_caucaia");
assert.equal(t.safeId("a),estado=eq.online"),"");
const cities=[
 {key:"caucaia",name:"Caucaia",systems:{
  portais:[{id:"portais_caucaia",estado:"online",ultima_verificacao:iso(2*60000)}],
  fluxus:[],veiculos:[{id:"veiculos_caucaia",estado:"offline",ultima_verificacao:iso(2*60000)}]
 }},
 {key:"sobral",name:"Sobral",systems:{
  portais:[{id:"portais_sobral",estado:"online",ultima_verificacao:iso(18*60000)}],
  fluxus:[],veiculos:[]
 }},
 {key:"sem",name:"Sem sistema",systems:{portais:[],fluxus:[],veiculos:[]}}
];
const sum=t.analyze(cities,now);
assert.equal(sum.municipalities,3);
assert.equal(sum.covered,2);
assert.equal(sum.envs,3);
assert.equal(sum.online,1);
assert.equal(sum.offline,1);
assert.equal(sum.desatualizado,1);
assert.equal(sum.currentCities,1);
assert.deepEqual(Array.from(sum.distribution),[1,1,1,0]);
assert.equal(sum.systems.portais.onlineMunicipalities,1);
const html=t.managerialMarkup(cities,sum,[]);
assert.match(html,/Ceará|CEARÁ|Cobertura/);
assert.match(html,/Caucaia|2 sistemas/);
(async()=>{
 const events=await t.loadCityEvents(cities[0],7);
 assert.equal(events.length,3);
 assert.equal(events[0].rows.length,1);
 assert.equal(events[1].rows.length,0);
 assert.equal(events[2].rows.length,1);
 assert.equal(requested.length,2,"Histórico sem Fluxus não deve consultar uma tabela desnecessária");
 assert.equal(requested[0].table,"portais_monitor_eventos");
 assert.equal(requested[1].table,"veiculos_monitor_eventos");
 console.log("OK: indicadores com frescor 15min, distribuição, segurança do ID, histórico Supabase");
})().catch(e=>{console.error(e);process.exit(1)});
