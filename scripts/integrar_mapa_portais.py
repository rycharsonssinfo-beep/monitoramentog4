#!/usr/bin/env python3
"""Sincroniza mapa e melhorias visuais ao main.py sem duplicar a navegação."""
from pathlib import Path
import ast
import json

root = Path(__file__).resolve().parents[1]
main = root / "main.py"
js = (root / "scripts" / "mapa_sistemas_embed.js").read_text(encoding="utf-8").strip()
extra_js = (root / "scripts" / "mapa_sistemas_enhance.js").read_text(encoding="utf-8").strip()
extra_css = (root / "scripts" / "mapa_sistemas_enhance.css").read_text(encoding="utf-8").strip()
logo_js = (root / "scripts" / "logo_grupo_ss_oficial.js").read_text(encoding="utf-8").strip()
report_js = (root / "scripts" / "mapa_sistemas_report.js").read_text(encoding="utf-8").strip()
report_css = (root / "scripts" / "mapa_sistemas_report.css").read_text(encoding="utf-8").strip()
css_js = (
    '(function(){if(!document.getElementById("ss-map-enhance-v21")){'
    'const tag=document.createElement("style");'
    'tag.id="ss-map-enhance-v21";'
    'tag.textContent=' + json.dumps(extra_css, ensure_ascii=False) + ';'
    'document.head.appendChild(tag);}})();'
)
report_css_js = (
    '(function(){if(!document.getElementById("ss-map-report-css")){'
    'const tag=document.createElement("style");'
    'tag.id="ss-map-report-css";'
    'tag.textContent=' + json.dumps(report_css, ensure_ascii=False) + ';'
    'document.head.appendChild(tag);}})();'
)
full = js + "\n" + css_js + "\n" + extra_js + "\n" + logo_js + "\n" + report_css_js + "\n" + report_js
source = main.read_text(encoding="utf-8")

start_marker = "(function ssMapInstall(){"
end_marker = "\nfunction portalStart(host){"
button_anchor = '<button type="button" class="portal-report-trigger" data-portal="report-button">Relatórios</button>'
new_button = '<button type="button" class="ss-map-open" data-portal="map-button">Mapa de Sistemas</button>'
event_anchor = 'host.querySelector(\'[data-portal="report-button"]\').onclick=()=>portalOpenReport(host);'
event = 'host.querySelector(\'[data-portal="map-button"]\').onclick=()=>window.ssMapOpen(host);'

if source.count(end_marker) != 1:
    raise SystemExit("Âncora portalStart ausente ou duplicada.")
if source.count(start_marker) != 1:
    raise SystemExit("Âncora ssMapInstall ausente ou duplicada.")

begin = source.index(start_marker)
end = source.index(end_marker, begin)
old_block = source[begin:end].rstrip()
if not old_block.endswith("})();"):
    raise SystemExit("Limite do componente não reconhecido. Nenhum arquivo alterado.")
source = source[:begin] + full + source[end:]

if new_button not in source:
    if source.count(button_anchor) != 1:
        raise SystemExit("Botão Relatórios não encontrado de forma única.")
    source = source.replace(button_anchor, button_anchor + new_button, 1)
if event not in source:
    if source.count(event_anchor) != 1:
        raise SystemExit("Evento do botão Relatórios não encontrado de forma única.")
    source = source.replace(event_anchor, event_anchor + "\n  " + event, 1)

previous = main.read_text(encoding="utf-8")
if source == previous:
    print("Mapa e melhorias visuais já atualizados.")
    raise SystemExit(0)
ast.parse(source, filename=str(main))
main.write_text(source, encoding="utf-8")
print("Mapa e relatório de cobertura integrados; Python válido.")
