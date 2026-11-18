"""Ajuste visual dos estados do G4Flex (sem alterar regras de monitoramento)."""
from pathlib import Path
import ast

path=Path(__file__).resolve().parents[1]/"main.py"
s=path.read_text(encoding="utf-8")
anchor=".g4f-board.g4f-ss-mode .ss-list-panel .ss-attendants-table tbody tr.is-paused:not(.has-assignment):not(.is-calling){background:#f4f8ff}"
if s.count(anchor)!=1:raise SystemExit(f"Marcador CSS esperado 1 vez; encontrado {s.count(anchor)}")
styles="""
/* G4Flex: estado da linha e do card, com barra lateral junto à foto.
   Prioridade: ligação (roxo) > pausa (amarelo) > atribuição (vermelho). */
.g4f-board.g4f-ss-mode .ss-list-panel .ss-attendants-table tbody tr.is-paused:not(.is-calling){
    background:#fff5df!important;box-shadow:inset 4px 0 #f5aa1c!important;
}
.g4f-board.g4f-ss-mode .ss-list-panel .ss-attendants-table tbody tr.has-assignment:not(.is-paused):not(.is-calling){
    background:#fff0f2!important;box-shadow:inset 4px 0 #ef4261!important;
}
.g4f-board.g4f-ss-mode .ss-list-panel .ss-attendants-table tbody tr.is-calling{
    background:#fbf5ff!important;box-shadow:inset 4px 0 #9b40e0!important;
}
.g4f-board.g4f-ss-mode .ss-agent.ss-paused:not(.ss-calling){
    background:#fff5df!important;box-shadow:inset 4px 0 #f5aa1c!important;
}
.g4f-board.g4f-ss-mode .ss-agent.ss-assigned:not(.ss-paused):not(.ss-calling){
    background:#fff0f2!important;box-shadow:inset 4px 0 #ef4261!important;
}
.g4f-board.g4f-ss-mode .ss-agent.ss-calling{
    background:#fbf5ff!important;box-shadow:inset 4px 0 #9b40e0!important;
}
/* Layout G4Flex original: pausa e atribuição também distinguíveis. */
.g4f-board:not(.g4f-ss-mode) .g4f-agent.paused{
    background:#fff5df!important;box-shadow:inset 4px 0 #f5aa1c!important;
}
.g4f-board:not(.g4f-ss-mode) .g4f-agent.has-assignment:not(.paused){
    background:#fff0f2!important;box-shadow:inset 4px 0 #ef4261!important;
}
"""
if "G4Flex: estado da linha e do card" not in s:
    s=s.replace(anchor,anchor+"\n"+styles,1)
ast.parse(s)
assert s.count("G4Flex: estado da linha e do card")==1
assert "ss-agent.ss-calling" in s and "ss-list-row" in s
path.write_text(s,encoding="utf-8")
print("OK: regras de pausa, atribuição e ligação inseridas em main.py.")
