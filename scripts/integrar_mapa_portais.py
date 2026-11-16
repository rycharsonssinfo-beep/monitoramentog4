#!/usr/bin/env python3
"""Integra o Mapa de Sistemas dentro do cabeçalho do Monitor de Portais S&S."""
from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
main=root/"main.py"
js=(root/"scripts"/"mapa_sistemas_embed.js").read_text(encoding="utf-8")
source=main.read_text(encoding="utf-8")
anchor="function portalStart(host){"
button_anchor='<button type="button" class="portal-report-trigger" data-portal="report-button">Relatórios</button>'
new_button='<button type="button" class="ss-map-open" data-portal="map-button">Mapa de Sistemas</button>'
event_anchor='host.querySelector(\'[data-portal="report-button"]\').onclick=()=>portalOpenReport(host);'
event='host.querySelector(\'[data-portal="map-button"]\').onclick=()=>window.ssMapOpen(host);'
if source.count(anchor)!=1 or source.count(button_anchor)!=1 or source.count(event_anchor)!=1:
    raise SystemExit(f"Âncoras mudaram: function={source.count(anchor)}, botão={source.count(button_anchor)}, listener={source.count(event_anchor)}; nada foi alterado.")
if "window.ssMapOpen=function(host)" in source:
    print("Mapa já integrado. Sem alterações.")
    raise SystemExit(0)
source=source.replace(anchor,js+"\n"+anchor,1)
source=source.replace(button_anchor,button_anchor+new_button,1)
source=source.replace(event_anchor,event_anchor+"\n  "+event,1)
ast.parse(source,filename=str(main))
main.write_text(source,encoding="utf-8")
print("Mapa integrado ao monitor de portais; validação Python aprovada.")
