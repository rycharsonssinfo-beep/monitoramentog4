"""Navigation and layout for the configuration workspace."""

import html
import json
from pathlib import Path

import streamlit as st

from config_settings import matches_search


GROUPS = {
    "Monitoramento": (
        ("overview", "Visão geral", "resumo perfil dashboard início"),
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

SECTION_ICONS = {
    "overview": "dashboard",
    "panels": "layers", "profiles": "group", "stability": "monitor_heart", "visual": "desktop_windows",
    "ticker": "sell", "updates": "sync", "agenda": "event", "comunicados": "campaign",
    "integration": "hub", "sim_alert": "notifications", "access": "manage_accounts",
    "backup": "backup", "diagnostics": "monitoring", "releases": "download", "news": "info",
}
GROUP_ICONS = {
    "Monitoramento": "desktop_windows", "Comunicação": "campaign",
    "Integrações e alertas": "hub", "Administração": "admin_panel_settings",
}


def _icon(name):
    return f'<span class="cfg-material-icon" aria-hidden="true">{html.escape(name)}</span>'


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
    query = st.text_input(":material/search: Buscar configuração", placeholder="Ex.: recarregar painel",
                          key="cfg_workspace_search")
    if query.strip():
        matches = [(key, title) for group, items in groups.items() for key, title, terms in items
                   if matches_search(query, f"{group} {title} {terms}")]
        for key, title in matches:
            st.button(title, key=f"cfg_result_{key}", icon=f":material/{SECTION_ICONS[key]}:", use_container_width=True,
                      type="primary" if key == section else "secondary", on_click=_select_section, args=(key,))
        if not matches:
            st.info("Nenhuma configuração encontrada.")
        return

    with st.container(key="cfg_workspace_desktop_nav"):
        for group, items in groups.items():
            group_key = items[0][0]
            with st.container(key=f"cfg_nav_group_{group_key}"):
                st.html(f'<div class="cfg-nav-group" role="heading" aria-level="3">'
                        f'{_icon(GROUP_ICONS[group])}<span>{html.escape(group)}</span></div>')
                for key, title, _ in items:
                    st.button(title, key=f"cfg_link_{key}", icon=f":material/{SECTION_ICONS[key]}:", use_container_width=True,
                              type="primary" if key == section else "secondary", on_click=_select_section, args=(key,))
    with st.container(key="cfg_workspace_mobile_nav"):
        mobile_key = f"cfg_mobile_{section}"

        def change_mobile_section():
            _select_section(st.session_state[mobile_key])

        st.selectbox("Seção", list(sections), index=list(sections).index(section),
                     format_func=sections.get, key=mobile_key, on_change=change_mobile_section)


def _render_overview(panels, sections):
    with st.container(key="cfg_overview_order"):
        heading, action = st.columns([3, 1], vertical_alignment="center")
        with heading:
            st.html(f'<div class="cfg-section-heading"><span class="cfg-title-tile">{_icon("layers")}</span>'
                    '<h2>Ordem de exibição</h2></div>')
        with action:
            st.button("Editar painéis", icon=":material/edit:", key="cfg_overview_edit",
                      use_container_width=True, on_click=_select_section, args=("panels",))
        if panels:
            rows = "".join(
                f'<li><span class="cfg-overview-position">{position}</span>'
                f'<strong>{html.escape(panel["nome"])}</strong>'
                f'<span class="cfg-overview-duration">{html.escape(str(panel["tempo"]))} s</span>'
                '<span class="cfg-overview-active">✓ Ativo</span></li>'
                for position, panel in enumerate(panels, start=1)
            )
            st.html(f'<ol class="cfg-overview-list" aria-label="Sequência dos painéis ativos">{rows}</ol>')
        else:
            st.info("Nenhum painel está pronto para exibição neste perfil.")

    with st.container(key="cfg_overview_shortcuts"):
        st.html(f'<div class="cfg-section-heading"><span class="cfg-title-tile">{_icon("bolt")}</span>'
                '<h2>Acessos rápidos</h2></div>')
        shortcuts = (("profiles", "Perfis"), ("comunicados", "Comunicados"),
                     ("integration", "Integrações"), ("diagnostics", "Diagnóstico"))
        visible = [(key, label) for key, label in shortcuts if key in sections]
        for column, (key, label) in zip(st.columns(len(visible)), visible):
            with column:
                st.button(label, icon=f":material/{SECTION_ICONS[key]}:", key=f"cfg_overview_{key}",
                          use_container_width=True, on_click=_select_section, args=(key,))


def render_workspace(config, profile_id, is_admin, render_section, active_panels, save, start, reload_revision):
    groups = {group: [item for item in items if is_admin or item[0] not in {"access", "comunicados"}]
              for group, items in GROUPS.items()}
    sections = {key: title for items in groups.values() for key, title, _ in items}
    section = st.query_params.get("sec", "overview")
    if section not in sections:
        section = "overview"
    profile = config["profiles"][profile_id]
    css = (Path(__file__).parent / "scripts" / "central_config.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    with st.container(key="cfg_workspace"):
        st.html(
            '<div class="cfg-workspace-header"><img src="app/static/grupo-ss-oficial.png" '
            'alt="Grupo S&S" width="225" height="58">'
            f'<div class="cfg-header-title"><span class="cfg-title-tile">{_icon("settings")}</span>'
            f'<h1>{"Visão geral" if section == "overview" else "Configurações"}</h1></div></div>',
        )
        with st.container(key="cfg_workspace_profile"):
            profile_col, summary_col, launch_col = st.columns([1.45, 1.2, 1.1], vertical_alignment="center")
            with profile_col:
                ids = list(config["profiles"])
                selected = st.selectbox(
                    ":material/person: Perfil de monitoramento" if section == "overview" else ":material/person: Perfil em edição",
                    ids, index=ids.index(profile_id),
                    format_func=lambda pid: config["profiles"][pid]["nome"], key=f"cfg_workspace_profile_{profile_id}",
                )
                if selected != profile_id:
                    st.session_state.pop("cfg_pending_restore", None)
                    st.query_params["perfil"] = selected
                    st.rerun()
            with summary_col, st.container(key="cfg_workspace_summary"):
                summary = st.empty()
                save_status = st.empty()
            with launch_col, st.container(key="cfg_workspace_launch"):
                launch = st.button("Iniciar monitoramento", icon=":material/play_arrow:",
                                   type="primary", use_container_width=True,
                                   disabled=bool(st.session_state.get("config_conflito")))
        conflict_notice = st.empty()

        menu_col, content_col = st.columns([1, 3.15], gap="medium")
        with menu_col, st.container(key="cfg_workspace_nav"):
            _render_nav(groups, sections, section)
        with content_col, st.container(key="cfg_workspace_content"):
            if section == "overview":
                _render_overview(active_panels(profile), sections)
            else:
                scope = ""
                if section in {"panels", "stability", "visual"}:
                    scope = f"Perfil: {profile['nome']}"
                elif section in {"ticker", "updates", "agenda", "integration", "sim_alert", "comunicados", "access"}:
                    scope = "Configuração global"
                scope_html = f'<p class="cfg-section-scope">{html.escape(scope)}</p>' if scope else ""
                st.html(f'<div class="cfg-section-heading"><span class="cfg-title-tile">{_icon(SECTION_ICONS[section])}</span>'
                        f'<div><h2>{html.escape(sections[section])}</h2>{scope_html}</div></div>')
                render_section(section)
        _focus_section(section)

        if launch:
            start()
        default_label = " · Perfil padrão" if profile_id == config.get("default_profile_id") else ""
        summary.html(f'<div class="cfg-profile-count">{_icon("layers")}<span>'
                     f'<strong>{len(active_panels(profile))} de {len(profile["paineis"])} painéis ativos</strong>'
                     f'{default_label}</span></div>')
        error = st.session_state.get("ultimo_erro_persistencia")
        saved_at = st.session_state.get("ultima_gravacao")
        if st.session_state.get("config_conflito"):
            with conflict_notice.container():
                with st.container(key="cfg_revision_actions"):
                    st.markdown(
                        '<div class="cfg-revision-notice" role="alert"><strong>Há uma revisão mais recente.</strong> '
                        'Exporte sua edição antes de carregar a revisão do servidor se quiser preservá-la.</div>',
                        unsafe_allow_html=True,
                    )
                    recover_col, reload_col = st.columns(2)
                    with recover_col:
                        st.download_button("Exportar minha edição", json.dumps(config, ensure_ascii=False, indent=2),
                                           file_name="monitoramento_config_edicao.json", mime="application/json")
                    with reload_col:
                        st.button("Descartar edição e carregar revisão do servidor", on_click=reload_revision)
        elif error:
            save_status.error(error)
            if st.button("Tentar salvar novamente"):
                if save(config, force=True):
                    st.rerun()
        elif saved_at:
            save_status.markdown(f'<span class="cfg-workspace-saved">✓ Salvo às {html.escape(saved_at)}</span>',
                                 unsafe_allow_html=True)
        else:
            save_status.caption("Sem alterações nesta sessão")
