/* Homologação lógica dos alertas v3.53: DOM e áudio simulados, sem rede. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync("portal_alerts_v353.js","utf8");

function app(dateOverride=Date){
  const storage=new Map(),timeouts=[],intervals=[];
  let audioStarts=0,nextTimerId=0;
  const slot={
    html:"",buttons:{},
    get innerHTML(){return this.html;},
    set innerHTML(value){this.html=String(value);this.buttons={};},
    querySelector(selector){
      if(!this.buttons[selector])this.buttons[selector]={onclick:null};
      return this.buttons[selector];
    },
    querySelectorAll(){return []}
  };
  const visible=new Set();
  const modal={
    id:"",innerHTML:"",
    classList:{
      add:k=>visible.add(k),remove:k=>visible.delete(k),
      contains:k=>visible.has(k)
    },
    querySelector:selector=>selector===".sspa-slot"?slot:null
  };
  const nodes=[];
  const document={
    getElementById:id=>nodes.find(n=>n.id===id)||null,
    createElement:tag=>tag==="div"?modal:{innerHTML:"",style:{},querySelector(){return null}},
    body:{appendChild:node=>nodes.push(node)}
  };
  class AudioContext{
    constructor(){this.state="running";this.currentTime=0;this.destination={};}
    createOscillator(){return {
      frequency:{value:0},connect(){},start(){audioStarts++;},stop(){}
    };}
    createGain(){return {gain:{
      setValueAtTime(){},exponentialRampToValueAtTime(){}
    },connect(){}};}
  }
  const window={AudioContext};
  const localStorage={
    getItem:key=>storage.get(key)||null,
    setItem:(key,value)=>storage.set(key,String(value))
  };
  const context={window,document,localStorage,Date:dateOverride,console,
    setTimeout:(fn,ms)=>{fn.__timerId=++nextTimerId;fn.delay=ms;timeouts.push(fn);return fn.__timerId;},
    clearTimeout:id=>{const fn=timeouts.find(t=>t.__timerId===id);if(fn)fn.__cancelled=true;},
    setInterval:fn=>{intervals.push(fn);return intervals.length;}
  };
  vm.runInNewContext(source,context,{filename:"portal_alerts_v353.js"});
  return {api:window.ssPortalAlerts353,slot,visible,timeouts,intervals,storage,
    audioStarts:()=>audioStarts,
    close(){const btn=slot.querySelector("[data-action='secondary']");
      assert.equal(typeof btn.onclick,"function");
      btn.onclick();},
    flush(){let fn;while((fn=timeouts.shift())){if(!fn.__cancelled){fn();return true;}}return false;}
  };
}
const now=Date.now();
const timestamp=minutes=>new Date(now-minutes*60000).toISOString();
const offline=(id,minutes=13,verified=0)=>({
  id,municipio:"Município "+id,estado:"offline",
  mudou_em:timestamp(minutes),ultima_verificacao:timestamp(verified)
});
const online=id=>({
  id,municipio:"Município "+id,estado:"online",
  mudou_em:timestamp(0),ultima_verificacao:timestamp(0)
});

(async()=>{
  // São necessários tempo confirmado e coleta atual; dados antigos nunca alertam.
  {
    const a=app();
    a.api.receive([offline("Recente",5),offline("Desatualizado",15,5)]);
    assert.equal(a.visible.has("visible"),false,"Leitura insuficiente não abre alerta");
    a.api.receive([online("Recente"),online("Desatualizado")]);
    assert.equal(a.visible.has("visible"),false,"Quedas não notificadas não geram recuperação");
  }
  // Alerta visual, áudio, persistência e fila de municípios offline.
  {
    const a=app();
    a.api.receive([offline("Alfa"),offline("Beta")]);
    assert.match(a.slot.innerHTML,/Município Alfa/);
    assert.match(a.slot.innerHTML,/Queda confirmada/);
    assert.equal(a.audioStarts(),3,"O alerta dispara três tons");
    assert.equal(a.visible.has("visible"),true);
    assert.ok(a.storage.get("ss_portais_alertas_emitidos_v353"),"Ocorrência é persistida");
    a.close();
    a.flush();
    assert.match(a.slot.innerHTML,/Município Beta/,"A segunda queda deve aparecer");
    a.close();
    a.flush();
    assert.equal(a.visible.has("visible"),false);
    a.api.receive([offline("Alfa"),offline("Beta")]);
    assert.equal(a.visible.has("visible"),false,"Não repetir as mesmas quedas");
    a.api.receive([online("Alfa"),online("Beta")]);
    assert.match(a.slot.innerHTML,/Município Alfa/);
    assert.match(a.slot.innerHTML,/Recuperado/);
    a.close();
    a.flush();
    assert.match(a.slot.innerHTML,/Município Beta/,"Segunda recuperação não pode ser perdida");
    assert.match(a.slot.innerHTML,/Recuperado/);
    a.close();
    a.flush();
    assert.equal(a.visible.has("visible"),false);
  }
  // Recuperação substitui imediatamente a notificação de queda ainda aberta.
  {
    const a=app();
    a.api.receive([offline("Gama")]);
    a.api.receive([online("Gama")]);
    assert.match(a.slot.innerHTML,/Recuperado/);
    assert.match(a.slot.innerHTML,/Município Gama/);
  }
  // O teste manual sempre abre a simulação e permite acionar o som.
  {
    const a=app();
    a.api.showTest();
    assert.match(a.slot.innerHTML,/MODO DE TESTE/);
    assert.match(a.slot.innerHTML,/TEMPO SIMULADO DE QUEDA/);
    assert.match(a.slot.innerHTML,/data-sspa-duration-value>11<\/strong>/);
    assert.match(source,/\.sspa-kpi-value\{font-size:clamp\(34px,4\.5vw,46px\)/);
    assert.equal(a.audioStarts(),3);
    a.slot.querySelector("[data-action='primary']").onclick();
    assert.equal(a.audioStarts(),6,"Botão de som deve reproduzir os tons");
    assert.equal(a.slot.querySelector("[data-sspa-audio]").textContent,
      "Áudio autorizado neste navegador","Estado do som atualiza sem reabrir a janela");
  }
  // O controlador consulta o monitor em segundo plano independentemente da aba.
  {
    const a=app();
    let fetches=0;
    a.api.start({state:row=>row.estado,fetch:async()=>{fetches++;return [offline("Delta")];}});
    assert.equal(a.timeouts.length,1);
    assert.equal(a.intervals.length,2,"Intervalos para monitoramento e repetição");
    await a.timeouts.shift()();
    assert.equal(fetches,1);
    assert.match(a.slot.innerHTML,/Município Delta/);
  }
  // Contador avança sem reconstruir o modal nem interromper áudio ou ações.
  {
    let fakeNow=Date.now();
    class Clock extends Date{static now(){return fakeNow;}}
    const a=app(Clock);
    a.api.start({state:row=>row.estado,fetch:async()=>[]});
    a.api.receive([offline("Cronometro",64)]);
    assert.match(a.slot.innerHTML,/INDISPONÍVEL HÁ/);
    assert.match(a.slot.innerHTML,/data-sspa-duration-value>1h<\/strong>/);
    assert.match(a.slot.innerHTML,/data-sspa-duration-unit>04min<\/span>/);
    fakeNow+=60000;
    a.intervals[1]();
    assert.equal(a.slot.querySelector("[data-sspa-duration-value]").textContent,"1h");
    assert.equal(a.slot.querySelector("[data-sspa-duration-unit]").textContent,"05min");
    assert.equal(a.visible.has("visible"),true,"A notificação segue aberta");
  }
  // Todas as telas abertas usam o polling global, mesmo sem montar a aba Portais.
  {
    const a=app(),b=app();
    const fetch=async()=>[offline("Compartilhado",13)];
    a.api.start({state:r=>r.estado,fetch});
    b.api.start({state:r=>r.estado,fetch});
    assert.equal(a.intervals.length,2);
    assert.equal(b.intervals.length,2);
    await a.timeouts.shift()();
    await b.timeouts.shift()();
    assert.match(a.slot.innerHTML,/Município Compartilhado/);
    assert.match(b.slot.innerHTML,/Município Compartilhado/);
    assert.equal(a.visible.has("visible"),true);
    assert.equal(b.visible.has("visible"),true);
    assert.match(source,/setInterval\(refresh,15000\)/);
  }
  // A notificação não fica permanente na tela: encerra em 20s.
  {
    const a=app();
    a.api.receive([offline("Expirar")]);
    assert.equal(a.timeouts.find(fn=>fn.delay===20000)!=null,true);
    a.flush();
    assert.equal(a.visible.has("visible"),false,"Alerta deve desaparecer automaticamente");
    a.flush();
    assert.equal(a.visible.has("visible"),false,"Não repetir ocorrência expirada");
  }
  // Recuperações e testes também têm fechamento automático.
  {
    const a=app();
    a.api.receive([offline("Recuperar")]);
    a.api.receive([online("Recuperar")]);
    assert.match(a.slot.innerHTML,/Recuperado/);
    a.flush();
    assert.equal(a.visible.has("visible"),false,"Recuperação desaparece após o período definido");
    const b=app();
    b.api.showTest();
    b.flush();
    assert.equal(b.visible.has("visible"),false,"Simulação não fica fixa");
  }
  assert.match(source,/data-opt='autoDismissSeconds'/);
  console.log("OK: alertas globais em diferentes telas, áudio, encerramento automático, cronômetro e recuperação.");
})().catch(err=>{console.error(err);process.exitCode=1;});
