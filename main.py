import copy
import json
import uuid
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# Painel de Monitoramento 2.1
# =========================================================

st.set_page_config(
    page_title="Painel de Monitoramento 2.1",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CONFIG_PATH = Path.cwd() / "monitoramento_config.json"
CONFIG_VERSION = 2


def novo_id():
    return uuid.uuid4().hex[:12]


def painel_padrao(nome, link, tempo, recarregar=True, ativo=True):
    return {
        "id": novo_id(),
        "nome": nome,
        "link": link,
        "tempo": tempo,
        "recarregar": recarregar,
        "ativo": ativo,
    }


DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,
    "active_profile": "Suporte",
    "profiles": {
        "Suporte": {
            "paineis": [
                painel_padrao(
                    "Fila de Voz / Zoiper",
                    "https://ssinformatica.g4flex.com.br:9090/monitoring/queues",
                    25,
                    True,
                ),
                painel_padrao(
                    "Grade de Filas Chat",
                    "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues",
                    25,
                    True,
                ),
                painel_padrao(
                    "Monitoramento SIM",
                    "https://consultatce-dev.ssinformatica.net/sim-submissions",
                    50,
                    True,
                ),
            ],
            "horas_reload_geral": 0,
            "auto_ocultar_controles": True,
            "modo_tv_padrao": False,
            "sim_refresh_seconds": 20,
        }
    },
}


def normalizar_config(data):
    """Aceita o formato 2.0 e corrige campos ausentes sem apagar dados."""
    if not isinstance(data, dict):
        return copy.deepcopy(DEFAULT_CONFIG)

    if "profiles" not in data or not isinstance(data.get("profiles"), dict) or not data["profiles"]:
        return copy.deepcopy(DEFAULT_CONFIG)

    data.setdefault("version", CONFIG_VERSION)
    if data.get("active_profile") not in data["profiles"]:
        data["active_profile"] = next(iter(data["profiles"]))

    for nome_perfil, perfil in list(data["profiles"].items()):
        if not isinstance(perfil, dict):
            data["profiles"][nome_perfil] = copy.deepcopy(DEFAULT_CONFIG["profiles"]["Suporte"])
            perfil = data["profiles"][nome_perfil]

        perfil.setdefault("paineis", [])
        perfil.setdefault("horas_reload_geral", 0)
        perfil.setdefault("auto_ocultar_controles", True)
        perfil.setdefault("modo_tv_padrao", False)
        perfil.setdefault("sim_refresh_seconds", 20)
        horas_validas = [0, 1, 2, 4, 6, 8, 12, 24]
        try:
            horas = int(perfil.get("horas_reload_geral", 0))
        except Exception:
            horas = 0
        perfil["horas_reload_geral"] = horas if horas in horas_validas else 0
        try:
            perfil["sim_refresh_seconds"] = max(0, min(300, int(perfil.get("sim_refresh_seconds", 20))))
        except Exception:
            perfil["sim_refresh_seconds"] = 20

        paineis_normalizados = []
        for p in perfil["paineis"]:
            if not isinstance(p, dict):
                continue
            paineis_normalizados.append(
                {
                    "id": str(p.get("id") or novo_id()),
                    "nome": str(p.get("nome") or "Novo Painel"),
                    "link": str(p.get("link") or ""),
                    "tempo": max(5, min(600, int(p.get("tempo") or 20))),
                    "recarregar": bool(p.get("recarregar", True)),
                    "ativo": bool(p.get("ativo", True)),
                }
            )
        perfil["paineis"] = paineis_normalizados

    return data


def carregar_config():
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                return normalizar_config(json.load(f))
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_CONFIG)


def salvar_config(config):
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as exc:
        st.session_state["ultimo_erro_persistencia"] = str(exc)
        return False


def url_valida(url):
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def perfil_ativo(config):
    return config["profiles"][config["active_profile"]]


def regenerar_ids(perfil):
    novo = copy.deepcopy(perfil)
    for p in novo.get("paineis", []):
        p["id"] = novo_id()
    return novo


if "config_v2" not in st.session_state:
    st.session_state.config_v2 = carregar_config()

config = st.session_state.config_v2

# Sincroniza estado de apresentação pela URL.
query_iniciado = str(st.query_params.get("iniciado", "false")).lower() == "true"
if "iniciado" not in st.session_state:
    st.session_state.iniciado = query_iniciado

