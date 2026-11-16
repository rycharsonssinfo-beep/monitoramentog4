/* Testes isolados do relatório: filtros, XLSX e impressão PDF. */
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const {execFileSync}=require("node:child_process");
const src=fs.readFileSync("scripts/mapa_sistemas_report.js","utf8");
const instrumented=src.replace(/\}\)\(\);\s*$/, "window.__reportTest={makeXlsx,rowsFor,summary,records,printPdf};})();");
assert.notEqual(instrumented,src,"Ponto de instrumentação não encontrado");
let printed="";
const win={ssMapOpen(){},open(){
  return {document:{readyState:"loading",open(){},write(s){printed=s},close(){}},
    addEventListener(){},focus(){},print(){}};
}};
const ctx={window:win,Blob,TextEncoder,URL,Date,setTimeout,console};
vm.runInNewContext(instrumented,ctx,{filename:"mapa_sistemas_report.js"});
const t=win.__reportTest;
assert(t,"Funções de relatório não disponíveis");
const cities=[
 {name:"Caucaia",key:"caucaia",code:"2303709",systems:{
  portais:[],
  fluxus:[{name:"Prefeitura de Caucaia",url:"https://caucaia.ssinformatica.net/",estado:"online",ultima_verificacao:"2026-11-16T16:00:00-03:00"}],
  veiculos:[{name:"IPM Caucaia",url:"https://ssveiculos.ssinformatica.net/IPMCaucaia",estado:"offline",ultima_verificacao:"2026-11-16T16:05:00-03:00"}]
 }},
 {name:"Sobral",key:"sobral",code:"2312908",systems:{
   portais:[{name:"Sobral",url:"https://exemplo.com/portal",estado:"online",ultima_verificacao:"2026-11-16"}],fluxus:[],veiculos:[]
 }},
 {name:"Município sem cadastro",key:"semcadastro",code:"0000000",systems:{portais:[],fluxus:[],veiculos:[]}}
];
const sum=t.summary(cities);
assert.equal(sum.municipios,3);assert.equal(sum.covered,2);
assert.equal(sum.missing,1);assert.equal(sum.environments,3);
assert.equal(sum.online,2);
const filtered=t.rowsFor({cities,modes:["fluxus","veiculos"],selected:"caucaia"},"filtered");
assert.equal(filtered.length,1);assert.equal(filtered[0].name,"Caucaia");
assert.equal(t.rowsFor({cities,modes:[],selected:"sobral"},"selected")[0].name,"Sobral");
assert.equal(t.records(cities).length,3);
(async()=>{
 const xlsx=t.makeXlsx(cities,"all");
 assert.equal(xlsx.type,"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
 const out="/tmp/monitor_sistemas_report_test.xlsx";
 fs.writeFileSync(out,Buffer.from(await xlsx.arrayBuffer()));
 const py=[
  "import sys,zipfile,xml.etree.ElementTree as ET",
  "with zipfile.ZipFile(sys.argv[1]) as z:",
  " assert z.testzip() is None, 'ZIP invalido'",
  " names=set(z.namelist())",
  " exp={'[Content_Types].xml','xl/workbook.xml','xl/styles.xml','xl/worksheets/sheet1.xml','xl/worksheets/sheet2.xml','xl/worksheets/sheet3.xml'}",
  " assert exp.issubset(names), names",
  " w=z.read('xl/workbook.xml').decode()",
  " assert all(x in w for x in ['Resumo','Cobertura Municipal','Ambientes'])",
  " for n in (1,2,3): ET.fromstring(z.read('xl/worksheets/sheet%d.xml'%n))",
  " assert 'Caucaia' in z.read('xl/worksheets/sheet2.xml').decode()",
  " assert 'IPM Caucaia' in z.read('xl/worksheets/sheet3.xml').decode()",
  " print('XLSX valido: ZIP, tres abas e dados de teste')"
 ].join("\n");
 execFileSync("python",["-c",py,out],{stdio:"inherit"});
 t.printPdf(cities,"all");
 assert.match(printed,/Caucaia/);
 assert.match(printed,/Sobral/);
 assert.match(printed,/RELATÓRIO DE COBERTURA DOS SISTEMAS/);
 console.log("OK: resumo, filtros, XLSX e conteudo PDF validados");
})().catch(e=>{console.error(e);process.exit(1)});
