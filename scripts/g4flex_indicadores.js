/* Painel analítico G4Flex - não faz novas chamadas ao G4Flex ou Supabase.
   Lê apenas o snapshot já recebido por g4fPoll. */
const g4fReportCols=[
 ['horario','Horário'],['abertas','Abertas'],['atendidas','Atendidas'],
 ['nao_atendidas','Não atendidas'],['encerradas','Encerradas'],
 ['abandonadas','Abandonadas'],['tme','TME'],['tma','TMA'],
 ['tmo','TMO'],['tta','TTA'],['primeira_resposta','1ª Resp.'],
 ['tmr','T.M.R'],['tm_atribuicao','TM atrib.'],['nivel_servico','N. serviço'],
 ['nivel_atendimento','N. atend.'],['volume_projetado','Vol. projetado'],
 ['volume_total','Volume total']
];
function g4fReportNumber(value){
 const n=Number(value);return Number.isFinite(n)?Math.max(0,n):0;
}
function g4fReportHours(row){
 const raw=row?.resumo?.matriz_horaria;
 if(!Array.isArray(raw))return [];
 return raw.filter(x=>x&&typeof x==='object').slice(0,48);
}
function g4fReportQueues(row){
 const r=row?.resumo||{};
 // Campo próprio quando disponível; compatibilidade com o ranking já publicado pelo coletor.
 const raw=Array.isArray(r.ranking_filas)?r.ranking_filas:r.ranking_motivos;
 if(!Array.isArray(raw))return [];
 return raw.map(x=>({nome:String(x?.fila||x?.nome||x?.motivo||'').trim(),
   quantidade:g4fReportNumber(x?.quantidade??x?.total??x?.atendimentos??x?.qtd)}))
   .filter(x=>x.nome&&x.quantidade>0).sort((a,b)=>b.quantidade-a.quantidade).slice(0,10);
}
function g4fReportReasons(row){return g4fReportQueues(row);}
function g4fReportKpi(label,value,note,shade){
 return `<div class="g4f-report-kpi"><small>${g4fText(label)}</small>
    <strong class="${shade||''}">${g4fText(value)}</strong>
    <span>${g4fText(note)}</span></div>`;
}
function g4fReportPlot(hours){
 if(!hours.length)return '<div class="g4f-report-empty">A matriz horária ainda não foi enviada pelo robô G4Flex. Os números históricos serão exibidos aqui quando a coleta estiver integrada.</div>';
 const maximum=Math.max(1,...hours.map(x=>Math.max(g4fReportNumber(x.abertas),g4fReportNumber(x.atendidas))));
 return `<div class="g4f-report-chart-legend"><i class="open"></i>Abertas <i class="answered"></i>Atendidas</div>
 <div class="g4f-report-plot" role="img" aria-label="Comparação de conversas abertas e atendidas por horário">
 ${hours.map(x=>`<div class="g4f-report-plot-column" title="${g4fText(x.horario||'')}">
    <div class="g4f-report-bars"><div class="open" style="height:${Math.max(2,g4fReportNumber(x.abertas)/maximum*100)}%"></div>
    <div class="answered" style="height:${Math.max(2,g4fReportNumber(x.atendidas)/maximum*100)}%"></div></div>
    <small>${g4fText(x.horario||'—')}</small></div>`).join('')}</div>`;
}
function g4fReportTable(hours){
 if(!hours.length)return '<div class="g4f-report-empty">Nenhum indicador por horário disponível nesta coleta.</div>';
 return `<div class="g4f-report-table-scroll" role="region" aria-label="Matriz horária de indicadores" tabindex="0">
 <table class="g4f-report-table"><thead><tr>${g4fReportCols.map(([key,name])=>`<th scope="col" title="${g4fText(name)}">${g4fText(name)}</th>`).join('')}</tr></thead>
 <tbody>${hours.map(row=>`<tr>${g4fReportCols.map(([key])=>`<td>${g4fText(row[key]??'—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function g4fReportRanking(reasons){
 if(!reasons.length)return '<div class="g4f-report-empty">O ranking de filas ainda não está disponível na coleta do robô.</div>';
 const max=Math.max(1,reasons[0].quantidade);
 return `<div class="g4f-report-ranking">${reasons.map((r,i)=>`<div class="g4f-report-reason">
  <span class="g4f-report-rank">${i+1}</span><span class="g4f-report-reason-name" title="${g4fText(r.nome)}">${g4fText(r.nome)}</span>
  <div class="g4f-report-reason-track"><div style="width:${Math.max(2,(r.quantidade/max)*100)}%"></div></div>
  <strong>${g4fText(r.quantidade)}</strong></div>`).join('')}</div>`;
}
function g4fInsightsRender(host,row){
 const screen=host?.querySelector('.g4f-insights');
 if(!screen||screen.hidden)return;
 const all=Array.isArray(row?.atendentes)?row.atendentes.filter(g4fVisibleAgent):[];
 const r=row?.resumo||{};
 const hours=g4fReportHours(row),reasons=g4fReportQueues(row);
 const current=[
  ['Atendentes monitorados',all.length,'Equipe de suporte'],
  ['Disponíveis',all.filter(a=>a.status==='ativo').length,'Estado atual'],
  ['Em pausa',all.filter(a=>a.status==='pausado').length,'Estado atual'],
  ['Em atendimento',all.reduce((sum,a)=>sum+g4fReportNumber(a.em_atendimento),0),'Conversas da equipe']
 ];
 screen.querySelector('[data-g4f-report-current]').innerHTML=current.map(x=>g4fReportKpi(...x)).join('');
 const sum=(k)=>hours.reduce((v,h)=>v+g4fReportNumber(h[k]),0);
 const reports=hours.length?[
  ['Abertas',sum('abertas'),'Soma das faixas horárias'],
  ['Atendidas',sum('atendidas'),'Soma das faixas horárias'],
  ['Não atendidas',sum('nao_atendidas'),'Soma das faixas horárias'],
  ['Abandonadas',sum('abandonadas'),'Soma das faixas horárias']
 ]:[];
 // Evita reconstruir os gráficos a cada polling (3 s) quando os dados não mudaram.
 // Assim a rolagem da matriz continua no mesmo ponto durante a leitura.
 const historyKey=JSON.stringify([hours,reasons]);
 if(screen._g4fReportHistoryKey!==historyKey){
  screen.querySelector('[data-g4f-report-historical]').innerHTML=reports.length?reports.map(x=>g4fReportKpi(...x)).join('')
   :'<div class="g4f-report-empty g4f-report-empty-span">Resumo horário pendente de integração com o coletor.</div>';
  screen.querySelector('[data-g4f-report-plot]').innerHTML=g4fReportPlot(hours);
  screen.querySelector('[data-g4f-report-table]').innerHTML=g4fReportTable(hours);
  screen.querySelector('[data-g4f-report-ranking]').innerHTML=g4fReportRanking(reasons);
  screen._g4fReportHistoryKey=historyKey;
 }
 const stamp=screen.querySelector('[data-g4f-report-stamp]');
 stamp.textContent=row?'Última leitura do G4Flex: '+g4fTime(row.recebido_em):'Aguardando primeira leitura do G4Flex';
 const status=screen.querySelector('[data-g4f-report-availability]');
 status.textContent=(hours.length||reasons.length)?'Indicadores históricos recebidos':'Aguardando indicadores históricos do robô';
 status.classList.toggle('ready',Boolean(hours.length||reasons.length));
}
function g4fInsightsInit(host){
 if(!host||host.querySelector('.g4f-insights'))return;
 const section=document.createElement('section');
 section.className='g4f-insights';
 section.hidden=true;
 section.setAttribute('role','dialog');
 section.setAttribute('aria-modal','true');
 section.setAttribute('aria-label','Indicadores e desempenho G4Flex');
 section.innerHTML=`<div class="g4f-insights-content">
  <header class="g4f-report-head">
   <div><div class="g4f-report-eyebrow">GRUPO S&S · G4FLEX</div>
     <h2>Indicadores e desempenho</h2><p>Matriz horária e ranking de filas</p></div>
   <div class="g4f-report-head-actions"><button type="button" class="g4f-report-daily-btn" data-g4f-report-daily>▣ Relatório do dia</button>
   <button type="button" class="g4f-insights-close" data-g4f-insights-close>← Voltar ao atendimento</button></div>
  </header>
  <div class="g4f-report-meta"><span data-g4f-report-stamp>Aguardando coleta</span>
   <span class="g4f-report-availability" data-g4f-report-availability>Aguardando indicadores históricos do robô</span></div>
  <div class="g4f-report-scroll">
   <section class="g4f-report-block"><div class="g4f-report-section-head"><h3>Equipe de suporte agora</h3><small>Dados instantâneos · somente atendentes monitorados</small></div>
     <div class="g4f-report-kpis" data-g4f-report-current></div></section>
   <section class="g4f-report-block"><div class="g4f-report-section-head"><h3>Resumo das faixas horárias</h3><small>Indicadores consolidados da matriz do G4Flex, quando disponíveis</small></div>
     <div class="g4f-report-kpis" data-g4f-report-historical></div></section>
   <section class="g4f-report-block"><div class="g4f-report-section-head"><h3>Volume de atendimento por horário</h3><small>Abertas × Atendidas</small></div>
     <div data-g4f-report-plot></div></section>
   <section class="g4f-report-block"><div class="g4f-report-section-head"><h3>Matriz horária detalhada</h3><small>Deslize horizontalmente para consultar todas as métricas</small></div>
     <div data-g4f-report-table></div></section>
   <section class="g4f-report-block"><div class="g4f-report-section-head"><h3>Ranking de filas</h3><small>Top 10 · classificação registrada no G4Flex</small></div>
     <div data-g4f-report-ranking></div></section>
   <p class="g4f-report-disclaimer">A matriz horária e o ranking de filas podem representar toda a operação do G4Flex. O ranking é recebido atualmente como classificação de motivos do G4Flex. A visão de equipe acima considera somente os atendentes habilitados no Monitor S&S. Não confunda indicadores históricos gerais com resultados individuais da equipe de suporte.</p>
  </div>
 </div>`;
 host.appendChild(section);
 const close=section.querySelector('[data-g4f-insights-close]');
 section.querySelector('[data-g4f-report-daily]').addEventListener('click',()=>g4fExportDailyReport(g4fLastData));
 function hide(){section.hidden=true;host._g4fInsightsOpen=false;}
 close.addEventListener('click',hide);
 section.addEventListener('keydown',ev=>{if(ev.key==='Escape')hide();});
 for(const parent of host.querySelectorAll('.g4f-top-actions')){
  const btn=document.createElement('button');
  btn.type='button';btn.className='g4f-insights-trigger';btn.textContent='▤ Indicadores';
  btn.setAttribute('aria-label','Abrir matriz horária e ranking de filas G4Flex');
  btn.addEventListener('click',()=>{host._g4fInsightsOpen=true;section.hidden=false;g4fInsightsRender(host,g4fLastData);close.focus();});
  parent.prepend(btn);
 }
}
