#!/usr/bin/env python3
"""Oculta usuários não pertencentes ao escopo de suporte no painel de atendimento."""
from pathlib import Path
import ast

main=Path(__file__).resolve().parents[1]/"main.py"
source=main.read_text(encoding="utf-8")

def replace_once(old,new,meaning):
    global source
    if new in source:
        if source.count(new)!=1:raise SystemExit(f"Novo marcador duplicado: {meaning}")
        return
    if source.count(old)!=1:raise SystemExit(f"Marcador {meaning}: encontrado {source.count(old)} vezes")
    source=source.replace(old,new,1)

anchor="             const ssOffices={"
addition=(
"             // Exclusão temporária na interface; não é permissão de acesso ao Supabase.\n"
"             const g4fHiddenNames=new Set(['Cislena Cisne','Marla Lima','Emanuela Costa'].map(ssNormalizeName));\n"
"             const g4fVisibleAgent=agent=>!g4fHiddenNames.has(ssNormalizeName(agent?.nome));\n"
)
replace_once(anchor,addition+anchor,"lista de exclusão")
replace_once(
"                 for(const a of (Array.isArray(row.atendentes)?row.atendentes:[])){",
"                 for(const a of (Array.isArray(row.atendentes)?row.atendentes:[])){\n"
"                     if(!g4fVisibleAgent(a))continue;",
"alertas de atribuição",
)
replace_once(
"                 const all=Array.isArray(row?.atendentes)?row.atendentes:[];",
"                 const all=Array.isArray(row?.atendentes)?row.atendentes.filter(g4fVisibleAgent):[];",
"contadores S&S",
)
replace_once(
"                 const allAgents=Array.isArray(row?.atendentes)?row.atendentes:[];",
"                 const allAgents=Array.isArray(row?.atendentes)?row.atendentes.filter(g4fVisibleAgent):[];",
"lista de atendentes dos dois layouts",
)
replace_once(
"                     ['◉','Disponíveis',r.agentes_disponiveis,'green'],",
"                     ['◉','Disponíveis',all.filter(a=>a.status==='ativo').length,'green'],",
"disponíveis S&S",
)
replace_once(
"                     ['▣','Em atendimento',r.conversas_em_atendimento,'blue'],",
"                     ['▣','Em atendimento',all.reduce((sum,a)=>sum+Math.max(0,Number(a.em_atendimento)||0),0),'blue'],",
"conversas S&S",
)
replace_once(
"                     ['♧','Total logados',r.usuarios_logados,'navy'],",
"                     ['♧','Total monitorados',all.length,'navy'],",
"total monitorado S&S",
)
old="                 const query=g4fSearchText.toLocaleLowerCase('pt-BR');"
new=(
"                 const scopedKpis={\n"
"                     usuarios_logados:allAgents.length,\n"
"                     agentes_disponiveis:allAgents.filter(a=>a.status==='ativo').length,\n"
"                     agentes_em_pausa:allAgents.filter(a=>a.status==='pausado').length,\n"
"                     conversas_em_atendimento:allAgents.reduce((sum,a)=>sum+Math.max(0,Number(a.em_atendimento)||0),0),\n"
"                 };\n"
"                 const query=g4fSearchText.toLocaleLowerCase('pt-BR');"
)
replace_once(old,new,"contadores originais G4Flex")
replace_once(
"                     stamp.textContent=row?`Última atualização: ${g4fTime(row.recebido_em)} · ${row.total_cartoes??'—'} atendentes`:'Aguardando primeira leitura';",
"                     stamp.textContent=row?`Última atualização: ${g4fTime(row.recebido_em)} · ${allAgents.length} atendentes monitorados`:'Aguardando primeira leitura';",
"total da última leitura",
)
replace_once(
"g4fNumber(r[key])}</span><small>${g4fText(description)}",
"g4fNumber(Object.prototype.hasOwnProperty.call(scopedKpis,key)?scopedKpis[key]:r[key])}</span><small>${g4fText(description)}",
"valores dos cartões G4Flex",
)
replace_once(
"                     host.querySelector('[data-g4f=\"count\"]').textContent=`Exibindo ${agents.length} de ${Array.isArray(row?.atendentes)?row.atendentes.length:0} atendentes`;",
"                     host.querySelector('[data-g4f=\"count\"]').textContent=`Exibindo ${agents.length} de ${allAgents.length} atendentes monitorados`;",
"denominador de atendentes",
)
replace_once(
"['Pausa ativa','agentes_em_pausa_ativa','#496bdf','Indicador original'],",
"['Pausa ativa','agentes_em_pausa_ativa','#496bdf','Indicador global do G4Flex'],",
"indicador global de pausa ativa",
)
replace_once(
"['Totalmente ocupados','agentes_totalmente_ocupados','#d97706','Indicador original'],",
"['Totalmente ocupados','agentes_totalmente_ocupados','#d97706','Indicador global do G4Flex'],",
"indicador global de ocupação",
)
replace_once(
"['Não atendidas','conversas_nao_atendidas','#db3943','Conversas aguardando'],",
"['Não atendidas','conversas_nao_atendidas','#db3943','Conversas aguardando · indicador global'],",
"indicador global de conversas pendentes",
)
ast.parse(source,filename=str(main))
if source.count("const g4fVisibleAgent=")!=1:raise SystemExit("Filtro ausente ou duplicado")
if source.count("atendentes.filter(g4fVisibleAgent)")!=2:raise SystemExit("Filtragem incompleta")
main.write_text(source,encoding="utf-8")
print("OK: três atendentes ocultados dos layouts G4Flex e S&S, contadores e alertas filtrados.")
