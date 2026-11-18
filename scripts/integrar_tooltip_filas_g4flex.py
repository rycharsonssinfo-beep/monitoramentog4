#!/usr/bin/env python3
"""Adiciona hover de filas efetivamente logadas aos três modos visuais G4Flex."""
from pathlib import Path
import ast

p=Path(__file__).resolve().parents[1]/"main.py"
s=p.read_text(encoding="utf-8")
def one(old,new,label):
    global s
    if new in s:
        if s.count(new)!=1:raise SystemExit("Marcador novo repetido: "+label)
        return
    if s.count(old)!=1:raise SystemExit("Marcador de "+label+" não encontrado de forma única: "+str(s.count(old)))
    s=s.replace(old,new,1)

# O texto só exibe filas confirmadas no campo filas_logadas. Nunca considera
# fila_exibida, setor ou fila_atendimento_atual como substitutos.
helper="""            // 3.56: filas LOGADAS no G4Flex, diferentes da primeira fila exibida.
            function g4fQueueTitle(agent){
                const raw=Array.isArray(agent?.filas_logadas)?agent.filas_logadas:[];
                const seen=new Set(), queues=[];
                for(const value of raw){
                    const name=String(value||'').trim();
                    const key=name.toLocaleLowerCase('pt-BR');
                    if(name && name.length<=140 && !seen.has(key)){seen.add(key);queues.push(name);}
                }
                return queues.length?'Filas em que está logado:\\n'+queues.join('\\n'):String(agent?.nome||'');
            }
"""
one("            function g4fCard(agent){",helper+"            function g4fCard(agent){","função tooltip")

# O mesmo tooltip no nome de cada apresentação.
one(
' <strong title="${g4fText(agent.nome||\'\')}">${g4fText(agent.nome||\'Sem nome\')}${phoneIcon}</strong>',
' <strong title="${g4fText(g4fQueueTitle(agent))}">${g4fText(agent.nome||\'Sem nome\')}${phoneIcon}</strong>',
"nome do cartão G4Flex")
one(
'<strong title="${g4fText(agent.nome)}">${g4fText(agent.nome||\'Sem nome\')}</strong>',
'<strong title="${g4fText(g4fQueueTitle(agent))}">${g4fText(agent.nome||\'Sem nome\')}</strong>',
"nome dos Cards S&S")
one(
'<strong title="${g4fText(agent.nome||\'Sem nome\')}">${g4fText(agent.nome||\'Sem nome\')}</strong>',
'<strong title="${g4fText(g4fQueueTitle(agent))}">${g4fText(agent.nome||\'Sem nome\')}</strong>',
"nome da Lista S&S")

ast.parse(s,filename=str(p))
if s.count("function g4fQueueTitle(agent)")==1:
    assert s.count("g4fQueueTitle(agent)")>=4
    assert 'Array.isArray(agent?.filas_logadas)' in s
p.write_text(s,encoding="utf-8")
print("OK: ao passar o mouse sobre os nomes, mostra filas logadas quando o robô as fornecer.")
