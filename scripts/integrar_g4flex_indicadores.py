#!/usr/bin/env python3
"""Integra painel de indicadores ao Monitor G4Flex, sem modificar o robô nem o polling."""
from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
path=root/"main.py"
source=path.read_text(encoding="utf-8")
insights_js=(root/"scripts"/"g4flex_indicadores.js").read_text(encoding="utf-8").strip()
insights_css=(root/"scripts"/"g4flex_indicadores.css").read_text(encoding="utf-8").strip()
tooltip_js=(root/"scripts"/"g4flex_tooltip_filas.js").read_text(encoding="utf-8").strip()
daily_report_js=(root/"scripts"/"g4flex_relatorio_dia.js").read_text(encoding="utf-8").strip()
official_logo_js=(root/"scripts"/"logo_grupo_ss_oficial.js").read_text(encoding="utf-8").strip()

def insert_once(marker,piece,where,tag):
    global source
    if tag in source:
        if source.count(tag)!=1:
            raise SystemExit(f"{tag} duplicado.")
        return
    if source.count(marker)!=1 and marker.startswith(" "):
        stripped=marker.lstrip(" ")
        if source.count(stripped)==1:
            ix=source.index(stripped)
            line_start=source.rfind("\n",0,ix)+1
            prefix=source[line_start:ix]
            if not prefix.strip():
                marker=prefix+stripped
    if source.count(marker)!=1:
        raise SystemExit(f"Marcador {tag} encontrado {source.count(marker)} vezes.")
    if where=="before":
        source=source.replace(marker,piece+"\n"+marker,1)
    elif where=="after":
        source=source.replace(marker,marker+"\n"+piece,1)
    else:
        raise SystemExit("Posição inválida")

css_anchor="        .g4f-board.g4f-ss-mode .ss-list-panel .ss-attendants-table tbody tr.is-paused:not(.has-assignment):not(.is-calling){background:#f4f8ff}"
insert_once(css_anchor,insights_css,"before","/* G4Flex - página informativa de indicadores.")

js_anchor="            function g4fStart(host){"
insert_once(js_anchor,insights_js,"before","/* Painel analítico G4Flex - não faz novas chamadas")
insert_once(js_anchor,tooltip_js,"before","/* Tooltip acessível de filas G4Flex:")
insert_once("/* Tooltip acessível de filas G4Flex:",daily_report_js,"before","/* Relatório diário G4Flex:")

init_anchor='                 host.querySelector(\'[data-ss="search"]\').value=g4fSearchText;'
insert_once(init_anchor,'                 g4fInsightsInit(host);',"before","                 g4fInsightsInit(host);")
insert_once(init_anchor,'                 g4fQueueTooltipInit(host);',"before","                 g4fQueueTooltipInit(host);")

render_anchor="                     host.querySelector('[data-g4f=\"clock\"]').textContent=new Date().toLocaleTimeString('pt-BR');"
insert_once(render_anchor,"                     g4fInsightsRender(host,row);","after","                     g4fInsightsRender(host,row);")

# Atualização idempotente: sincroniza os módulos CSS/JS incorporados no main.py.
def sync_embedded(start_tag, next_tag, fresh):
    global source
    i=source.find(start_tag)
    if i<0:raise SystemExit("Módulo já integrado não encontrado: "+start_tag)
    j=source.find(next_tag,i)
    if j<0:raise SystemExit("Fim do módulo não encontrado: "+next_tag)
    source=source[:i]+fresh+"\n"+source[j:]

sync_embedded("/* G4Flex - página informativa de indicadores.",css_anchor,insights_css)
# Reconstrói o bloco único em ordem determinística; evita conflito com outros
# usos da logomarca no arquivo principal.
sync_embedded("/* Painel analítico G4Flex - não faz novas chamadas","/* Tooltip acessível de filas G4Flex:",insights_js+"\n"+official_logo_js+"\n"+daily_report_js)
sync_embedded("/* Tooltip acessível de filas G4Flex:",js_anchor,tooltip_js)

ast.parse(source)
assert source.count("function g4fInsightsRender(host,row)")==1
assert source.count("function g4fInsightsInit(host)")==1
assert source.count("function g4fQueueTooltipInit(host)")==1
assert source.count("function g4fDailyReportHTML(row)")==1
_idx_start=source.index("/* Painel analítico G4Flex - não faz novas chamadas")
_idx_tip=source.index("/* Tooltip acessível de filas G4Flex:",_idx_start)
_idx_report=source.find("/* Relatório diário G4Flex:",_idx_start)
_idx_logo=source.find("/* Logo oficial Grupo S&S",_idx_start)
_count_global=source.count("window.__SS_OFICIAL_LOGO__=")
_count_section=source[_idx_start:_idx_tip].count("window.__SS_OFICIAL_LOGO__=")
print("DIAG identidade: limites",_idx_start,_idx_logo,_idx_report,_idx_tip,"marcas totais",_count_global,"marcas no bloco",_count_section)
assert _count_section==1
assert "Soma das faixas horárias" not in source[source.index("/* Painel analítico G4Flex - não faz novas chamadas"):source.index("/* Tooltip acessível de filas G4Flex:")]
assert source.count("function g4fExportDailyReport(row)")==1
assert source.count("g4fQueueTooltipInit(host);")==1
assert source.count("g4fInsightsInit(host);")==1
assert source.count("g4fInsightsRender(host,row);")==1
path.write_text(source,encoding="utf-8")
print("OK: ranking de filas e relatório diário integrados, sem novas consultas.")
