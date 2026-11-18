#!/usr/bin/env python3
"""Vincula o mascote de recuperação ao alerta dos Portais sem alterar as regras de queda."""
from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
main=root/"main.py"
source=main.read_text(encoding="utf-8")
asset=root/"assets"/"mascote_retorno.png"

# A imagem só é utilizada quando está presente. Evita erro 404 no navegador.
# A URI data é construída em Python durante a montagem do painel.
anchor="mascot:settings.mascotAlert||'__MASCOTE_COMUNICADO_DATA_URI__',"
replacement="mascot:settings.mascotAlert||'__MASCOTE_COMUNICADO_DATA_URI__',recoveryMascot:'__MASCOTE_RETORNO_DATA_URI__',"
if replacement not in source:
    if source.count(anchor)!=1:raise SystemExit("Inicialização dos alertas não localizada de forma única.")
    source=source.replace(anchor,replacement,1)

# No HTML final, o token de recuperação é substituído por PNG incorporado.
# Fallback mantém a imagem atual quando o PNG não estiver disponível.
anchor2='    html_painel = html_painel.replace("__PAYLOAD_B64__", payload_b64)'
inject='''    _retorno_png = Path(__file__).with_name("assets") / "mascote_retorno.png"
    if _retorno_png.is_file():
        import base64 as _retorno_b64
        _retorno_uri = "data:image/png;base64," + _retorno_b64.b64encode(_retorno_png.read_bytes()).decode("ascii")
    else:
        _retorno_uri = ""
    html_painel = html_painel.replace("__MASCOTE_RETORNO_DATA_URI__", _retorno_uri)
'''
if inject not in source:
    if source.count(anchor2)!=1:raise SystemExit("Ponto de montagem do HTML não encontrado de forma única.")
    source=source.replace(anchor2,inject+anchor2,1)
ast.parse(source)
main.write_text(source,encoding="utf-8")
print("Integração da imagem de retorno concluída. PNG presente:",asset.is_file())
