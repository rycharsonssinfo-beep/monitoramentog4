"""Navigation and layout for the configuration workspace."""

import html
import json
from pathlib import Path

import streamlit as st

from config_settings import matches_search


GROUPS = {
    "Monitoramento": (
        ("panels", "Painéis e ordem de exibição", "tv ordem tempo duração iframe reload recarregar f5"),
        ("profiles", "Perfis de monitoramento", "tv padrão criar duplicar renomear"),
        ("stability", "Estabilidade e operação", "desempenho sessão recarregar watchdog f5"),
        ("visual", "Aparência do monitor", "escala relógio barra tema transição g4flex"),
    ),
    "Comunicação": (
        ("ticker", "Faixas corporativas", "ticker rodapé velocidade notícias"),
        ("updates", "Atualizações S&S", "notícias conteúdo prévia portal"),
        ("agenda", "Agenda S&S", "compromisso reunião calendário"),
        ("comunicados", "Central de Comunicados", "aviso publicar áudio cancelar"),
    ),
    "Integrações e alertas": (
        ("integration", "S&S Conecta", "portal integração sincronização manual"),
        ("sim_alert", "Alerta de Nova Entrega SIM", "entrega tce api áudio som"),
    ),
    "Administração": (
        ("access", "Usuários e permissões", "conta criar senha aprovar acesso"),
        ("backup", "Backup e restauração", "importar exportar restaurar json revisão"),
        ("diagnostics", "Diagnóstico", "rede ip configuração iframe erro"),
        ("releases", "Downloads e atualizações", "instalador windows versão robô"),
        ("news", "Sobre e novidades", "versão histórico changelog"),
    ),
}


def _select_section(key):
    st.query_params["sec"] = key
    st.session_state["cfg_focus_section"] = key


def _focus_section(section):
    if st.session_state.pop("cfg_focus_section", None) != section:
        return
    focus = st.components.v2.component(
        "cfg_workspace_focus", html='<span hidden></span>', css=":host{display:none!important}",
        js="""
        export default function({parentElement}) {
          const frame = requestAnimationFrame(() => {
            const heading = parentElement.ownerDocument.querySelector('.st-key-cfg_workspace_content h2');
            if (heading) {
              heading.tabIndex = -1;
              heading.focus();
            }
          });
          return () => cancelAnimationFrame(frame);
        }
        """,
    )
    focus(key=f"cfg_focus_{section}")


def _render_nav(groups, sections, section):
    query = st.text_input("Buscar configuração", placeholder="Ex.: recarregar painel", key="cfg_workspace_search")
    if query.strip():
        matches = [(key, title) for group, items in groups.items() for key, title, terms in items
                   if matches_search(query, f"{group} {title} {terms}")]
        for key, title in matches:
            st.button(title, key=f"cfg_result_{key}", use_container_width=True,
                      type="primary" if key == section else "secondary", on_click=_select_section, args=(key,))
        if not matches:
            st.info("Nenhuma configuração encontrada.")
        return

    with st.container(key="cfg_workspace_desktop_nav"):
        for group, items in groups.items():
            st.markdown(f"**{group}**")
            for key, title, _ in items:
                st.button(title, key=f"cfg_link_{key}", use_container_width=True,
                          type="primary" if key == section else "secondary", on_click=_select_section, args=(key,))
    with st.container(key="cfg_workspace_mobile_nav"):
        mobile_key = f"cfg_mobile_{section}"

        def change_mobile_section():
            _select_section(st.session_state[mobile_key])

        st.selectbox("Seção", list(sections), index=list(sections).index(section),
                     format_func=sections.get, key=mobile_key, on_change=change_mobile_section)


def render_workspace(config, profile_id, is_admin, render_section, active_panels, save, start, reload_revision):
    groups = {group: [item for item in items if is_admin or item[0] not in {"access", "comunicados"}]
              for group, items in GROUPS.items()}
    sections = {key: title for items in groups.values() for key, title, _ in items}
    section = st.query_params.get("sec", "panels")
    if section not in sections:
        section = "panels"
    profile = config["profiles"][profile_id]
    css = (Path(__file__).parent / "scripts" / "central_config.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    with st.container(key="cfg_workspace"):
        st.markdown(
            '<div class="cfg-workspace-header"><img src="app/static/grupo-ss-oficial.png" '
            'alt="Grupo S&S" width="182"><h1>Configurações</h1></div>',
            unsafe_allow_html=True,
        )
        with st.container(key="cfg_workspace_profile"):
            profile_col, summary_col, launch_col = st.columns([1.45, 1.2, 1.1], vertical_alignment="center")
            with profile_col:
                ids = list(config["profiles"])
                selected = st.selectbox(
                    "Perfil em edição", ids, index=ids.index(profile_id),
                    format_func=lambda pid: config["profiles"][pid]["nome"], key=f"cfg_workspace_profile_{profile_id}",
                )
                if selected != profile_id:
                    st.session_state.pop("cfg_pending_restore", None)
                    st.query_params["perfil"] = selected
                    st.rerun()
            with summary_col:
                summary = st.empty()
                save_status = st.empty()
            with launch_col, st.container(key="cfg_workspace_launch"):
                launch = st.button("Iniciar monitoramento", icon=":material/play_arrow:",
                                   type="primary", use_container_width=True)
        if st.session_state.get("config_conflito"):
            st.warning("Há uma revisão mais recente no servidor. Exporte esta edição antes de recarregar, se quiser preservá-la.")
            recover_col, reload_col = st.columns(2)
            with recover_col:
                st.download_button("Exportar minha edição", json.dumps(config, ensure_ascii=False, indent=2),
                                   file_name="monitoramento_config_edicao.json", mime="application/json")
            with reload_col:
                st.button("Descartar edição e carregar revisão do servidor", on_click=reload_revision)

        menu_col, content_col = st.columns([1, 3.15], gap="medium")
        with menu_col, st.container(key="cfg_workspace_nav"):
            _render_nav(groups, sections, section)
        with content_col, st.container(key="cfg_workspace_content"):
            st.header(sections[section], anchor=False)
            if section in {"panels", "stability", "visual"}:
                st.caption(f"Perfil: {profile['nome']}")
            elif section in {"ticker", "updates", "agenda", "integration", "sim_alert", "comunicados", "access"}:
                st.caption("Configuração global")
            render_section(section)
        _focus_section(section)

        default_label = " · Perfil padrão" if profile_id == config.get("default_profile_id") else ""
        summary.markdown(f"**{len(active_panels(profile))} de {len(profile['paineis'])} painéis ativos**{default_label}")
        error = st.session_state.get("ultimo_erro_persistencia")
        saved_at = st.session_state.get("ultima_gravacao")
        if error:
            save_status.error(error)
            if not st.session_state.get("config_conflito") and st.button("Tentar salvar novamente"):
                if save(config, force=True):
                    st.rerun()
        elif saved_at:
            save_status.markdown(f'<span class="cfg-workspace-saved">✓ Salvo às {html.escape(saved_at)}</span>',
                                 unsafe_allow_html=True)
        else:
            save_status.caption("Sem alterações nesta sessão")
        if launch:
            start()
