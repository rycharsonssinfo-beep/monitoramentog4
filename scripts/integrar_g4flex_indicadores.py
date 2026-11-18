#!/usr/bin/env python3
"""Integra painel de indicadores ao Monitor G4Flex, sem modificar o robô nem o polling."""
from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
path=root/"main.py"
source=path.read_text(encoding="utf-8")
insights_js=(root/"scripts"/"g4flex_indicadores.js").read_text(encoding="utf-8").strip()
insights_css=(root/"scripts"/"g4flex_indicadores.css").read_text(encoding="utf-8").strip()

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

init_anchor='                 host.querySelector(\'[data-ss="search"]\').value=g4fSearchText;'
insert_once(init_anchor,'                 g4fInsightsInit(host);',"before","                 g4fInsightsInit(host);")

render_anchor="                     host.querySelector('[data-g4f=\"clock\"]').textContent=new Date().toLocaleTimeString('pt-BR');"
insert_once(render_anchor,"                     g4fInsightsRender(host,row);","after","                     g4fInsightsRender(host,row);")

ast.parse(source)
assert source.count("function g4fInsightsRender(host,row)")==1
assert source.count("function g4fInsightsInit(host)")==1
assert source.count("g4fInsightsInit(host);")==1
assert source.count("g4fInsightsRender(host,row);")==1
path.write_text(source,encoding="utf-8")
print("OK: botão Indicadores, tela completa e atualização pelo snapshot existente integrados.")
