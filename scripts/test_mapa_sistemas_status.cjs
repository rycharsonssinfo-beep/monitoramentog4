/* Testa que um chip conta ambientes, mas colore municípios únicos.
   Os filtros de status e sistema se cruzam e a verificação vencida NÃO vira offline. */
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const source=fs.readFileSync("scripts/mapa_sistemas_status.js","utf8");
const css=fs.readFileSync("scripts/mapa_sistemas_status.css","utf8");
const now=Date.now();
const ago=minutes=>new Date(now-minutes*60000).toISOString();
const operational=(row,t)=>{
 const at=Date.parse(row?.ultima_verificacao||"");
 if(!Number.isFinite(at)||at>t+300000)return "sem_leitura";
 if(t-at>900000)return "desatualizado";
 return row.estado==="online"?"online":row.estado==="offline"?"offline":"observacao";
};
const win={ssMapOpen(){},ssMapOperationalState:operational};
vm.runInNewContext(source,{window:win,Date,console},{filename:"mapa_sistemas_status.js"});
const matches=win.ssMapMatchedStatusCities;
assert.equal(typeof matches,"function");
const cities=[
 {key:"caucaia",name:"Caucaia",systems:{
  portais:[{estado:"online",ultima_verificacao:ago(2)}],
  fluxus:[],
  veiculos:[{estado:"offline",ultima_verificacao:ago(1)},{estado:"offline",ultima_verificacao:ago(3)}]
 }},
 {key:"sobral",name:"Sobral",systems:{
  portais:[{estado:"online",ultima_verificacao:ago(22)}],
  fluxus:[{estado:"offline",ultima_verificacao:ago(5)}],
  veiculos:[]
 }},
 {key:"crato",name:"Crato",systems:{
  portais:[],fluxus:[{estado:"online",ultima_verificacao:ago(5)}],
  veiculos:[{estado:"offline",ultima_verificacao:ago(29)}]
 }},
 {key:"maranguape",name:"Maranguape",systems:{portais:[],fluxus:[],veiculos:[]}}
];
function select(status,modes=[]){return Array.from(matches(cities,status,modes,now))}
const offline=select("offline");
assert.deepEqual(offline.map(x=>x.name),["Caucaia","Sobral"]);
assert.equal(offline.reduce((n,x)=>n+x.count,0),3);
assert.equal(select("offline",["veiculos"]).length,1);
assert.equal(select("offline",["veiculos"])[0].name,"Caucaia");
assert.equal(select("offline",["fluxus"])[0].name,"Sobral");
assert.equal(select("offline",["portais"]).length,0);
assert.equal(select("offline",["portais","veiculos"]).length,0,"Combinação requer os dois sistemas");
assert.deepEqual(select("desatualizado").map(x=>x.name),["Crato","Sobral"]);
assert.equal(select("online").length,2);
assert.deepEqual(select("sem_leitura"),[]);
assert.match(source,/data-map-status/);
assert.match(source,/aria-pressed/);
assert.match(source,/ss-map-filter-change/);
assert.match(source,/removeProperty\("fill"\)/);
assert.match(source,/data-map-city/);
assert.match(css,/ss-map-status-match/);
assert.match(css,/ss-map-ops-chip\.ss-map-status-button\.offline\.active/);
console.log("OK: 3 ambientes offline em 2 municípios; clique, cores, período de 15min e filtros combinados");
