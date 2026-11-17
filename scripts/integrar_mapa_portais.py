#!/usr/bin/env python3
"""Sincroniza mapa e melhorias visuais ao main.py sem duplicar a navegação."""
from pathlib import Path
import ast
import json
import base64

root = Path(__file__).resolve().parents[1]
main = root / "main.py"
js = (root / "scripts" / "mapa_sistemas_embed.js").read_text(encoding="utf-8").strip()
extra_js = (root / "scripts" / "mapa_sistemas_enhance.js").read_text(encoding="utf-8").strip()
extra_css = (root / "scripts" / "mapa_sistemas_enhance.css").read_text(encoding="utf-8").strip()
logo_js = (root / "scripts" / "logo_grupo_ss_oficial.js").read_text(encoding="utf-8").strip()
report_js = (root / "scripts" / "mapa_sistemas_report.js").read_text(encoding="utf-8").strip()
ops_js = (root / "scripts" / "mapa_sistemas_operacao.js").read_text(encoding="utf-8").strip()
ops_css = (root / "scripts" / "mapa_sistemas_operacao.css").read_text(encoding="utf-8").strip()
report_css = (root / "scripts" / "mapa_sistemas_report.css").read_text(encoding="utf-8").strip()
icons_css = (root / "scripts" / "mapa_sistemas_icones.css").read_text(encoding="utf-8").strip()
# Usa somente os arquivos oficiais do repositório, embutidos na página.
# Em falha de integridade, interrompe a atualização em vez de exibir ícones genéricos.
image_files = {
    "__SS_MAP_ICON_PORTAIS__": "mapa_portal_contribuinte.webp",
    "__SS_MAP_ICON_FLUXUS__": "mapa_fluxus.webp",
    "__SS_MAP_ICON_VEICULOS__": "mapa_veiculos.webp",
}
for placeholder, filename in image_files.items():
    asset = (root / "scripts" / "assets" / filename).read_bytes()
    if not (asset.startswith(b"RIFF") and asset[8:12] == b"WEBP"):
        raise SystemExit(f"Arquivo de ícone oficial inválido: {filename}")
    if len(asset) < 100 or len(asset) > 200_000:
        raise SystemExit(f"Tamanho inesperado do ícone: {filename}")
    if icons_css.count(placeholder) != 1:
        raise SystemExit(f"Referência do ícone ausente ou duplicada: {placeholder}")
    data_uri = "data:image/webp;base64," + base64.b64encode(asset).decode("ascii")
    icons_css = icons_css.replace(placeholder, data_uri)
if "__SS_MAP_ICON_" in icons_css:
    raise SystemExit("Há ícones oficiais não resolvidos no CSS.")

css_js = (
    '(function(){if(!document.getElementById("ss-map-enhance-v21")){'
    'const tag=document.createElement("style");'
    'tag.id="ss-map-enhance-v21";'
    'tag.textContent=' + json.dumps(extra_css, ensure_ascii=False) + ';'
    'document.head.appendChild(tag);}})();'
)
icons_css_js = (
    '(function(){if(!document.getElementById("ss-map-official-icons")){'
    'const tag=document.createElement("style");'
    'tag.id="ss-map-official-icons";'
    'tag.textContent=' + json.dumps(icons_css, ensure_ascii=False) + ';'
    'document.head.appendChild(tag);}})();'
)
report_css_js = (
    '(function(){if(!document.getElementById("ss-map-report-css")){'
    'const tag=document.createElement("style");'
    'tag.id="ss-map-report-css";'
    'tag.textContent=' + json.dumps(report_css, ensure_ascii=False) + ';'
    'document.head.appendChild(tag);}})();'
)
ops_css_js = (
    '(function(){if(!document.getElementById("ss-map-operations-css")){'
    'const tag=document.createElement("style");'
    'tag.id="ss-map-operations-css";'
    'tag.textContent=' + json.dumps(ops_css, ensure_ascii=False) + ';'
    'document.head.appendChild(tag);}})();'
)
full = js + "\n" + css_js + "\n" + extra_js + "\n" + icons_css_js + "\n" + logo_js + "\n" + report_css_js + "\n" + report_js + "\n" + ops_css_js + "\n" + ops_js
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
print("Mapa, Relatório, Operação, Histórico e Painel Gerencial integrados; Python válido.")
