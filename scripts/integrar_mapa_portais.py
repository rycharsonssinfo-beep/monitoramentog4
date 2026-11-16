#!/usr/bin/env python3
"""Sincroniza Mapa de Sistemas incorporado ao Monitor de Portais, de forma idempotente."""
from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
main = root / "main.py"
js = (root / "scripts" / "mapa_sistemas_embed.js").read_text(encoding="utf-8").strip()
source = main.read_text(encoding="utf-8")

start_marker = "(function ssMapInstall(){"
end_marker = "\nfunction portalStart(host){"
button_anchor = '<button type="button" class="portal-report-trigger" data-portal="report-button">Relatórios</button>'
new_button = '<button type="button" class="ss-map-open" data-portal="map-button">Mapa de Sistemas</button>'
event_anchor = 'host.querySelector(\'[data-portal="report-button"]\').onclick=()=>portalOpenReport(host);'
event = 'host.querySelector(\'[data-portal="map-button"]\').onclick=()=>window.ssMapOpen(host);'

if source.count(end_marker) != 1:
    raise SystemExit("Âncora portalStart ausente ou duplicada; operação cancelada.")
if source.count(start_marker) > 1:
    raise SystemExit("Há múltiplos mapas incorporados; operação cancelada.")

if start_marker in source:
    begin = source.index(start_marker)
    end = source.index(end_marker, begin)
    old_js = source[begin:end].rstrip()
    if not old_js.endswith("})();"):
        raise SystemExit("Limites do mapa não reconhecidos; operação cancelada.")
    source = source[:begin] + js + source[end:]
else:
    source = source.replace(end_marker, "\n" + js + end_marker, 1)

if new_button not in source:
    if source.count(button_anchor) != 1:
        raise SystemExit("Botão Relatórios ausente ou ambíguo; operação cancelada.")
    source = source.replace(button_anchor, button_anchor + new_button, 1)
if event not in source:
    if source.count(event_anchor) != 1:
        raise SystemExit("Evento do relatório ausente ou ambíguo; operação cancelada.")
    source = source.replace(event_anchor, event_anchor + "\n  " + event, 1)

if source == main.read_text(encoding="utf-8"):
    print("Mapa premium já sincronizado; nenhuma alteração necessária.")
    raise SystemExit(0)

ast.parse(source, filename=str(main))
main.write_text(source, encoding="utf-8")
print("Mapa premium integrado com sucesso. Sintaxe Python aprovada.")