# =========================================================
# CSS - configuração | Pacote Visual 2.1
# Cor principal: Azul-escuro / azul petróleo #0E5285
# =========================================================
st.markdown(
    """
    <style>
        :root {
            --primary: #0E5285;
            --primary-dark: #0A3E66;
            --primary-hover: #0B466F;
            --primary-soft: #EAF3FA;
            --primary-soft-2: #F4F8FC;
            --primary-border: #C9D9E6;
            --text-main: #17324D;
            --text-muted: #64748B;
        }

        header {visibility: hidden !important; height: 0 !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}

        .stApp {
            background: #F4F7FB;
            color: var(--text-main);
        }
        .block-container {
            max-width: 1220px;
            padding-top: 22px !important;
            padding-bottom: 44px !important;
        }
        h1, h2, h3, h4, label { color: var(--primary) !important; }

        .app-title {
            font-size: 30px;
            line-height: 1.15;
            font-weight: 780;
            color: var(--primary);
            margin: 2px 0 4px 0;
            letter-spacing: -0.5px;
        }
        .app-subtitle {
            color: var(--text-muted);
            font-size: 14px;
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 16px;
            font-weight: 760;
            color: var(--primary);
            margin: 0;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 12px 0 18px 0;
        }
        .summary-card {
            background: #FFFFFF;
            border: 1px solid var(--primary-border);
            border-radius: 12px;
            padding: 13px 15px;
            box-shadow: 0 1px 3px rgba(14, 82, 133, .06);
        }
        .summary-label {
            color: var(--text-muted);
            font-size: 11px;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: .35px;
        }
        .summary-value {
            color: var(--primary);
            font-size: 21px;
            font-weight: 800;
            margin-top: 2px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--primary-border) !important;
            border-radius: 12px !important;
            background: #FFFFFF !important;
            box-shadow: 0 1px 3px rgba(14, 82, 133, .045);
        }

        .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border-color: #D7E2EB !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 1px var(--primary) !important;
        }

        .stButton button, .stDownloadButton button {
            border-radius: 8px !important;
            font-weight: 650 !important;
            min-height: 38px;
        }
        .stButton button[kind="primary"] {
            background-color: var(--primary) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--primary) !important;
        }
        .stButton button[kind="primary"]:hover {
            background-color: var(--primary-hover) !important;
            border-color: var(--primary-hover) !important;
        }
        .stButton button:not([kind="primary"]):hover,
        .stDownloadButton button:hover {
            color: var(--primary) !important;
            border-color: var(--primary) !important;
            background: var(--primary-soft-2) !important;
        }

        /* Streamlit toggle: azul quando ligado, cinza quando desligado. */
        div[data-testid="stToggle"] input[role="switch"]:checked + div,
        div[data-testid="stToggle"] input:checked + div,
        div[data-testid="stToggle"] [role="switch"][aria-checked="true"] {
            background-color: var(--primary) !important;
            border-color: var(--primary) !important;
        }
        div[data-testid="stToggle"] input[role="switch"]:not(:checked) + div,
        div[data-testid="stToggle"] input:not(:checked) + div,
        div[data-testid="stToggle"] [role="switch"][aria-checked="false"] {
            background-color: #94A3B8 !important;
            border-color: #94A3B8 !important;
        }
        div[data-testid="stToggle"] label p {
            color: var(--primary) !important;
            font-weight: 650 !important;
        }

        div[data-testid="stExpander"] details {
            border-color: var(--primary-border) !important;
            border-radius: 10px !important;
            background: #FFFFFF !important;
        }
        div[data-testid="stExpander"] summary:hover {
            color: var(--primary) !important;
        }

        .status-ok { color: #047857; font-size: 12px; font-weight: 680; }
        .status-warn { color: #B45309; font-size: 12px; font-weight: 680; }
        .muted { color: var(--text-muted); font-size: 12px; }
        .f5-pill-on, .f5-pill-off {
            display: inline-block;
            margin-top: -3px;
            padding: 2px 7px;
            border-radius: 999px;
            font-size: 10px;
            line-height: 1.25;
            font-weight: 800;
            letter-spacing: .25px;
        }
        .f5-pill-on {
            color: var(--primary);
            background: var(--primary-soft);
            border: 1px solid #B8D2E5;
        }
        .f5-pill-off {
            color: #5B6573;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
        }
        .url-status-wrap {
            padding-top: 30px;
            min-height: 55px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            white-space: nowrap;
        }
        .palette-note {
            color: var(--text-muted);
            font-size: 11px;
        }

        @media (max-width: 900px) {
            .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .block-container { padding-left: 12px !important; padding-right: 12px !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TELA 1 - CONFIGURAÇÃO 2.1
# =========================================================
if not st.session_state.iniciado:
    top_left, top_right = st.columns([1.65, 1])
    with top_left:
        st.image("https://www.ssinformatica.net/wp-content/uploads/2023/03/Grupo-SS.png", width=250)
        st.markdown('<div class="app-title">Painel de Monitoramento</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="app-subtitle">Configure a rotação, o comportamento de atualização e os perfis de monitoramento.</div>',
            unsafe_allow_html=True,
        )

    perfil = perfil_ativo(config)
    paineis = perfil["paineis"]
    ativos = [p for p in paineis if p.get("ativo", True) and p.get("link", "").strip()]
    tempo_total = sum(int(p.get("tempo", 0)) for p in ativos)
    min_total, seg_total = divmod(tempo_total, 60)
    tempo_total_fmt = f"{min_total}m {seg_total:02d}s" if min_total else f"{seg_total}s"
    urls_invalidas = sum(1 for p in ativos if not url_valida(p.get("link", "")))

    with top_right:
        st.markdown("<div style='height: 42px'></div>", unsafe_allow_html=True)
        perfis = list(config["profiles"].keys())
        perfil_escolhido = st.selectbox(
            "Perfil de monitoramento",
            perfis,
            index=perfis.index(config["active_profile"]),
            key="perfil_select_v2",
        )
        if perfil_escolhido != config["active_profile"]:
            config["active_profile"] = perfil_escolhido
            salvar_config(config)
            st.rerun()

    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-card"><div class="summary-label">Painéis cadastrados</div><div class="summary-value">{len(paineis)}</div></div>
            <div class="summary-card"><div class="summary-label">Painéis ativos</div><div class="summary-value">{len(ativos)}</div></div>
            <div class="summary-card"><div class="summary-label">Tempo do ciclo</div><div class="summary-value">{tempo_total_fmt}</div></div>
            <div class="summary-card"><div class="summary-label">URLs inválidas</div><div class="summary-value">{urls_invalidas}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- Perfis ----------------
    with st.expander("Perfis de monitoramento", expanded=False):
        c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
        with c1:
            nome_novo_perfil = st.text_input(
                "Nome do novo perfil",
                placeholder="Ex.: Coordenação, eSocial, SAT...",
                key="novo_perfil_nome_v2",
            )
        with c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Criar perfil", use_container_width=True, key="criar_perfil_v2"):
                nome = nome_novo_perfil.strip()
                if not nome:
                    st.warning("Informe um nome para o perfil.")
                elif nome in config["profiles"]:
                    st.warning("Já existe um perfil com esse nome.")
                else:
                    config["profiles"][nome] = {
                        "paineis": [],
                        "horas_reload_geral": 0,
                        "auto_ocultar_controles": True,
                        "modo_tv_padrao": False,
                        "sim_refresh_seconds": 20,
                    }
                    config["active_profile"] = nome
                    salvar_config(config)
                    st.rerun()

        with c3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Duplicar perfil", use_container_width=True, key="duplicar_perfil_v2"):
                base = config["active_profile"]
                i = 2
                novo_nome = f"{base} - Cópia"
                while novo_nome in config["profiles"]:
                    novo_nome = f"{base} - Cópia {i}"
                    i += 1
                config["profiles"][novo_nome] = regenerar_ids(config["profiles"][base])
                config["active_profile"] = novo_nome
                salvar_config(config)
                st.rerun()

        with c4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Excluir perfil", use_container_width=True, key="pedir_excluir_perfil_v2", disabled=len(config["profiles"]) <= 1):
                st.session_state.confirmar_exclusao_perfil = True

        if st.session_state.get("confirmar_exclusao_perfil"):
            st.warning(f"Excluir o perfil **{config['active_profile']}** e todos os painéis dele?")
            x1, x2 = st.columns(2)
            with x1:
                if st.button("Cancelar", use_container_width=True, key="cancelar_excluir_perfil_v2"):
                    st.session_state.confirmar_exclusao_perfil = False
                    st.rerun()
            with x2:
                if st.button("Confirmar exclusão", type="primary", use_container_width=True, key="confirmar_excluir_perfil_v2"):
                    alvo = config["active_profile"]
                    del config["profiles"][alvo]
                    config["active_profile"] = next(iter(config["profiles"]))
                    st.session_state.confirmar_exclusao_perfil = False
                    salvar_config(config)
                    st.rerun()

    # ---------------- Painéis ----------------
    header_l, header_r = st.columns([4, 1])
    with header_l:
        st.markdown('<div class="section-title">Painéis e ordem de exibição</div>', unsafe_allow_html=True)
        st.caption("Use ↑ e ↓ para reorganizar. Painéis desativados permanecem salvos, mas não entram na apresentação.")
    with header_r:
        if st.button("＋ Adicionar painel", use_container_width=True, key="add_painel_v2"):
            paineis.append(
                {
                    "id": novo_id(),
                    "nome": f"Novo Painel {len(paineis) + 1}",
                    "link": "",
                    "tempo": 20,
                    "recarregar": True,
                    "ativo": True,
                }
            )
            salvar_config(config)
            st.rerun()

    pending_delete = st.session_state.get("painel_pendente_exclusao")

    for i, painel in enumerate(paineis):
        pid = painel["id"]
        with st.container(border=True):
            # Linha principal mais compacta e com colunas dimensionadas para evitar cortes.
            row_top = st.columns([0.52, 0.52, 0.95, 3.65, 0.9, 1.45, 1.0, 0.95])

            with row_top[0]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("▲", key=f"up_{pid}", help="Mover painel para cima", disabled=i == 0, use_container_width=True):
                    paineis[i - 1], paineis[i] = paineis[i], paineis[i - 1]
                    salvar_config(config)
                    st.rerun()

            with row_top[1]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("▼", key=f"down_{pid}", help="Mover painel para baixo", disabled=i == len(paineis) - 1, use_container_width=True):
                    paineis[i + 1], paineis[i] = paineis[i], paineis[i + 1]
                    salvar_config(config)
                    st.rerun()

            with row_top[2]:
                painel["ativo"] = st.toggle("Ativo", value=bool(painel.get("ativo", True)), key=f"ativo_{pid}")

            with row_top[3]:
                painel["nome"] = st.text_input("Nome do painel", value=painel["nome"], key=f"nome_{pid}")

            with row_top[4]:
                painel["tempo"] = st.number_input(
                    "Tempo (s)",
                    min_value=5,
                    max_value=600,
                    value=int(painel.get("tempo", 20)),
                    step=5,
                    key=f"tempo_{pid}",
                )

            with row_top[5]:
                painel["recarregar"] = st.toggle(
                    "F5 automático",
                    value=bool(painel.get("recarregar", True)),
                    key=f"reload_{pid}",
                    help="ON: permite recarregamento automático. OFF: preserva a página e impede o F5 automático neste painel.",
                )
                classe_f5 = "f5-pill-on" if painel["recarregar"] else "f5-pill-off"
                texto_f5 = "F5 ON" if painel["recarregar"] else "F5 OFF"
                st.markdown(f'<span class="{classe_f5}">{texto_f5}</span>', unsafe_allow_html=True)

            with row_top[6]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Duplicar", key=f"dup_{pid}", use_container_width=True, help="Duplicar este painel"):
                    clone = copy.deepcopy(painel)
                    clone["id"] = novo_id()
                    clone["nome"] = f"{clone['nome']} - Cópia"
                    paineis.insert(i + 1, clone)
                    salvar_config(config)
                    st.rerun()

            with row_top[7]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Excluir", key=f"del_{pid}", use_container_width=True, help="Excluir este painel"):
                    st.session_state.painel_pendente_exclusao = pid
                    st.rerun()

            # URL + validação na mesma linha para reduzir a altura do card.
            url_col, status_col = st.columns([6.8, 1.35])
            with url_col:
                painel["link"] = st.text_input(
                    "URL da página",
                    value=painel["link"],
                    key=f"link_{pid}",
                    placeholder="https://...",
                )
            with status_col:
                st.markdown('<div class="url-status-wrap">', unsafe_allow_html=True)
                if painel["link"].strip():
                    if url_valida(painel["link"]):
                        st.markdown('<span class="status-ok">✓ URL válida</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-warn">⚠ URL inválida</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="muted">URL pendente</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if pending_delete == pid:
                st.warning(f"Excluir o painel **{painel['nome']}**?")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("Cancelar exclusão", key=f"cancel_del_{pid}", use_container_width=True):
                        st.session_state.painel_pendente_exclusao = None
                        st.rerun()
                with d2:
                    if st.button("Confirmar exclusão", key=f"confirm_del_{pid}", type="primary", use_container_width=True):
                        perfil["paineis"] = [p for p in paineis if p["id"] != pid]
                        st.session_state.painel_pendente_exclusao = None
                        salvar_config(config)
                        st.rerun()

    # Persistência automática das alterações de widgets.
    salvar_config(config)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ---------------- Estabilidade / desempenho ----------------
    with st.container(border=True):
        st.markdown('<div class="section-title">Estabilidade e desempenho</div>', unsafe_allow_html=True)
        st.caption("Opções voltadas a uso contínuo em TV/monitor e à redução de consumo de memória.")

        s1, s2, s3, s4 = st.columns([1.4, 1.1, 1.1, 1.1])
        with s1:
            perfil["horas_reload_geral"] = st.selectbox(
                "Reinício completo da aplicação",
                options=[0, 1, 2, 4, 6, 8, 12, 24],
                index=[0, 1, 2, 4, 6, 8, 12, 24].index(int(perfil.get("horas_reload_geral", 0))),
                format_func=lambda x: "Desativado" if x == 0 else ("A cada 1 hora" if x == 1 else f"A cada {x} horas"),
                key=f"reload_geral_{config['active_profile']}",
            )
        with s2:
            perfil["auto_ocultar_controles"] = st.toggle(
                "Ocultar controles automaticamente",
                value=bool(perfil.get("auto_ocultar_controles", True)),
                key=f"autohide_{config['active_profile']}",
            )
        with s3:
            perfil["modo_tv_padrao"] = st.toggle(
                "Iniciar em Modo TV",
                value=bool(perfil.get("modo_tv_padrao", False)),
                key=f"kiosk_{config['active_profile']}",
            )
        with s4:
            perfil["sim_refresh_seconds"] = st.number_input(
                "F5 técnico do SIM (s)",
                min_value=0,
                max_value=300,
                value=int(perfil.get("sim_refresh_seconds", 20)),
                step=5,
                key=f"sim_refresh_{config['active_profile']}",
                help="0 desativa. Quando o painel atual for o SIM e F5 automático estiver ON, ele recarrega a URL nesse intervalo.",
            )

        st.caption(
            "O modo 2.1 mantém apenas o painel atual, o próximo painel pré-carregado e os painéis com F5 automático em OFF. "
            "Isso reduz o número de iframes simultâneos sem quebrar a função de preservar uma página escolhida sem F5."
        )

    salvar_config(config)

    # ---------------- Backup / importação / diagnóstico ----------------
    with st.expander("Backup, importação e diagnóstico", expanded=False):
        b1, b2 = st.columns(2)
        with b1:
            st.download_button(
                "Exportar configuração (.json)",
                data=json.dumps(config, ensure_ascii=False, indent=2),
                file_name="monitoramento_config_v2_1.json",
                mime="application/json",
                use_container_width=True,
            )
        with b2:
            arquivo_importado = st.file_uploader("Importar configuração", type=["json"], key="import_config_v2")
            if arquivo_importado is not None and st.button("Aplicar configuração importada", use_container_width=True, key="aplicar_import_v2"):
                try:
                    dados = json.loads(arquivo_importado.getvalue().decode("utf-8"))
                    novo_config = normalizar_config(dados)
                    st.session_state.config_v2 = novo_config
                    salvar_config(novo_config)
                    st.success("Configuração importada.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não foi possível importar o JSON: {exc}")

        st.markdown("**Diagnóstico atual**")
        st.write(f"Perfil ativo: `{config['active_profile']}`")
        st.write(f"Painéis ativos com URL: `{len(ativos)}`")
        st.write(f"URLs inválidas: `{urls_invalidas}`")
        st.write(f"Arquivo de persistência: `{CONFIG_PATH.name}`")
        st.write("Arquitetura de exibição: `iframe atual + próximo pré-carregado + preservados com F5 OFF`")
        st.info(
            "Páginas externas podem bloquear exibição em iframe por X-Frame-Options ou Content-Security-Policy. "
            "A aplicação não consegue contornar essa restrição do navegador."
        )
        if st.session_state.get("ultimo_erro_persistencia"):
            st.error(f"Último erro ao salvar configuração: {st.session_state['ultimo_erro_persistencia']}")

    # ---------------- Iniciar ----------------
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    urls_invalidas_lista = [p for p in ativos if not url_valida(p.get("link", ""))]

    if st.button("Iniciar monitoramento", type="primary", use_container_width=True, key="iniciar_v2"):
        if not ativos:
            st.error("Ative e configure pelo menos um painel com URL.")
        elif urls_invalidas_lista:
            st.error("Corrija as URLs inválidas antes de iniciar o monitoramento.")
        else:
            salvar_config(config)
            st.session_state.iniciado = True
            st.query_params["iniciado"] = "true"
            st.rerun()


# =========================================================
# TELA 2 - APRESENTAÇÃO 2.1
# =========================================================
else:
    # A apresentação ocupa toda a área útil do navegador.
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 100% !important;
                width: 100% !important;
                height: 100vh !important;
                padding: 0 !important;
                margin: 0 !important;
                overflow: hidden !important;
            }
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
                overflow: hidden !important;
                height: 100vh !important;
            }
            iframe[title="streamlit.components.v1.html"] {
                width: 100% !important;
                height: 100vh !important;
                display: block !important;
                border: 0 !important;
            }
            div[data-testid="stElementContainer"] { margin: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    perfil_nome = config["active_profile"]
    perfil = perfil_ativo(config)
    paineis_ativos = [
        p for p in perfil["paineis"]
        if p.get("ativo", True) and p.get("link", "").strip() and url_valida(p.get("link", ""))
    ]

    if not paineis_ativos:
        st.session_state.iniciado = False
        st.query_params["iniciado"] = "false"
        st.warning("Não há painéis ativos com URL válida.")
        if st.button("Voltar para configurações"):
            st.rerun()
        st.stop()

    paineis_json = json.dumps(paineis_ativos, ensure_ascii=False)
    perfil_json = json.dumps(perfil_nome, ensure_ascii=False)
    intervalo_limpeza_ms = int(perfil.get("horas_reload_geral", 0)) * 3600 * 1000
    auto_hide = "true" if perfil.get("auto_ocultar_controles", True) else "false"
    kiosk_default = "true" if perfil.get("modo_tv_padrao", False) else "false"
    sim_refresh_seconds = int(perfil.get("sim_refresh_seconds", 20))

    html_painel = r"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            :root {
                --azul: #0E5285;
                --azul-escuro: #0A3E66;
                --azul-claro: #4D9BD3;
                --texto-claro: #EAF3FA;
                --toolbar-h: 40px;
                --progress-h: 3px;
            }
            * { box-sizing: border-box; }
            html, body {
                width: 100%;
                height: 100%;
                margin: 0;
                overflow: hidden;
                background: #fff;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            }
            #control-shell {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                z-index: 10000;
                transition: transform .18s ease, opacity .18s ease;
            }
            #control-shell.hidden {
                transform: translateY(calc(-1 * (var(--toolbar-h) + var(--progress-h))));
                opacity: 0;
                pointer-events: none;
            }
            #toolbar {
                height: var(--toolbar-h);
                background: var(--azul);
                color: #fff;
                display: grid;
                grid-template-columns: minmax(220px, 1.2fr) minmax(120px, .8fr) auto;
                align-items: center;
                gap: 12px;
                padding: 0 10px 0 14px;
                box-shadow: 0 2px 7px rgba(0,0,0,.18);
            }
            .toolbar-left {
                min-width: 0;
                display: flex;
                align-items: center;
                gap: 8px;
                overflow: hidden;
                white-space: nowrap;
            }
            #panel-name {
                overflow: hidden;
                text-overflow: ellipsis;
                font-weight: 760;
                font-size: 12px;
            }
            #panel-order {
                color: #C7DFF2;
                font-size: 11px;
                flex-shrink: 0;
            }
            .toolbar-center {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                font-size: 11px;
                color: var(--texto-claro);
            }
            #dots { display: flex; gap: 5px; align-items: center; }
            .dot {
                width: 7px;
                height: 7px;
                border-radius: 50%;
                border: 1px solid rgba(255,255,255,.65);
                background: transparent;
                opacity: .8;
            }
            .dot.active { background: #fff; opacity: 1; }
            .toolbar-right {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 4px;
            }
            .btn {
                height: 28px;
                min-width: 30px;
                padding: 0 8px;
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,.22);
                background: rgba(255,255,255,.08);
                color: #fff;
                cursor: pointer;
                font-size: 11px;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
                user-select: none;
            }
            .btn:hover { background: rgba(255,255,255,.18); }
            .btn.active-good { background: #1B6FA8; border-color: #8CC4E8; }
            .btn.active-bad { background: #7f1d1d; border-color: #f87171; }
            #clock {
                min-width: 55px;
                text-align: right;
                font-size: 11px;
                font-weight: 700;
                color: #DCEEFF;
                margin-left: 3px;
            }
            #progress-container {
                width: 100%;
                height: var(--progress-h);
                background: var(--azul-escuro);
                overflow: hidden;
            }
            #progress {
                width: 100%;
                height: 100%;
                background: var(--azul-claro);
                transform-origin: left;
                transform: scaleX(1);
            }
            #stage {
                position: fixed;
                top: calc(var(--toolbar-h) + var(--progress-h));
                left: 0;
                width: 100%;
                height: calc(100vh - var(--toolbar-h) - var(--progress-h));
                background: #fff;
                transition: top .18s ease, height .18s ease;
                overflow: hidden;
            }
            body.controls-hidden #stage {
                top: 0;
                height: 100vh;
            }
            .iframe-panel {
                position: absolute;
                inset: 0;
                visibility: hidden;
                opacity: 0;
                pointer-events: none;
                background: #fff;
                transition: opacity .22s ease;
            }
            .iframe-panel.active {
                visibility: visible;
                opacity: 1;
                pointer-events: auto;
                z-index: 2;
            }
            .iframe-panel.preload {
                visibility: hidden;
                opacity: 0;
                z-index: 1;
            }
            .iframe-panel iframe {
                width: 100%;
                height: 100%;
                border: 0;
                display: block;
                background: #fff;
            }
            .loading-overlay {
                position: absolute;
                inset: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 8px;
                background: #f8fafc;
                color: #334155;
                z-index: 3;
                font-size: 13px;
            }
            .loading-overlay small { color: #64748b; max-width: 520px; text-align: center; }
            .loading-overlay.hidden { display: none; }
            #diag {
                position: fixed;
                right: 10px;
                top: 48px;
                width: min(460px, calc(100vw - 20px));
                max-height: 54vh;
                z-index: 10020;
                background: rgba(15,23,42,.96);
                color: #e2e8f0;
                border: 1px solid rgba(255,255,255,.12);
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,.3);
                padding: 12px;
                display: none;
                overflow: auto;
                font-size: 11px;
            }
            #diag.open { display: block; }
            #diag h4 { margin: 0 0 8px; font-size: 12px; color: #fff; }
            #diag .hint { color: #94a3b8; margin-bottom: 8px; line-height: 1.35; }
            #diag-log { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; line-height: 1.45; }
            body.kiosk.controls-hidden { cursor: none; }
            @media (max-width: 900px) {
                #toolbar { grid-template-columns: 1fr auto; }
                .toolbar-center { display: none; }
                .btn .label { display: none; }
                .btn { padding: 0 7px; }
            }
        </style>
    </head>
    <body>
        <div id="control-shell">
            <div id="toolbar">
                <div class="toolbar-left">
                    <span>●</span>
                    <span id="panel-name">Carregando...</span>
                    <span id="panel-order"></span>
                </div>
                <div class="toolbar-center">
                    <div id="dots"></div>
                    <span id="countdown">--:--</span>
                </div>
                <div class="toolbar-right">
                    <button class="btn" onclick="mudarTela(-1)" title="Painel anterior (←)">←</button>
                    <button class="btn" id="pause-btn" onclick="alternarPausa()" title="Pausar/retomar (Espaço)">⏸ <span class="label">Pausar</span></button>
                    <button class="btn" onclick="mudarTela(1)" title="Próximo painel (→)">→</button>
                    <button class="btn" id="reload-toggle" onclick="alternarRecarregamento()" title="Ativar/desativar F5 automático neste painel">↻ <span class="label">F5 ON</span></button>
                    <button class="btn" onclick="recarregarAgora()" title="Atualizar este painel agora (R)">⟳</button>
                    <button class="btn" id="kiosk-btn" onclick="alternarModoTV()" title="Modo TV / Kiosk (K)">▣ <span class="label">TV</span></button>
                    <button class="btn" onclick="alternarTelaCheia()" title="Tela cheia (F)">⛶</button>
                    <button class="btn" onclick="toggleDiag()" title="Diagnóstico">ⓘ</button>
                    <button class="btn" onclick="irParaAjustes()" title="Voltar para ajustes">⚙</button>
                    <span id="clock"></span>
                </div>
            </div>
            <div id="progress-container"><div id="progress"></div></div>
        </div>

        <div id="stage"></div>

        <div id="diag">
            <h4>Diagnóstico do monitoramento</h4>
            <div class="hint">Domínios externos podem impedir iframe por X-Frame-Options/CSP. A aplicação registra carregamentos e trocas, mas não consegue acessar o conteúdo interno de outro domínio.</div>
            <div id="diag-log"></div>
        </div>

        <script>
            const panels = __PAINEIS__;
            const profileName = __PERFIL__;
            const generalReloadMs = __INTERVALO__;
            const autoHideEnabled = __AUTO_HIDE__;
            const kioskDefault = __KIOSK_DEFAULT__;
            const simRefreshSeconds = __SIM_REFRESH__;

            let index = 0;
            let paused = false;
            let remaining = 0;
            let totalSeconds = 0;
            let timer = null;
            let simTimer = null;
            let hideTimer = null;
            let kioskMode = false;
            let pool = new Map();
            let logs = [];

            const stage = document.getElementById('stage');
            const controlShell = document.getElementById('control-shell');
            const panelName = document.getElementById('panel-name');
            const panelOrder = document.getElementById('panel-order');
            const countdown = document.getElementById('countdown');
            const progress = document.getElementById('progress');
            const pauseBtn = document.getElementById('pause-btn');
            const reloadToggle = document.getElementById('reload-toggle');
            const kioskBtn = document.getElementById('kiosk-btn');
            const clock = document.getElementById('clock');
            const dots = document.getElementById('dots');
            const diag = document.getElementById('diag');
            const diagLog = document.getElementById('diag-log');

            const profileKey = profileName.replace(/[^a-zA-Z0-9_-]/g, '_');
            const indexKey = `monitor_v2_index_${profileKey}`;
            const reloadKey = `monitor_v2_reload_${profileKey}`;

            const savedIndex = parseInt(localStorage.getItem(indexKey) || '0', 10);
            if (!Number.isNaN(savedIndex) && savedIndex >= 0 && savedIndex < panels.length) index = savedIndex;

            let reloadStates = {};
            try { reloadStates = JSON.parse(localStorage.getItem(reloadKey) || '{}') || {}; } catch (e) { reloadStates = {}; }
            panels.forEach(p => {
                if (typeof reloadStates[p.id] !== 'boolean') reloadStates[p.id] = !!p.recarregar;
            });

            function nowStamp() {
                return new Date().toLocaleTimeString('pt-BR', {hour12: false});
            }

            function log(msg) {
                logs.unshift(`${nowStamp()}  ${msg}`);
                logs = logs.slice(0, 80);
                diagLog.textContent = logs.join('\n');
            }

            function escapeHtml(s) {
                return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
            }

            function createPanelFrame(i, role='preload') {
                const p = panels[i];
                if (!p) return null;
                if (pool.has(p.id)) return pool.get(p.id);

                const container = document.createElement('div');
                container.className = `iframe-panel ${role}`;
                container.dataset.panelId = p.id;

                const overlay = document.createElement('div');
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `<strong>Carregando ${escapeHtml(p.nome)}...</strong><small>Se a tela permanecer em branco, o site pode estar bloqueando exibição em iframe.</small>`;

                const iframe = document.createElement('iframe');
                iframe.src = p.link;
                iframe.allow = 'fullscreen';
                iframe.referrerPolicy = 'no-referrer-when-downgrade';

                const timeout = setTimeout(() => {
                    if (!overlay.classList.contains('hidden')) {
                        overlay.innerHTML = `<strong>O carregamento está demorando.</strong><small>Verifique conexão, sessão do sistema ou bloqueio de iframe (X-Frame-Options/CSP).</small>`;
                        log(`Aviso de carregamento: ${p.nome}`);
                    }
                }, 18000);

                iframe.addEventListener('load', () => {
                    clearTimeout(timeout);
                    overlay.classList.add('hidden');
                    log(`Carregado: ${p.nome}`);
                });

                container.appendChild(iframe);
                container.appendChild(overlay);
                stage.appendChild(container);

                const item = { container, iframe, overlay, panel: p };
                pool.set(p.id, item);
                return item;
            }

            function nextIndex() {
                return (index + 1) % panels.length;
            }

            function managePool() {
                const currentId = panels[index].id;
                const nextId = panels[nextIndex()].id;

                createPanelFrame(index, 'active');
                if (panels.length > 1) createPanelFrame(nextIndex(), 'preload');

                for (const [id, item] of pool.entries()) {
                    const keepBecauseReloadOff = reloadStates[id] === false;
                    const mustKeep = id === currentId || id === nextId || keepBecauseReloadOff;
                    if (!mustKeep) {
                        item.container.remove();
                        pool.delete(id);
                        log(`Liberado da memória: ${item.panel.nome}`);
                    }
                }

                for (const [id, item] of pool.entries()) {
                    item.container.classList.remove('active', 'preload');
                    if (id === currentId) item.container.classList.add('active');
                    else item.container.classList.add('preload');
                }
            }

            function renderDots() {
                dots.innerHTML = '';
                panels.forEach((p, i) => {
                    const d = document.createElement('span');
                    d.className = 'dot' + (i === index ? ' active' : '');
                    d.title = p.nome;
                    d.addEventListener('click', () => { index = i; afterIndexChange('Clique no indicador'); });
                    dots.appendChild(d);
                });
            }

            function renderReloadButton() {
                const on = reloadStates[panels[index].id] !== false;
                reloadToggle.classList.toggle('active-good', on);
                reloadToggle.classList.toggle('active-bad', !on);
                reloadToggle.innerHTML = on ? '↻ <span class="label">F5 ON</span>' : '🔒 <span class="label">F5 OFF</span>';
            }

            function updateHeader() {
                const p = panels[index];
                panelName.textContent = p.nome;
                panelOrder.textContent = `${index + 1}/${panels.length}`;
                renderDots();
                renderReloadButton();
                localStorage.setItem(indexKey, String(index));
            }

            function formatCountdown(s) {
                const m = Math.floor(Math.max(0, s) / 60);
                const sec = Math.max(0, s) % 60;
                return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
            }

            function restartTimer() {
                clearInterval(timer);
                if (paused) return;

                totalSeconds = Math.max(5, parseInt(panels[index].tempo || 20, 10));
                remaining = totalSeconds;
                countdown.textContent = formatCountdown(remaining);

                progress.style.transition = 'none';
                progress.style.transform = 'scaleX(1)';
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        progress.style.transition = `transform ${totalSeconds}s linear`;
                        progress.style.transform = 'scaleX(0)';
                    });
                });

                timer = setInterval(() => {
                    if (paused) return;
                    remaining -= 1;
                    countdown.textContent = formatCountdown(remaining);
                    if (remaining <= 0) {
                        mudarTela(1);
                    }
                }, 1000);
            }

            function startSimRefresh() {
                clearInterval(simTimer);
                simTimer = null;
                const p = panels[index];
                const isSim = String(p.nome || '').toLowerCase().includes('sim') || String(p.link || '').toLowerCase().includes('sim-submissions');
                const reloadOn = reloadStates[p.id] !== false;
                if (isSim && reloadOn && simRefreshSeconds > 0) {
                    simTimer = setInterval(() => {
                        if (!paused && index >= 0 && reloadStates[panels[index].id] !== false) {
                            log(`F5 técnico do SIM: ${panels[index].nome}`);
                            recarregarAgora(false);
                        }
                    }, simRefreshSeconds * 1000);
                }
            }

            function afterIndexChange(reason='Troca') {
                managePool();
                updateHeader();
                restartTimer();
                startSimRefresh();
                log(`${reason}: ${panels[index].nome}`);
            }

            function mudarTela(direction) {
                if (!panels.length) return;
                index = (index + direction + panels.length) % panels.length;
                afterIndexChange(direction > 0 ? 'Próximo painel' : 'Painel anterior');
            }

            function alternarPausa() {
                paused = !paused;
                if (paused) {
                    clearInterval(timer);
                    clearInterval(simTimer);
                    pauseBtn.classList.add('active-bad');
                    pauseBtn.innerHTML = '▶ <span class="label">Retomar</span>';
                    countdown.textContent = 'PAUSA';
                    progress.style.transition = 'none';
                    log('Rotação pausada');
                } else {
                    pauseBtn.classList.remove('active-bad');
                    pauseBtn.innerHTML = '⏸ <span class="label">Pausar</span>';
                    restartTimer();
                    startSimRefresh();
                    log('Rotação retomada');
                }
            }

            function alternarRecarregamento() {
                const p = panels[index];
                reloadStates[p.id] = !(reloadStates[p.id] !== false);
                localStorage.setItem(reloadKey, JSON.stringify(reloadStates));
                renderReloadButton();
                managePool();
                startSimRefresh();
                log(`F5 automático ${reloadStates[p.id] ? 'ON' : 'OFF'}: ${p.nome}`);
            }

            function recarregarAgora(logEvent=true) {
                const p = panels[index];
                const item = pool.get(p.id) || createPanelFrame(index, 'active');
                if (!item) return;
                item.overlay.classList.remove('hidden');
                item.overlay.innerHTML = `<strong>Atualizando ${escapeHtml(p.nome)}...</strong><small>Recarregamento manual/automático da página.</small>`;
                item.iframe.src = p.link;
                if (logEvent) log(`Atualização manual: ${p.nome}`);
            }

            function alternarTelaCheia() {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(() => {});
                } else if (document.exitFullscreen) {
                    document.exitFullscreen().catch(() => {});
                }
            }

            function showControls() {
                controlShell.classList.remove('hidden');
                document.body.classList.remove('controls-hidden');
                document.body.style.cursor = '';
                clearTimeout(hideTimer);
                if (autoHideEnabled || kioskMode) {
                    hideTimer = setTimeout(hideControls, kioskMode ? 2200 : 4200);
                }
            }

            function hideControls() {
                if (!(autoHideEnabled || kioskMode)) return;
                controlShell.classList.add('hidden');
                document.body.classList.add('controls-hidden');
                if (kioskMode) document.body.style.cursor = 'none';
            }

            function alternarModoTV(force=null) {
                kioskMode = force === null ? !kioskMode : !!force;
                document.body.classList.toggle('kiosk', kioskMode);
                kioskBtn.classList.toggle('active-good', kioskMode);
                kioskBtn.innerHTML = kioskMode ? '▣ <span class="label">TV ON</span>' : '▣ <span class="label">TV</span>';
                if (kioskMode && !document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(() => {});
                }
                showControls();
                log(`Modo TV ${kioskMode ? 'ativado' : 'desativado'}`);
            }

            function toggleDiag() {
                diag.classList.toggle('open');
                showControls();
            }

            function irParaAjustes() {
                try {
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set('iniciado', 'false');
                    window.parent.location.href = url.toString();
                } catch (e) {
                    const url = new URL(window.location.href);
                    url.searchParams.set('iniciado', 'false');
                    window.location.href = url.toString();
                }
            }

            function updateClock() {
                const d = new Date();
                clock.textContent = d.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
            }

            document.addEventListener('mousemove', showControls, {passive: true});
            document.addEventListener('touchstart', showControls, {passive: true});
            document.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowLeft') mudarTela(-1);
                else if (e.key === 'ArrowRight') mudarTela(1);
                else if (e.code === 'Space') { e.preventDefault(); alternarPausa(); }
                else if (e.key.toLowerCase() === 'f') alternarTelaCheia();
                else if (e.key.toLowerCase() === 'r') recarregarAgora();
                else if (e.key.toLowerCase() === 'k') alternarModoTV();
            });

            if (generalReloadMs > 0) {
                setTimeout(() => {
                    try {
                        const url = new URL(window.parent.location.href);
                        url.searchParams.set('iniciado', 'true');
                        window.parent.location.href = url.toString();
                    } catch (e) {
                        window.location.reload();
                    }
                }, generalReloadMs);
            }

            updateClock();
            setInterval(updateClock, 1000);
            log(`Aplicação iniciada - perfil ${profileName}`);
            log(`Painéis ativos: ${panels.length}`);
            afterIndexChange('Inicial');
            showControls();

            if (kioskDefault) {
                setTimeout(() => alternarModoTV(true), 500);
            }
        </script>
    </body>
    </html>
    """

    html_painel = (
        html_painel
        .replace("__PAINEIS__", paineis_json)
        .replace("__PERFIL__", perfil_json)
        .replace("__INTERVALO__", str(intervalo_limpeza_ms))
        .replace("__AUTO_HIDE__", auto_hide)
        .replace("__KIOSK_DEFAULT__", kiosk_default)
        .replace("__SIM_REFRESH__", str(sim_refresh_seconds))
    )

    # O componente ocupa praticamente toda a viewport. O CSS interno administra a barra compacta.
    components.html(html_painel, height=960, scrolling=False)
