const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict');
const here=__dirname;
const ctx=vm.createContext({
 console,
 g4fText:x=>String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
 g4fVisibleAgent:a=>!['Cislena Cisne','Marla Lima','Emanuela Costa'].includes(a.nome),
 g4fTime:()=> '13:30'
});
vm.runInContext(fs.readFileSync(path.join(here,'g4flex_indicadores.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(path.join(here,'g4flex_relatorio_dia.js'),'utf8'),ctx);
const fixture={
 capturado_em:'2026-11-19T16:30:00+00:00',
 resumo:{
  indicadores_historicos_coletados_em:'2026-11-19T16:29:00+00:00',
  matriz_horaria:[
   {horario:'08:00 - 09:00',abertas:19,atendidas:17,nao_atendidas:2,abandonadas:0,tme:'00:01:45'},
   {horario:'09:00 - 10:00',abertas:18,atendidas:18,nao_atendidas:0,abandonadas:1,tme:'00:01:14'}
  ],
  ranking_motivos:[{motivo:'Folha de Pagamento',quantidade:19},{motivo:'SATWeb',quantidade:17}]
 }
};
ctx.fixture=fixture;
let html=vm.runInContext('g4fDailyReportHTML(fixture)',ctx);
assert.match(html,/Relat.rio do dia/);
assert.match(html,/Ranking de filas/);
assert.match(html,/Matriz horária de indicadores/);
assert.match(html,/Folha de Pagamento/);
assert.match(html,/SATWeb/);
assert.match(html,/19\/11\/2026/);
assert.match(html,/13:29:00/);
assert.match(html,/class="matrix"/);
assert.match(html,/>37<\/strong>/); // abertas: 19 + 18
assert.match(html,/ranking_motivos/);
assert.match(html,/Imprimir \/ Salvar como PDF/);
assert.ok(html.includes('size:A4 landscape'));
assert.match(html,/Dados parciais até a última coleta/);
assert.match(html,/Resumo dos atendimentos/);
assert.match(html,/Soma dos atendimentos/);
assert.doesNotMatch(html,/Soma das faixas horárias/);
assert.match(html,/class="brand-fallback"/); // fallback seguro se a logo não carregar
assert.doesNotMatch(html,/class="brandmark"/);
ctx.window={};
vm.runInContext(fs.readFileSync(path.join(here,'logo_grupo_ss_oficial.js'),'utf8'),ctx);
assert.match(ctx.window.__SS_OFICIAL_LOGO__,/^data:image\/png;base64,/);
const withLogo=vm.runInContext('g4fDailyReportHTML(fixture)',ctx);
assert.match(withLogo,/class="brand-logo"/);
assert.match(withLogo,/alt="Grupo S&amp;S — logomarca oficial"/);
assert.match(withLogo,/src="data:image\/png;base64,/);
assert.doesNotMatch(withLogo,/class="brand-fallback"/);
assert.match(withLogo,/border-top:3px solid/);
assert.match(withLogo,/Resumo dos atendimentos/);
ctx.empty={resumo:{}};
assert.equal(vm.runInContext('g4fDailyReportHTML(empty)',ctx),null);
assert.equal(vm.runInContext('g4fReportQueues(empty).length',ctx),0);
let count=vm.runInContext('g4fReportQueues(fixture).length',ctx);
assert.equal(count,2);
ctx.direct={resumo:{ranking_filas:[{fila:'Fila Técnica',quantidade:7}],ranking_motivos:[{motivo:'Nao deve aparecer',quantidade:100}]}};
assert.match(vm.runInContext('g4fReportRanking(g4fReportQueues(direct))',ctx),/Fila Técnica/);
assert.doesNotMatch(vm.runInContext('g4fReportRanking(g4fReportQueues(direct))',ctx),/Nao deve aparecer/);
ctx.evil={resumo:{ranking_filas:[{fila:'<script>alert(1)</script>',quantidade:2}]}};
assert.doesNotMatch(vm.runInContext('g4fDailyReportHTML(evil)',ctx),/<script>alert\(1\)<\/script>/);
assert.match(vm.runInContext('g4fDailyReportHTML(evil)',ctx),/&lt;script&gt;/);
let popped=null;
ctx.window={
 __SS_OFICIAL_LOGO__:ctx.window.__SS_OFICIAL_LOGO__,
 open(){const win={document:{open(){},write(v){popped=v;},close(){}},focus(){}};return win;},
 alert(){throw Error('Não deveria mostrar alerta ao abrir relatório')}
};
assert.equal(vm.runInContext('g4fExportDailyReport(fixture)',ctx),true);
assert.match(popped,/Relatório do dia/);
console.log('PASS: logo oficial PNG no PDF, resumo dos atendimentos, ranking de filas, datas, somas, segurança e impressão.');
