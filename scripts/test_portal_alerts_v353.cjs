/* Testes determinísticos da regra de indisponibilidade, sem rede. */
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const source=fs.readFileSync("portal_alerts_v353.js","utf8");
const storage=new Map();
const context={
  window:{},
  localStorage:{
    getItem:(k)=>storage.get(k)||null,
    setItem:(k,v)=>storage.set(k,String(v)),
  },
  Date, Math, JSON, Object, Number, String, Array, Map,
  setTimeout:()=>1,setInterval:()=>1,
};
vm.runInNewContext(source,context,{filename:"portal_alerts_v353.js"});
const api=context.window.ssPortalAlerts353;
assert.ok(api&&api.eligible&&api.receive&&api.mount&&api.start);
const now=Date.now();
const minutes=n=>new Date(now-n*60000).toISOString();
const row=(duration,verified=0,estado="offline")=>({
  id:"municipio_teste",municipio:"Município de teste",estado,
  mudou_em:minutes(duration),ultima_verificacao:minutes(verified),
});
assert.equal(api.eligible(row(11)),true,"Queda confirmada há 11 min deve alertar");
assert.equal(api.eligible(row(10.2)),true,"Queda confirmada há mais de 10 min deve alertar");
assert.equal(api.eligible(row(4)),false,"Queda recente não deve alertar");
assert.equal(api.eligible(row(20,5)),false,"Coleta antiga não deve provocar falso positivo");
assert.equal(api.eligible(row(12,0,"online")),false,"Portal online não deve alertar");
assert.equal(api.eligible({...row(15),mudou_em:null}),false,"Sem início da queda não deve alertar");
console.log("OK: regras de 10 min, atualização recente, recuperação e ausência de horário.");
