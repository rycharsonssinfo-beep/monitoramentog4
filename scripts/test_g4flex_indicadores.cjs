const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const code=fs.readFileSync(path.join(__dirname,'g4flex_indicadores.js'),'utf8');
const context=vm.createContext({
 console,
 g4fText:x=>String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
 g4fVisibleAgent:x=>!['Cislena Cisne','Marla Lima','Emanuela Costa'].includes(x.nome),
 g4fTime:()=> '17:31'
});
vm.runInContext(code,context,{filename:'g4flex_indicadores.js'});
const noHist={resumo:{},atendentes:[{nome:'Aline Carioca',status:'ativo',em_atendimento:2},{nome:'Marla Lima',status:'ativo',em_atendimento:4}]};
assert.equal(vm.runInContext('g4fReportHours({resumo:{}}).length',context),0);
assert.equal(vm.runInContext('g4fReportReasons({resumo:{}}).length',context),0);
assert.match(vm.runInContext('g4fReportPlot([])',context),/ainda não foi enviada/);
const data={
 resumo:{
  matriz_horaria:[
   {horario:'08:00 - 09:00',abertas:19,atendidas:17,nao_atendidas:2,abandonadas:0,tme:'00:01:45'},
   {horario:'09:00 - 10:00',abertas:18,atendidas:18,nao_atendidas:0,abandonadas:0,tme:'00:01:14'}
  ],
  ranking_motivos:[{motivo:'Folha de Pagamento',quantidade:19},{motivo:'Contabilidade',quantidade:17}]
 }
};
context.__fixture=data;
const tbl=vm.runInContext('g4fReportTable(g4fReportHours(__fixture))',context);
assert.match(tbl,/08:00 - 09:00/);
assert.match(tbl,/Abertas/);
assert.match(tbl,/00:01:45/);
const plot=vm.runInContext('g4fReportPlot(g4fReportHours(__fixture))',context);
assert.match(plot,/g4f-report-plot/);
const ranking=vm.runInContext('g4fReportRanking(g4fReportReasons(__fixture))',context);
assert.match(ranking,/Folha de Pagamento/);
assert.match(ranking,/Contabilidade/);
const nodes={};
for(const key of ['current','historical','plot','table','ranking','stamp','availability']){
 nodes['[data-g4f-report-'+key+']']={innerHTML:'',textContent:'',classList:{toggle(){}}};
}
const screen={hidden:false,querySelector:key=>nodes[key]};
const host={querySelector:key=>key==='.g4f-insights'?screen:null};
context.__host=host;context.__current=noHist;
vm.runInContext('g4fInsightsRender(__host,__current)',context);
assert.match(nodes['[data-g4f-report-current]'].innerHTML,/Atendentes monitorados/);
assert.match(nodes['[data-g4f-report-current]'].innerHTML,/>1</);
assert.match(nodes['[data-g4f-report-historical]'].innerHTML,/pendente/);
const prior=nodes['[data-g4f-report-plot]'].innerHTML;
context.__current=data;
vm.runInContext('g4fInsightsRender(__host,__current)',context);
assert.notEqual(nodes['[data-g4f-report-plot]'].innerHTML,prior);
const before=nodes['[data-g4f-report-table]'].innerHTML;
vm.runInContext('g4fInsightsRender(__host,__current)',context);
assert.equal(nodes['[data-g4f-report-table]'].innerHTML,before);
console.log('OK: leitura do snapshot, indicadores históricos, ranking, equipe filtrada e renderização estável.');
