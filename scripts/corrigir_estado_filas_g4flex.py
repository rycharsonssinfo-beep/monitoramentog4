#!/usr/bin/env python3
"""Exibe status claro no hover quando nenhum atendente possui filas confirmadas."""
from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
main=root/"main.py"
s=main.read_text(encoding="utf-8")

# Sincroniza tooltip e CSS mantendo o polling original.
import subprocess,sys
subprocess.run([sys.executable,str(root/"scripts"/"integrar_g4flex_indicadores.py")],check=True)
s=main.read_text(encoding="utf-8")

old=":String(agent?.nome||'');"
new=r":'Filas em que está logado:\nFilas ainda não recebidas pelo robô';"
if "Filas ainda não recebidas pelo robô" not in s:
    if s.count(old)!=1:
        raise SystemExit(f"Não foi possível localizar o fallback de filas: {s.count(old)}")
    s=s.replace(old,new,1)
else:
    if s.count("Filas ainda não recebidas pelo robô")!=2:
        raise SystemExit("Marcador de estado pendente duplicado/incorreto.")
ast.parse(s)
assert "g4f-queue-tooltip-waiting" in s
assert "function g4fQueueTooltipInit(host)" in s
assert s.count("setInterval(g4fPoll,3000)")==1
main.write_text(s,encoding="utf-8")
print("OK: hover informa ausência da lista até a captura do robô.")
