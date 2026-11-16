#!/usr/bin/env python3
"""Hotfix e integração do Mapa de Sistemas com navegação própria do Monitor."""
from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
p = root / "main.py"
original = p.read_text(encoding="utf-8")

old = '''        st.page_link(
            "pages/Mapa_de_Sistemas.py",
            label="🗺️ Mapa de Sistemas",
            icon=":material/map:",
            use_container_width=True,
        )'''
new = '''        if st.button("🗺️ Mapa de Sistemas", key="ss_abrir_mapa_sistemas", use_container_width=True):
            st.session_state["_ss_mapa_sistemas_aberto"] = not st.session_state.get("_ss_mapa_sistemas_aberto", False)
            st.rerun()'''
if old in original:
    source = original.replace(old, new, 1)
elif new in original:
    source = original
else:
    raise SystemExit("Navegação do mapa não encontrada. Nada foi alterado.")

anchor = '''_render_account_sidebar()'''
inject = '''_render_account_sidebar()
if st.session_state.get("_ss_mapa_sistemas_aberto"):
    import runpy
    _mapa_file = Path(__file__).resolve().parent / "pages" / "Mapa_de_Sistemas.py"
    if _mapa_file.is_file():
        runpy.run_path(str(_mapa_file), run_name="__ss_mapa_sistemas__")
    else:
        st.error("Arquivo do Mapa de Sistemas não encontrado.")
    st.stop()'''
# substituir somente a chamada raiz, nunca a definição de função
if inject not in source:
    token = "\n_render_account_sidebar()\n"
    if source.count(token)!=1:
        raise SystemExit("Âncora principal do pós-login não é única: operação cancelada.")
    source=source.replace(token,"\n"+inject+"\n",1)

if source==original:
    print("Integração já corrigida.")
    raise SystemExit(0)
ast.parse(source, filename=str(p))
p.write_text(source,encoding="utf-8")
print("Correção aplicada: navegação própria, sem st.page_link. AST aprovado.")
