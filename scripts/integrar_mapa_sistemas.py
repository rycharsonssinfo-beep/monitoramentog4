#!/usr/bin/env python3
"""Integra a página do Mapa de Sistemas ao sidebar autenticado do main.py.

Alteração idempotente e com âncora exata: falha sem alterar se layout mudou.
"""
from pathlib import Path
import ast

p = Path(__file__).resolve().parents[1] / "main.py"
original = p.read_text(encoding="utf-8")
target = '''        st.caption(email)
        if st.button("Sair", key="monitor_auth_logout", use_container_width=True):'''
replacement = '''        st.caption(email)
        st.page_link(
            "pages/Mapa_de_Sistemas.py",
            label="🗺️ Mapa de Sistemas",
            icon=":material/map:",
            use_container_width=True,
        )
        if st.button("Sair", key="monitor_auth_logout", use_container_width=True):'''
if replacement in original:
    print("Mapa de Sistemas já integrado; nenhuma alteração.")
    raise SystemExit(0)
if original.count(target) != 1:
    raise SystemExit(f"Não foi possível localizar âncora única do sidebar (ocorrências={original.count(target)}).")
updated = original.replace(target, replacement, 1)
ast.parse(updated, filename=str(p))
p.write_text(updated, encoding="utf-8")
print("Integração de menu aplicada. Sintaxe Python aprovada.")
