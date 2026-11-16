/* Relatório de Cobertura dos Sistemas — Monitor S&S
   Exportação integralmente no navegador, sem envio dos cadastros a terceiros.
   XLSX nativo (OOXML/ZIP sem bibliotecas externas); PDF via impressão do navegador. */
(function installSsCoverageReport(){
  if(window.__ssCoverageReportInstalled)return;
  window.__ssCoverageReportInstalled=true;
  const previous=window.ssMapOpen;
  if(typeof previous!=="function")return;
  const SYS=[["portais","Portal do Contribuinte"],["fluxus","Fluxus"],["veiculos","Veículos"]];
  const esc=s=>String(s??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const xml=s=>String(s??"").replace(/[<>&"']/g,ch=>({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;","'":"&apos;"}[ch]));
  const now=()=>new Date().toLocaleString("pt-BR");
  const dateKey=()=>new Date().toISOString().slice(0,10);
  const sort=(a,b)=>String(a.name).localeCompare(String(b.name),"pt-BR");
  const stateName=s=>({
    online:"Online na última consulta",offline:"Indisponível na última consulta",
    stale:"Leitura desatualizada",nao_verificado:"Sem leitura",
    suspeita_falha:"Falha em verificação",recuperando:"Recuperação em verificação",
    verificacao_bloqueada:"Verificação bloqueada"
  }[s]||"Situação não confirmada");
  function dateDisplay(input){
    if(!input)return"Não informado";
    const d=new Date(input);
    return isNaN(d.getTime())?String(input):d.toLocaleString("pt-BR");
  }
  function nSystems(city){return SYS.filter(([key])=>(city.systems[key]||[]).length).length}
  function nEnvs(city){return SYS.reduce((n,[key])=>n+(city.systems[key]||[]).length,0)}
  function nOnline(city){return SYS.reduce((n,[key])=>n+(city.systems[key]||[]).filter(r=>r.estado==="online").length,0)}
  function rowsFor(data,scope){
    const arr=[...data.cities].sort(sort);
    switch(scope){
      case "covered":return arr.filter(c=>nSystems(c)>0);
      case "filtered":return arr.filter(c=>nSystems(c)>0 && (!data.modes.length||data.modes.every(m=>(c.systems[m]||[]).length)));
      case "selected":return arr.filter(c=>c.key===data.selected);
      default:return arr;
    }
  }
  function records(cities){
    const out=[];
    for(const c of cities)for(const [mode,label] of SYS)for(const r of (c.systems[mode]||[])){
      out.push({
        municipio:c.name,uf:"CE",ibge:c.code||"",sistema:label,
        entidade:r.name||c.name,url:r.url||"",
        cadastro:"Cadastrado",situacao:stateName(r.estado),
        ultima:dateDisplay(r.ultima_verificacao),online:r.estado==="online"
      });
    }
    return out;
  }
  function summary(cities){
    const covered=cities.filter(c=>nSystems(c)>0).length;
    const environments=cities.reduce((n,c)=>n+nEnvs(c),0);
    const online=cities.reduce((n,c)=>n+nOnline(c),0);
    return {municipios:cities.length,covered,missing:cities.length-covered,
      environments,online,
      portals:cities.filter(c=>c.systems.portais?.length).length,
      fluxus:cities.filter(c=>c.systems.fluxus?.length).length,
      vehicles:cities.filter(c=>c.systems.veiculos?.length).length};
  }
  const scopes={
    all:"Todos os municípios do Ceará",
    covered:"Somente municípios com sistemas",
    filtered:"Municípios dos filtros selecionados",
    selected:"Somente o município selecionado"
  };
  // OOXML gerado localmente; strings são sempre células textuais, inclusive URLs e prefixos =,+,-,@.
  function excelSheet(rows,widths){
    const col=x=>{
      let o="";for(let n=x;n;n=Math.floor((n-1)/26))o=String.fromCharCode(65+(n-1)%26)+o;
      return o;
    };
    let body="";
    rows.forEach((row,i)=>{
      body+='<row r="'+(i+1)+'">';
      row.forEach((val,j)=>{
        if(val===null||val===undefined)return;
        const ref=col(j+1)+(i+1);
        if(typeof val==="number"&&Number.isFinite(val)){
          body+='<c r="'+ref+'" s="'+(i===0?1:0)+'"><v>'+val+'</v></c>';
        }else{
          body+='<c r="'+ref+'" s="'+(i===0?1:0)+'" t="inlineStr"><is><t xml:space="preserve">'+xml(val)+'</t></is></c>';
        }
      });
      body+='</row>';
    });
    const cols=widths.map((w,i)=>'<col min="'+(i+1)+'" max="'+(i+1)+'" width="'+w+'" customWidth="1"/>').join("");
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+
      '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'+
      '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'+
      '<cols>'+cols+'</cols><sheetData>'+body+'</sheetData></worksheet>';
  }
  function zip(files){
    const encoder=new TextEncoder(),parts=[],central=[];
    let offset=0;
    const crc32=bytes=>{
      let crc=0xffffffff;
      for(const byte of bytes){
        crc^=byte;
        for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);
      }
      return (crc^0xffffffff)>>>0;
    };
    function header(len){return new DataView(new ArrayBuffer(len))}
    const fileList=Object.entries(files);
    for(const [name,data] of fileList){
      const file=encoder.encode(data),fileName=encoder.encode(name),crc=crc32(file);
      const h=header(30+fileName.length),d=h;
      d.setUint32(0,0x04034b50,true);d.setUint16(4,20,true);
      d.setUint16(6,0x0800,true);d.setUint16(8,0,true);
      d.setUint32(14,crc,true);d.setUint32(18,file.length,true);d.setUint32(22,file.length,true);
      d.setUint16(26,fileName.length,true);
      new Uint8Array(d.buffer,30).set(fileName);
      parts.push(d.buffer,file);
      central.push({name:fileName,crc,size:file.length,offset});
      offset+=d.byteLength+file.length;
    }
    const centralStart=offset;
    for(const f of central){
      const h=header(46+f.name.length);
      h.setUint32(0,0x02014b50,true);h.setUint16(4,20,true);h.setUint16(6,20,true);
      h.setUint16(8,0x0800,true);h.setUint16(10,0,true);
      h.setUint32(16,f.crc,true);h.setUint32(20,f.size,true);h.setUint32(24,f.size,true);
      h.setUint16(28,f.name.length,true);h.setUint32(42,f.offset,true);
      new Uint8Array(h.buffer,46).set(f.name);
      parts.push(h.buffer);offset+=h.byteLength;
    }
    const end=header(22);end.setUint32(0,0x06054b50,true);
    end.setUint16(8,central.length,true);end.setUint16(10,central.length,true);
    end.setUint32(12,offset-centralStart,true);end.setUint32(16,centralStart,true);
    parts.push(end.buffer);
    return new Blob(parts,{type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
  }
  function makeXlsx(cities,sc){
    const totals=summary(cities),details=records(cities);
    const resumo=[
      ["RELATÓRIO DE COBERTURA DOS SISTEMAS — GRUPO S&S","Valor"],
      ["Data de emissão",now()],["Abrangência",scopes[sc]],
      ["Municípios incluídos",totals.municipios],
      ["Municípios com ao menos um sistema",totals.covered],
      ["Municípios sem cadastro identificado",totals.missing],
      ["Municípios com Portal do Contribuinte",totals.portals],
      ["Municípios com Fluxus",totals.fluxus],
      ["Municípios com Veículos",totals.vehicles],
      ["Total de ambientes cadastrados",totals.environments],
      ["Ambientes online na última consulta",totals.online],
      ["Critério","Sistema cadastrado não significa sistema online."],
      ["Fonte","Cadastros e última leitura disponíveis no Monitor de Portais S&S"]
    ];
    const coverage=[
      ["Município","UF","Código IBGE","Sistemas cadastrados","Portal do Contribuinte","Fluxus","Veículos","Ambientes","Ambientes online (última consulta)"],
      ...cities.map(c=>[c.name,"CE",c.code||"",nSystems(c),
        c.systems.portais?.length?"Sim":"Não",
        c.systems.fluxus?.length?"Sim":"Não",
        c.systems.veiculos?.length?"Sim":"Não",
        nEnvs(c),nOnline(c)])
    ];
    const ambientes=[
      ["Município","UF","Código IBGE","Sistema","Entidade","URL","Cadastro","Situação na última consulta","Data da última verificação"],
      ...details.map(r=>[r.municipio,r.uf,r.ibge,r.sistema,r.entidade,r.url,r.cadastro,r.situacao,r.ultima])
    ];
    const names=["Resumo","Cobertura Municipal","Ambientes"];
    const workbook='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'+
      '<sheets>'+names.map((n,i)=>'<sheet name="'+xml(n)+'" sheetId="'+(i+1)+'" r:id="rId'+(i+1)+'"/>').join("")+'</sheets></workbook>';
    const rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+
      names.map((_,i)=>'<Relationship Id="rId'+(i+1)+'" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet'+(i+1)+'.xml"/>').join("")+
      '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>';
    const styles='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+
      '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'+
      '<fonts count="2"><font><sz val="11"/><name val="Aptos"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Aptos"/></font></fonts>'+
      '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'+
      '<fill><patternFill patternType="solid"><fgColor rgb="FF124570"/><bgColor indexed="64"/></patternFill></fill></fills>'+
      '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'+
      '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'+
      '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'+
      '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs></styleSheet>';
    const ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'+
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'+
      '<Default Extension="xml" ContentType="application/xml"/>'+
      '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'+
      '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'+
      names.map((_,i)=>'<Override PartName="/xl/worksheets/sheet'+(i+1)+'.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>').join("")+
      '</Types>';
    const files={
      "[Content_Types].xml":ct,
      "_rels/.rels":'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
      "xl/workbook.xml":workbook,"xl/_rels/workbook.xml.rels":rels,
      "xl/styles.xml":styles,
      "xl/worksheets/sheet1.xml":excelSheet(resumo,[60,62]),
      "xl/worksheets/sheet2.xml":excelSheet(coverage,[30,7,15,23,28,14,14,15,31]),
      "xl/worksheets/sheet3.xml":excelSheet(ambientes,[30,7,15,25,52,68,18,33,28])
    };
    return zip(files);
  }
  function download(blob,name){
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download=name;a.style.display="none";
    document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),12000);
  }
  function printPdf(cities,sc,format="gerencial",statewideTotal=184){
    if(format!=="gerencial"&&format!=="tecnico")throw Error("Formato de PDF inválido.");
    const win=window.open("","_blank");
    if(!win)throw Error("Janela bloqueada. Autorize pop-ups para salvar o PDF.");
    const stats=summary(cities),details=format==="tecnico"?records(cities):[];
    const fraction=statewideTotal?100*stats.covered/statewideTotal:0;
    const percent=v=>v.toLocaleString("pt-BR",{maximumFractionDigits:1})+"%";
    const kpis=[
      ["Municípios",stats.municipios],["Atendidos",stats.covered],
      ["Sem cadastro",stats.missing],["Ambientes",stats.environments],
      ["Online na última leitura",stats.online],["Cobertura do Ceará",percent(fraction)]
    ];
    const kpiHTML=kpis.map(([label,value])=>'<div class="kpi"><b>'+esc(value)+'</b><span>'+esc(label)+'</span></div>').join("");
    const coverage=cities.map(c=>'<tr><td class="name">'+esc(c.name)+'</td><td>'+esc(c.code||"")+'</td>'+
      SYS.map(([m])=>'<td class="center">'+(c.systems[m]?.length?"✓":"—")+'</td>').join("")+
      '<td class="num">'+nEnvs(c)+'</td><td class="num">'+nOnline(c)+'</td></tr>').join("");
    const detailsRows=details.map(r=>'<tr><td>'+esc(r.municipio)+'</td><td>'+esc(r.sistema)+'</td>'+
      '<td>'+esc(r.entidade)+'</td><td class="url">'+
      (r.url?'<a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer">'+esc(r.url)+'</a>':"—")+
      '</td><td>'+esc(r.situacao)+'</td><td>'+esc(r.ultima)+'</td></tr>').join("");
    const isTech=format==="tecnico";
    const caption=isTech?"RELATÓRIO TÉCNICO COMPLETO":"RELATÓRIO GERENCIAL";
    const style=[
      '@page{size:A4 landscape;margin:10mm 11mm}',
      '*{box-sizing:border-box}',
      'html,body{margin:0;background:#fff;color:#163047;font-family:Arial,"Segoe UI",sans-serif;font-size:9px}',
      '.brand{display:flex;align-items:center;justify-content:space-between;border-top:4px solid #1c71af;border-bottom:1px solid #c3dbea;padding:8px 0 9px;gap:15px}',
      '.brand-name{font-weight:900;font-size:17px;color:#0e4c7c;letter-spacing:-.4px}',
      '.brand-name .icon{display:inline-block;background:linear-gradient(135deg,#12649e,#56bbeb);color:#fff;border-radius:6px;padding:5px 7px;margin-right:8px}',
      '.stamp{color:#4f6a80;font-size:9px;text-align:right;line-height:1.6}',
      'h1{font-size:18px;color:#103f6d;margin:13px 0 4px;letter-spacing:-.4px}',
      '.subtitle{font-size:9px;color:#587187;margin:0 0 12px}',
      '.stats{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:7px;margin:11px 0 12px}',
      '.kpi{border:1px solid #c4d5e5;border-radius:6px;padding:8px 7px;min-width:0;break-inside:avoid;background:#f9fcff}',
      '.kpi b{display:block;font-size:16px;color:#124a77;margin-bottom:4px}',
      '.kpi span{display:block;font-size:8px;color:#4c657a;line-height:1.25}',
      '.note{background:#f0f6fb;padding:7px 9px;border-left:3px solid #2b7eb6;color:#48667d;font-size:8px;margin:10px 0 12px;line-height:1.4}',
      'h2{color:#124e7b;font-size:12px;margin:10px 0 7px;break-after:avoid}',
      'table{width:100%;border-collapse:collapse;table-layout:fixed}',
      'thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}',
      'th{background:#165682;color:#fff;text-align:left;padding:6px 6px;font-size:8.2px}',
      'td{padding:4px 6px;border-bottom:1px solid #dde8ef;line-height:1.22;font-size:8.4px;overflow-wrap:anywhere}',
      'tbody tr:nth-child(even){background:#f1f6fa}',
      'td.center,td.num{text-align:center;font-weight:700}',
      'td.name{font-weight:700;color:#1b3f5b}',
      '.coverage-table th:nth-child(1){width:29%}.coverage-table th:nth-child(2){width:12%}',
      '.coverage-table th:nth-child(3),.coverage-table th:nth-child(4),.coverage-table th:nth-child(5){width:11%}',
      '.coverage-table th:nth-child(6),.coverage-table th:nth-child(7){width:13%}',
      '.detail-table{margin-top:3px}',
      '.detail-table th:nth-child(1){width:12%}.detail-table th:nth-child(2){width:13%}',
      '.detail-table th:nth-child(3){width:21%}.detail-table th:nth-child(4){width:29%}',
      '.detail-table th:nth-child(5){width:15%}.detail-table th:nth-child(6){width:10%}',
      '.detail-table td{font-size:7.6px;padding:3.7px 5px;line-height:1.15}',
      '.detail-table .url{font-size:7px;word-break:break-word;overflow-wrap:anywhere}',
      '.detail-table .url a{color:#125e99;text-decoration:underline;text-underline-offset:2px}',
      '.section-title{padding-top:11px}',
      '.footer{margin-top:16px;padding-top:6px;border-top:2px solid #bfd7e9;display:flex;justify-content:space-between;color:#63819a;font-size:8px;gap:12px}',
      '.footer strong{color:#1f608e}',
      '@media screen{body{padding:25px;max-width:1230px;margin:auto;box-shadow:0 0 14px #dde5ed}}',
      '@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact};}',
    ].join("");
    const technical=isTech?
      '<h2 class="section-title">Detalhamento dos ambientes cadastrados ('+details.length+')</h2>'+
      '<table class="detail-table"><thead><tr><th>Município</th><th>Sistema</th><th>Entidade</th><th>URL</th>'+
      '<th>Situação</th><th>Última verificação</th></tr></thead><tbody>'+detailsRows+'</tbody></table>':"";
    const doc='<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><title>'+caption+' — Cobertura dos Sistemas</title>'+
      '<style>'+style+'</style></head><body>'+
      '<div class="brand"><div class="brand-name"><span class="icon">S&S</span>Monitor Grupo S&S</div>'+
      '<div class="stamp">Ceará · '+esc(scopes[sc])+'<br/>Emissão: '+esc(now())+'</div></div>'+
      '<h1>Relatório de Cobertura dos Sistemas</h1>'+
      '<p class="subtitle">'+esc(caption)+' · Municípios e ambientes presentes no Monitor de Portais S&S</p>'+
      '<div class="stats">'+kpiHTML+'</div>'+
      '<p class="note">Cobertura = municípios atendidos neste recorte / '+esc(statewideTotal)+
      ' municípios do Ceará. Os valores online refletem a última consulta registrada, não disponibilidade em tempo real.</p>'+
      '<h2>Cobertura municipal ('+cities.length+' municípios)</h2>'+
      '<table class="coverage-table"><thead><tr><th>Município</th><th>IBGE</th><th>Portal</th><th>Fluxus</th>'+
      '<th>Veículos</th><th>Ambientes</th><th>Online</th></tr></thead><tbody>'+coverage+'</tbody></table>'+
      technical+
      '<div class="footer"><span>Fonte: Monitor Grupo S&S · Cadastros e últimas verificações</span>'+
      '<strong>Documento gerado localmente para consulta</strong></div></body></html>';
    win.document.open();win.document.write(doc);win.document.close();
    const start=()=>{try{win.focus();win.print()}catch(e){console.error("Relatório PDF:",e)}};
    if(win.document.readyState==="complete")setTimeout(start,350);
    else win.addEventListener("load",()=>setTimeout(start,350),{once:true});
  }
  function attach(host){
    const layer=host.querySelector("[data-ss-map]");
    if(!layer||layer.dataset.coverageReport)return;
    layer.dataset.coverageReport="1";
    const data={cities:null,modes:[],selected:"",selectedName:""};
    const back=layer.querySelector("[data-sm-back]");
    const head=layer.querySelector(".ss-map-head");
    if(!back||!head)return;
    const controls=document.createElement("div");controls.className="ss-map-report-actions";
    back.parentElement.insertBefore(controls,back);
    controls.append(back);
    const open=document.createElement("button");
    open.type="button";open.className="ss-map-report-open";
    open.textContent="▤ Relatório de Cobertura";open.title="Consultar e exportar cobertura por município";
    open.disabled=true;controls.prepend(open);
    layer.addEventListener("ss-map-data-ready",e=>{data.cities=e.detail?.cities||[];open.disabled=false});
    layer.addEventListener("ss-map-filter-change",e=>{data.modes=e.detail?.modes||[]});
    layer.addEventListener("ss-map-city-selected",e=>{
      data.selected=e.detail?.key||"";data.selectedName=e.detail?.name||"";
    });
    open.addEventListener("click",()=>{
      if(!data.cities){return}
      layer.querySelector(".ss-map-report-backdrop")?.remove();
      const overlay=document.createElement("div");overlay.className="ss-map-report-backdrop";
      overlay.innerHTML='<section class="ss-map-report-window" role="dialog" aria-modal="true" aria-label="Relatório de Cobertura dos Sistemas">'+
        '<div class="ss-map-report-head"><div><h2>Relatório de Cobertura</h2><p>Municípios, sistemas e ambientes cadastrados no Monitor S&S.</p></div>'+
        '<button type="button" class="ss-map-report-close" aria-label="Fechar relatório">✕</button></div>'+
        '<div class="ss-map-report-controls"><label>Abrangência <select data-coverage-scope>'+
          '<option value="all">Todos os municípios do Ceará</option>'+
          '<option value="covered">Somente municípios com sistemas</option>'+
          '<option value="filtered">Aplicar combinação de filtros do mapa</option>'+
          '<option value="selected">Somente município selecionado</option>'+
        '</select></label><div class="ss-map-report-actions2"><button type="button" data-report-excel class="excel">↓ Exportar Excel (.xlsx)</button>'+
        '<button type="button" data-report-pdf class="pdf">▤ Gerar PDF</button></div></div>'+
        '<div class="ss-map-report-message" data-report-feedback aria-live="polite"></div>'+
        '<div class="ss-map-report-metrics" data-report-metrics></div>'+
        '<div class="ss-map-report-table-wrap"><table class="ss-map-report-table"><thead><tr>'+
        '<th>Município</th><th>IBGE</th><th>Portal</th><th>Fluxus</th><th>Veículos</th><th>Ambientes</th><th>Online</th>'+
        '</tr></thead><tbody data-report-preview></tbody></table></div>'+
        '<div class="ss-map-report-footer"><span data-report-count></span>'+
        '<span>Excel: 3 abas. No PDF, escolha “Salvar como PDF” e desative “Cabeçalhos e rodapés” na janela de impressão.</span></div></section>';
      layer.append(overlay);
      const choose=overlay.querySelector("[data-coverage-scope]");
      const msg=overlay.querySelector("[data-report-feedback]");
      const result=()=>rowsFor(data,choose.value);
      function render(){
        const cities=result(),stats=summary(cities);
        overlay.querySelector("[data-report-metrics]").innerHTML=
          [["Municípios",stats.municipios],["Atendidos",stats.covered],
           ["Sem cadastro",stats.missing],["Ambientes",stats.environments],
           ["Online na última leitura",stats.online]].map(([label,value])=>
             '<div><b>'+value+'</b><span>'+label+'</span></div>').join("");
        const lines=cities.slice(0,18).map(c=>'<tr><td>'+esc(c.name)+'</td><td>'+esc(c.code||"")+'</td>'+
          SYS.map(([m])=>'<td>'+(c.systems[m]?.length?"✓":"—")+'</td>').join("")+
          '<td>'+nEnvs(c)+'</td><td>'+nOnline(c)+'</td></tr>').join("");
        overlay.querySelector("[data-report-preview]").innerHTML=lines||
          '<tr><td colspan="7">Nenhum município encontrado para este recorte.</td></tr>';
        overlay.querySelector("[data-report-count]").textContent=
          'Prévia: '+Math.min(cities.length,18)+' de '+cities.length+' municípios (exportação completa).';
        const hasFilters=data.modes.length>0;
        msg.textContent=choose.value==="filtered"&&!hasFilters?
          'Nenhum filtro ativo no mapa. Neste recorte serão incluídos todos os municípios com sistema cadastrado.':
          choose.value==="selected"?'Município: '+(data.selectedName||"não selecionado"):
          'Relatório atualizado com a situação dos cadastros disponíveis nesta sessão.';
      }
      choose.onchange=render;render();
      overlay.querySelector(".ss-map-report-close").onclick=()=>overlay.remove();
      overlay.addEventListener("click",e=>{if(e.target===overlay)overlay.remove()});
      overlay.querySelector("[data-report-excel]").onclick=()=>{
        try{
          const cities=result();
          if(!cities.length){msg.textContent="Não há municípios neste recorte.";return}
          download(makeXlsx(cities,choose.value),"cobertura_sistemas_CE_"+dateKey()+".xlsx");
          msg.textContent="Planilha Excel gerada com resumo, cobertura e ambientes.";
        }catch(err){console.error(err);msg.textContent="Não foi possível gerar o Excel: "+String(err.message||err)}
      };
      overlay.querySelector("[data-report-pdf]").onclick=()=>{
        try{
          const cities=result();
          if(!cities.length){msg.textContent="Não há municípios neste recorte.";return}
          printPdf(cities,choose.value);
          msg.textContent="Na janela de impressão, escolha a opção Salvar como PDF.";
        }catch(err){console.error(err);msg.textContent=String(err.message||err)}
      };
      overlay.addEventListener("keydown",e=>{if(e.key==="Escape"){e.stopPropagation();overlay.remove()}});
      overlay.querySelector(".ss-map-report-close").focus();
    });
  }
  window.ssMapOpen=function(host){
    previous(host);
    attach(host);
  };
})();