/* Relatório diário G4Flex: gera documento imprimível a partir do snapshot existente.
   Não acessa o G4Flex, o Supabase ou qualquer servidor adicional. */
function g4fDailyEscape(v){
 return String(v??'—').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function g4fDailyDate(value){
 if(!value)return {date:'Não informada',datetime:'Não informado'};
 const time=new Date(value);
 if(!Number.isFinite(time.getTime()))return {date:'Não informada',datetime:'Não informado'};
 const common={timeZone:'America/Fortaleza'};
 return {
  date:new Intl.DateTimeFormat('pt-BR',{...common,day:'2-digit',month:'2-digit',year:'numeric'}).format(time),
  datetime:new Intl.DateTimeFormat('pt-BR',{...common,day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(time)
 };
}
function g4fDailyReportHTML(row){
 const hours=g4fReportHours(row);
 const queues=g4fReportQueues(row);
 if(!hours.length&&!queues.length)return null;
 const r=row?.resumo||{};
 const clock=g4fDailyDate(r.indicadores_historicos_coletados_em||row?.capturado_em||row?.recebido_em);
 const emitted=g4fDailyDate(new Date().toISOString());
 const total=k=>hours.reduce((acc,x)=>acc+g4fReportNumber(x[k]),0);
 const stats=hours.length?[
  ['Conversas abertas',total('abertas')],
  ['Atendidas',total('atendidas')],
  ['Não atendidas',total('nao_atendidas')],
  ['Abandonadas',total('abandonadas')]
 ]:[];
 const statsHTML=stats.length?stats.map(([label,value])=>
  '<div class="metric"><span>'+g4fDailyEscape(label)+'</span><strong>'+g4fDailyEscape(value)+'</strong><small>Soma das faixas horárias</small></div>'
 ).join(''):'<p class="empty">Matriz horária não disponível nesta coleta.</p>';
 const matrixHTML=hours.length?
  '<table class="matrix"><thead><tr>'+g4fReportCols.map(([key,label])=>'<th>'+g4fDailyEscape(label)+'</th>').join('')+'</tr></thead><tbody>'+
  hours.map(hour=>'<tr>'+g4fReportCols.map(([key])=>'<td>'+g4fDailyEscape(hour[key]??'—')+'</td>').join('')+'</tr>').join('')+'</tbody></table>':
  '<p class="empty">Matriz horária não disponível nesta coleta.</p>';
 const max=Math.max(1,...queues.map(x=>x.quantidade));
 const rankingHTML=queues.length?queues.map((x,index)=>
  '<div class="rank"><span class="number">'+(index+1)+'</span><strong>'+g4fDailyEscape(x.nome)+'</strong>'+
  '<div class="bar"><span style="width:'+Math.min(100,Math.max(1,x.quantidade/max*100)).toFixed(2)+'%"></span></div>'+
  '<b>'+g4fDailyEscape(x.quantidade)+'</b></div>'
 ).join(''):'<p class="empty">Ranking de filas não disponível nesta coleta.</p>';
 const note=Array.isArray(r.ranking_filas)?'Ranking de filas informado pelo G4Flex.':
  'O ranking foi publicado pelo G4Flex como classificação de motivos (ranking_motivos). A correspondência com filas operacionais ainda não foi validada.';
 const css=`
  @page{size:A4 landscape;margin:12mm 10mm}
  *{box-sizing:border-box}
  body{margin:0;background:#eef4fb;color:#16395f;font:12px/1.42 Arial,Helvetica,sans-serif}
  .actions{display:flex;gap:10px;justify-content:flex-end;max-width:1320px;margin:16px auto 0;padding:0 15px}
  .actions button{border:1px solid #a4c9e9;background:#0b5fa5;color:#fff;border-radius:8px;padding:10px 18px;font:700 12px Arial;cursor:pointer}
  .actions button.secondary{background:white;color:#0b5fa5}
  .sheet{max-width:1320px;margin:12px auto 28px;background:#fff;padding:26px 30px;box-shadow:0 5px 24px #124b7924;border-radius:10px}
  .header{display:flex;gap:16px;align-items:center;justify-content:space-between;border-bottom:3px solid #1666a9;padding-bottom:17px}
  .brand{display:flex;align-items:center;gap:13px}
  .brandmark{background:#086a75;color:white;border-radius:12px;font:bold 24px Arial;padding:13px}
  .brandname{font-size:13px;font-weight:800;color:#086b75}
  h1{font-size:23px;margin:3px 0 0;color:#123b69}
  h2{font-size:15px;color:#143d68;margin:24px 0 10px}
  .meta{min-width:250px;text-align:right;font-size:11px;color:#466885}
  .meta strong{color:#103c68}
  .chip{display:inline-block;color:#91620b;background:#fff4d8;border:1px solid #f2dbaa;border-radius:30px;padding:5px 9px;font-weight:700;font-size:10px}
  .summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
  .metric{border:1px solid #d7e6f5;background:#f5faff;border-radius:9px;padding:12px 14px;display:flex;flex-direction:column;gap:4px}
  .metric span{font-size:11px;color:#51728d;font-weight:700}
  .metric strong{font-size:26px;line-height:1.2;color:#064e92}
  .metric small{font-size:9px;color:#718ba6}
  table.matrix{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.5px}
  .matrix th{background:#e5effa;color:#204d77;font-size:7px;padding:7px 3px;border:1px solid #cddfee;overflow-wrap:anywhere}
  .matrix th:first-child{width:9%}
  .matrix td{border:1px solid #dde9f3;text-align:center;padding:7px 2px;overflow-wrap:anywhere}
  .matrix td:first-child{text-align:left;font-weight:700;color:#0e4b80}
  .matrix tr:nth-child(even){background:#f7fbff}
  .rank{display:grid;grid-template-columns:20px minmax(150px,220px) 1fr 35px;align-items:center;gap:11px;padding:6px 0;border-bottom:1px solid #eaf2f8}
  .rank strong{font-size:11px}
  .number{text-align:center;color:#7592ad}
  .rank b{text-align:right;color:#0d5795}
  .bar{height:13px;border-radius:12px;background:#e5f0fa;overflow:hidden}
  .bar span{display:block;height:100%;border-radius:12px;background:linear-gradient(90deg,#1567c5,#2ba4d7)}
  .note{color:#5a7794;font-size:10px;line-height:1.6;margin-top:13px}
  footer{border-top:1px solid #d9e6f3;margin-top:25px;padding-top:11px;font-size:10px;color:#647f99;display:flex;justify-content:space-between;gap:16px}
  .empty{background:#f5f9fd;color:#6684a3;padding:16px;border-radius:7px}
  @media print{
    body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .actions{display:none!important}.sheet{max-width:none;margin:0;box-shadow:none;padding:0;border-radius:0}
    .summary,.rank{break-inside:avoid}
    h2{break-after:avoid}table.matrix thead{display:table-header-group}
    .matrix tr{break-inside:avoid}
  }
 `;
 return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
  '<title>Relatório G4Flex - '+g4fDailyEscape(clock.date)+'</title><style>'+css+'</style></head><body>'+
  '<div class="actions"><button type="button" onclick="window.print()">Imprimir / Salvar como PDF</button>'+
  '<button type="button" class="secondary" onclick="window.close()">Fechar</button></div>'+
  '<main class="sheet"><header class="header"><div class="brand"><span class="brandmark">S&amp;S</span>'+
  '<div><div class="brandname">GRUPO S&amp;S · MONITORAMENTO G4FLEX</div><h1>Relatório do dia</h1></div></div>'+
  '<div class="meta"><div><strong>Data de referência:</strong> '+g4fDailyEscape(clock.date)+'</div>'+
  '<div><strong>Última coleta histórica:</strong> '+g4fDailyEscape(clock.datetime)+'</div>'+
  '<div><strong>Emissão:</strong> '+g4fDailyEscape(emitted.datetime)+'</div>'+
  '<div style="margin-top:7px"><span class="chip">Dados parciais até a última coleta</span></div></div></header>'+
  '<h2>Resumo de atendimentos por horário</h2><div class="summary">'+statsHTML+'</div>'+
  '<h2>Matriz horária de indicadores</h2>'+matrixHTML+
  '<h2>Ranking de filas — Top 10</h2>'+rankingHTML+
  '<p class="note">'+g4fDailyEscape(note)+'</p>'+
  '<footer><span>Fonte: coleta automatizada do G4Flex. Os indicadores históricos podem abranger toda a operação, não apenas os atendentes exibidos no Monitor S&amp;S.</span>'+
  '<span>Grupo S&amp;S · Documento de acompanhamento operacional</span></footer></main></body></html>';
}
function g4fExportDailyReport(row){
 const html=g4fDailyReportHTML(row);
 if(!html){
   window.alert('Ainda não existem dados históricos recebidos para emitir o relatório do dia.');
   return false;
 }
 const win=window.open('','_blank');
 if(win){
   win.document.open();
   win.document.write(html);
   win.document.close();
   win.focus();
   return true;
 }
 // Se o navegador bloquear nova aba, entrega um HTML local imprimível.
 const blob=new Blob([html],{type:'text/html;charset=utf-8'});
 const uri=URL.createObjectURL(blob);
 const a=document.createElement('a');
 const time=g4fDailyDate(row?.resumo?.indicadores_historicos_coletados_em||row?.capturado_em);
 a.href=uri;a.download='Relatorio_G4Flex_'+time.date.replaceAll('/','-')+'.html';
 document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(uri),1200);
 window.alert('O navegador bloqueou a nova aba. O relatório foi salvo em HTML; abra-o e selecione Imprimir / Salvar como PDF.');
 return true;
}
