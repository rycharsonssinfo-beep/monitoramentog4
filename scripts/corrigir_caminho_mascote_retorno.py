from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
main=root/"main.py"
asset=root/"scripts"/"assets"/"mascote_retorno.png"
if not asset.is_file() or asset.stat().st_size<1000:
    raise SystemExit("PNG não localizado em scripts/assets/mascote_retorno.png")
data=asset.read_bytes()
if not data.startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("Arquivo não é um PNG válido")

s=main.read_text(encoding="utf-8")
old='Path(__file__).with_name("assets") / "mascote_retorno.png"'
new='Path(__file__).with_name("scripts") / "assets" / "mascote_retorno.png"'
if old in s:
    if s.count(old)!=1:raise SystemExit("Caminho anterior duplicado")
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit("Código de recuperação não localizado em main.py")
if "recoveryMascot:'__MASCOTE_RETORNO_DATA_URI__'" not in s:
    raise SystemExit("O parâmetro recoveryMascot não está configurado")
if 'html_painel.replace("__MASCOTE_RETORNO_DATA_URI__", _retorno_uri)' not in s:
    raise SystemExit("O PNG não está sendo incorporado ao HTML")
ast.parse(s,filename="main.py")
main.write_text(s,encoding="utf-8")
print("OK: mascote de recuperação encontrado e caminho integrado:",asset.relative_to(root))
