import base64
import copy
import hashlib
import html
import json
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# Painel de Monitoramento 2.4.1
# Inclui: 2.2 Estabilidade e Operação + 2.3 Experiência e Visual + 2.4 Primeiro Uso
# 2.4.2: correção do F5 OFF com preservação automática e navegação de Ajustes
# Cor principal: Azul petróleo #0E5285
# =========================================================

APP_VERSION = "2.4.2"
CONFIG_VERSION = 3
CONFIG_PATH = Path.cwd() / "monitoramento_config.json"
BACKUP_PATH = Path.cwd() / "monitoramento_config.backup.json"

st.set_page_config(
    page_title=f"Painel de Monitoramento {APP_VERSION}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def novo_id(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def painel_padrao(nome, link, tempo, reload_enabled=True, ativo=True, tipo="normal"):
    return {
        "id": novo_id("p_"),
        "nome": nome,
        "link": link,
        "tempo": int(tempo),
        "ativo": bool(ativo),
        "reload_enabled": bool(reload_enabled),
        "reload_strategy": "interval" if tipo == "sim" else "on_show",
        "reload_interval": 20 if tipo == "sim" else 60,
        "preserve_session": not bool(reload_enabled),
        "tipo": tipo,
    }


def perfil_padrao(nome="Suporte"):
    pid = novo_id("pr_")
    return pid, {
        "id": pid,
        "nome": nome,
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
                tipo="sim",
            ),
        ],
        "horas_reload_geral": 0,
        "auto_ocultar_controles": True,
        "modo_tv_padrao": False,
        "preload_seconds": 8,
        "watchdog_seconds": 90,
        "ui_scale": 100,
        "toolbar_position": "top",
        "transition_ms": 220,
        "show_clock": True,
        "show_dots": True,
        "show_status": True,
        "config_view": "compact",
    }


_DEFAULT_PROFILE_ID, _DEFAULT_PROFILE = perfil_padrao()
DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,
    "default_profile_id": _DEFAULT_PROFILE_ID,
    "profiles": {_DEFAULT_PROFILE_ID: _DEFAULT_PROFILE},
}


def config_hash(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def url_valida(url):
    try:
        parsed = urlparse(str(url).strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _clamp_int(value, default, minimum, maximum):
    try:
        return max(minimum, min(maximum, int(value)))
    except Exception:
        return default


def migrar_config_legada(data):
    """Migra configuração 2.0/2.1 (perfis por nome) para o formato 2.3 (perfis por ID)."""
    if not isinstance(data, dict):
        return copy.deepcopy(DEFAULT_CONFIG)

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        return copy.deepcopy(DEFAULT_CONFIG)

    # Já está no formato atual se as entradas tiverem id/nome.
    if all(isinstance(v, dict) and v.get("id") and v.get("nome") for v in profiles.values()):
        return data

    old_active = data.get("active_profile")
    new_profiles = {}
    name_to_id = {}

    for old_name, old_profile in profiles.items():
        if not isinstance(old_profile, dict):
            continue
        pid = novo_id("pr_")
        name_to_id[str(old_name)] = pid
        old_sim_seconds = _clamp_int(old_profile.get("sim_refresh_seconds", 20), 20, 0, 300)
        new_panels = []
        for p in old_profile.get("paineis", []):
            if not isinstance(p, dict):
                continue
            nome = str(p.get("nome") or "Novo Painel")
            link = str(p.get("link") or "")
            old_reload = bool(p.get("recarregar", True))
            is_sim = "sim" in nome.lower() or "sim-submissions" in link.lower()
            new_panels.append(
                {
                    "id": str(p.get("id") or novo_id("p_")),
                    "nome": nome,
                    "link": link,
                    "tempo": _clamp_int(p.get("tempo", 20), 20, 5, 600),
                    "ativo": bool(p.get("ativo", True)),
                    "reload_enabled": old_reload,
                    "reload_strategy": "interval" if is_sim and old_sim_seconds > 0 else "on_show",
                    "reload_interval": old_sim_seconds if is_sim and old_sim_seconds > 0 else 60,
                    "preserve_session": not old_reload,
                    "tipo": "sim" if is_sim else "normal",
                }
            )

        new_profiles[pid] = {
            "id": pid,
            "nome": str(old_name),
            "paineis": new_panels,
            "horas_reload_geral": _clamp_int(old_profile.get("horas_reload_geral", 0), 0, 0, 24),
            "auto_ocultar_controles": bool(old_profile.get("auto_ocultar_controles", True)),
            "modo_tv_padrao": bool(old_profile.get("modo_tv_padrao", False)),
            "preload_seconds": 8,
            "watchdog_seconds": 90,
            "ui_scale": 100,
            "toolbar_position": "top",
            "transition_ms": 220,
            "show_clock": True,
            "show_dots": True,
            "show_status": True,
            "config_view": "compact",
        }

    if not new_profiles:
        return copy.deepcopy(DEFAULT_CONFIG)

    default_id = name_to_id.get(str(old_active)) or next(iter(new_profiles))
    return {"version": CONFIG_VERSION, "default_profile_id": default_id, "profiles": new_profiles}


def normalizar_config(data):
    data = migrar_config_legada(copy.deepcopy(data))
    if not isinstance(data, dict):
        return copy.deepcopy(DEFAULT_CONFIG)

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        return copy.deepcopy(DEFAULT_CONFIG)

    normalized_profiles = {}
    seen_profile_ids = set()
    for key, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        pid = str(profile.get("id") or key or novo_id("pr_"))
        if pid in seen_profile_ids:
            pid = novo_id("pr_")
        seen_profile_ids.add(pid)

        nome = str(profile.get("nome") or "Perfil")
        raw_panels = profile.get("paineis") if isinstance(profile.get("paineis"), list) else []
        panels = []
        seen_panel_ids = set()
        for p in raw_panels:
            if not isinstance(p, dict):
                continue
            panel_id = str(p.get("id") or novo_id("p_"))
            if panel_id in seen_panel_ids:
                panel_id = novo_id("p_")
            seen_panel_ids.add(panel_id)

            legacy_reload = p.get("recarregar")
            reload_enabled = bool(p.get("reload_enabled", legacy_reload if legacy_reload is not None else True))
            strategy = str(p.get("reload_strategy") or "on_show")
            if strategy not in {"on_show", "interval"}:
                strategy = "on_show"
            panel_type = str(p.get("tipo") or "normal")
            if panel_type not in {"normal", "sim", "personalizado"}:
                panel_type = "normal"

            panels.append(
                {
                    "id": panel_id,
                    "nome": str(p.get("nome") or "Novo Painel"),
                    "link": str(p.get("link") or ""),
                    "tempo": _clamp_int(p.get("tempo", 20), 20, 5, 600),
                    "ativo": bool(p.get("ativo", True)),
                    "reload_enabled": reload_enabled,
                    "reload_strategy": strategy,
                    "reload_interval": _clamp_int(p.get("reload_interval", 60), 60, 5, 3600),
                    "preserve_session": bool(p.get("preserve_session", not reload_enabled)),
                    "tipo": panel_type,
                }
            )

        profile_norm = {
            "id": pid,
            "nome": nome,
            "paineis": panels,
            "horas_reload_geral": _clamp_int(profile.get("horas_reload_geral", 0), 0, 0, 24),
            "auto_ocultar_controles": bool(profile.get("auto_ocultar_controles", True)),
            "modo_tv_padrao": bool(profile.get("modo_tv_padrao", False)),
            "preload_seconds": _clamp_int(profile.get("preload_seconds", 8), 8, 0, 30),
            "watchdog_seconds": _clamp_int(profile.get("watchdog_seconds", 90), 90, 30, 600),
            "ui_scale": int(profile.get("ui_scale", 100)) if int(profile.get("ui_scale", 100)) in {90, 100, 110, 125} else 100,
            "toolbar_position": str(profile.get("toolbar_position", "top")) if str(profile.get("toolbar_position", "top")) in {"top", "bottom"} else "top",
            "transition_ms": int(profile.get("transition_ms", 220)) if int(profile.get("transition_ms", 220)) in {0, 150, 220, 400} else 220,
            "show_clock": bool(profile.get("show_clock", True)),
            "show_dots": bool(profile.get("show_dots", True)),
            "show_status": bool(profile.get("show_status", True)),
            "config_view": str(profile.get("config_view", "compact")) if str(profile.get("config_view", "compact")) in {"compact", "detailed"} else "compact",
        }
        normalized_profiles[pid] = profile_norm

    if not normalized_profiles:
        return copy.deepcopy(DEFAULT_CONFIG)

    default_id = str(data.get("default_profile_id") or "")
    if default_id not in normalized_profiles:
        default_id = next(iter(normalized_profiles))

    return {"version": CONFIG_VERSION, "default_profile_id": default_id, "profiles": normalized_profiles}


def validar_config_importada(data):
    erros = []
    avisos = []
    if not isinstance(data, dict):
        return ["O arquivo precisa conter um objeto JSON."], avisos
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        erros.append("Nenhum perfil de monitoramento foi encontrado.")
        return erros, avisos

    nomes = set()
    total_panels = 0
    for key, profile in profiles.items():
        if not isinstance(profile, dict):
            erros.append(f"Perfil {key} possui formato inválido.")
            continue
        nome = str(profile.get("nome") or key).strip()
        if nome.lower() in nomes:
            avisos.append(f"Há perfis com nome repetido: {nome}.")
        nomes.add(nome.lower())
        paineis = profile.get("paineis", [])
        if not isinstance(paineis, list):
            erros.append(f"Painéis do perfil {nome} não estão em uma lista.")
            continue
        total_panels += len(paineis)
        for p in paineis:
            if not isinstance(p, dict):
                erros.append(f"Há painel inválido no perfil {nome}.")
                continue
            link = str(p.get("link") or "").strip()
            if link and not url_valida(link):
                avisos.append(f"URL aparentemente inválida em {nome}: {link[:60]}")
    if total_panels == 0:
        avisos.append("A configuração importada não possui painéis cadastrados.")
    return erros, avisos


def carregar_config():
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                return normalizar_config(json.load(f))
        except Exception as exc:
            try:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                corrupt = CONFIG_PATH.with_name(f"monitoramento_config.corrompido_{stamp}.json")
                shutil.copy2(CONFIG_PATH, corrupt)
                st.session_state["config_corrompida_backup"] = corrupt.name
            except Exception:
                pass
            st.session_state["ultimo_erro_persistencia"] = f"Falha ao ler configuração: {exc}"
    return copy.deepcopy(DEFAULT_CONFIG)


def salvar_config(config, force=False):
    """Grava apenas quando necessário, com backup e substituição atômica."""
    try:
        cfg = normalizar_config(config)
        current_hash = config_hash(cfg)
        if not force and st.session_state.get("ultimo_hash_salvo") == current_hash:
            return True

        if CONFIG_PATH.exists():
            try:
                current_disk = CONFIG_PATH.read_text(encoding="utf-8")
                disk_hash = hashlib.sha256(current_disk.encode("utf-8")).hexdigest()
                new_raw = json.dumps(cfg, ensure_ascii=False, indent=2)
                new_hash_raw = hashlib.sha256(new_raw.encode("utf-8")).hexdigest()
                if disk_hash != new_hash_raw:
                    shutil.copy2(CONFIG_PATH, BACKUP_PATH)
            except Exception:
                pass

        raw = json.dumps(cfg, ensure_ascii=False, indent=2)
        fd, temp_name = tempfile.mkstemp(prefix="monitoramento_", suffix=".json", dir=str(CONFIG_PATH.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.write(raw)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(temp_name, CONFIG_PATH)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

        st.session_state["ultimo_hash_salvo"] = current_hash
        st.session_state["ultima_gravacao"] = datetime.now().strftime("%H:%M:%S")
        st.session_state.pop("ultimo_erro_persistencia", None)
        return True
    except Exception as exc:
        st.session_state["ultimo_erro_persistencia"] = str(exc)
        return False


def regenerar_ids(perfil):
    novo = copy.deepcopy(perfil)
    novo["id"] = novo_id("pr_")
    for p in novo.get("paineis", []):
        p["id"] = novo_id("p_")
    return novo


def perfil_por_id(config, pid):
    return config["profiles"].get(pid)


def perfil_id_da_url(config):
    requested = str(st.query_params.get("perfil", "") or "")
    if requested in config["profiles"]:
        return requested
    return config.get("default_profile_id") if config.get("default_profile_id") in config["profiles"] else next(iter(config["profiles"]))


def perfil_ativos(perfil):
    return [
        p for p in perfil.get("paineis", [])
        if p.get("ativo", True) and p.get("link", "").strip() and url_valida(p.get("link", ""))
    ]


def b64_json(data):
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


if "config_v23" not in st.session_state:
    st.session_state.config_v23 = carregar_config()
    st.session_state["ultimo_hash_salvo"] = config_hash(st.session_state.config_v23)

config = normalizar_config(st.session_state.config_v23)
st.session_state.config_v23 = config

query_iniciado = str(st.query_params.get("iniciado", "false")).lower() == "true"
if "iniciado" not in st.session_state:
    st.session_state.iniciado = query_iniciado
elif query_iniciado != bool(st.session_state.iniciado):
    st.session_state.iniciado = query_iniciado

active_profile_id = perfil_id_da_url(config)

# =========================================================
# CSS - Pacote Visual/UX 2.4
# =========================================================
st.markdown(
    """
    <style>
        :root {
            --primary: #0E5285;
            --primary-dark: #093D63;
            --primary-hover: #0B466F;
            --primary-soft: #EAF3FA;
            --primary-soft-2: #F5F9FC;
            --primary-border: #C7D9E7;
            --text-main: #16324A;
            --text-muted: #64748B;
            --success: #15803D;
            --warning: #B45309;
            --danger: #B42318;
            --surface: #FFFFFF;
        }
        header {visibility: hidden !important; height: 0 !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        .stApp { background: #F3F7FB; color: var(--text-main); }
        .block-container { max-width: 1240px; padding-top: 20px !important; padding-bottom: 42px !important; }
        h1, h2, h3, h4, label { color: var(--primary) !important; }
        .app-title { font-size: 30px; line-height: 1.12; font-weight: 800; color: var(--primary); margin: 3px 0 4px; letter-spacing: -.55px; }
        .app-subtitle { color: var(--text-muted); font-size: 14px; margin-bottom: 14px; }
        .section-title { font-size: 16px; font-weight: 780; color: var(--primary); margin: 0; }
        .summary-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:12px 0 18px; }
        .summary-card { background:#fff; border:1px solid var(--primary-border); border-radius:12px; padding:13px 15px; box-shadow:0 1px 3px rgba(14,82,133,.055); }
        .summary-label { color:var(--text-muted); font-size:10.5px; font-weight:750; text-transform:uppercase; letter-spacing:.4px; }
        .summary-value { color:var(--primary); font-size:21px; font-weight:820; margin-top:2px; }
        .save-line { color:#64748B; font-size:11px; text-align:right; margin-top:-4px; margin-bottom:4px; }
        .profile-help { color:var(--text-muted); font-size:11px; margin-top:-8px; margin-bottom:8px; }
        .rotation-preview { background:#fff; border:1px solid var(--primary-border); border-radius:10px; padding:9px 12px; margin:-2px 0 16px; color:#475569; font-size:12px; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
        .rotation-preview strong { color:var(--primary); }
        .onboarding-card { background:linear-gradient(135deg,#F8FBFE 0%,#EDF5FB 100%); border:1px solid var(--primary-border); border-radius:12px; padding:14px 16px; margin:6px 0 16px; }
        .onboarding-title { color:var(--primary); font-size:14px; font-weight:800; margin-bottom:7px; }
        .onboarding-steps { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }
        .onboarding-step { background:#fff; border:1px solid #D9E6F0; border-radius:9px; padding:9px 10px; color:#475569; font-size:11.5px; }
        .onboarding-step b { color:var(--primary); display:block; margin-bottom:2px; }
        .panel-headline { display:flex; align-items:center; justify-content:space-between; gap:10px; margin:-1px 0 7px; flex-wrap:wrap; }
        .panel-headline-left { display:flex; align-items:center; gap:8px; min-width:0; }
        .panel-number { width:31px; height:25px; border-radius:7px; display:inline-flex; align-items:center; justify-content:center; background:var(--primary-soft); border:1px solid #BAD4E7; color:var(--primary); font-size:11px; font-weight:850; flex:none; }
        .panel-headline-name { color:#244157; font-size:12.5px; font-weight:760; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:520px; }
        .panel-badges { display:flex; gap:5px; flex-wrap:wrap; align-items:center; }
        .ux24-fixed-bar { position:fixed; left:0; right:0; bottom:0; z-index:999998; background:rgba(255,255,255,.97); backdrop-filter:blur(10px); border-top:1px solid #C7D9E7; box-shadow:0 -5px 22px rgba(14,82,133,.09); }
        .ux24-fixed-inner { max-width:1240px; margin:0 auto; padding:10px 18px; display:flex; justify-content:space-between; align-items:center; gap:16px; }
        .ux24-fixed-copy { color:#64748B; font-size:11px; }
        .ux24-fixed-copy strong { color:#0E5285; font-size:12px; }
        .ux24-start-link { display:inline-flex; align-items:center; justify-content:center; text-decoration:none!important; background:#0E5285; color:#fff!important; padding:9px 18px; border-radius:8px; font-size:12.5px; font-weight:800; min-width:190px; box-shadow:0 2px 7px rgba(14,82,133,.17); }
        .ux24-start-link:hover { background:#0B466F; color:#fff!important; }
        .ux24-start-disabled { display:inline-flex; align-items:center; justify-content:center; background:#E2E8F0; color:#94A3B8; padding:9px 18px; border-radius:8px; font-size:12.5px; font-weight:800; min-width:190px; cursor:not-allowed; }
        .version-pill { display:inline-block; padding:3px 8px; border-radius:999px; background:var(--primary-soft); border:1px solid var(--primary-border); color:var(--primary); font-size:10px; font-weight:800; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--primary-border)!important; border-radius:12px!important; background:#fff!important; box-shadow:0 1px 3px rgba(14,82,133,.04); }
        .stTextInput input,.stNumberInput input,div[data-baseweb="select"]>div { border-radius:8px!important; border-color:#D6E2EC!important; }
        .stTextInput input:focus,.stNumberInput input:focus { border-color:var(--primary)!important; box-shadow:0 0 0 1px var(--primary)!important; }
        .stButton button,.stDownloadButton button,.stLinkButton a { border-radius:8px!important; font-weight:650!important; min-height:37px; }
        .stButton button[kind="primary"] { background:var(--primary)!important; color:#fff!important; border:1px solid var(--primary)!important; }
        .stButton button[kind="primary"]:hover { background:var(--primary-hover)!important; border-color:var(--primary-hover)!important; }
        .stButton button:not([kind="primary"]):hover,.stDownloadButton button:hover { color:var(--primary)!important; border-color:var(--primary)!important; background:var(--primary-soft-2)!important; }
        /*
           O primaryColor do tema é a fonte principal da cor dos toggles.
           Estes seletores funcionam como fallback visual entre versões do Streamlit/BaseWeb.
        */
        div[data-testid="stToggle"] [data-baseweb="checkbox"] input:checked ~ div,
        div[data-testid="stToggle"] [data-baseweb="checkbox"] input:checked + div,
        div[data-testid="stToggle"] [role="switch"][aria-checked="true"],
        div[data-testid="stToggle"] [role="checkbox"][aria-checked="true"] {
            background-color:var(--primary)!important;
            border-color:var(--primary)!important;
        }
        div[data-testid="stToggle"] [data-baseweb="checkbox"] input:not(:checked) ~ div,
        div[data-testid="stToggle"] [data-baseweb="checkbox"] input:not(:checked) + div,
        div[data-testid="stToggle"] [role="switch"][aria-checked="false"],
        div[data-testid="stToggle"] [role="checkbox"][aria-checked="false"] {
            background-color:#CBD5E1!important;
            border-color:#CBD5E1!important;
        }
        div[data-testid="stToggle"] [data-baseweb="checkbox"] > div { transition:background-color .15s ease!important; }
        div[data-testid="stToggle"] label p { color:var(--primary)!important; font-weight:650!important; }
        div[data-testid="stToggle"] { min-width:0; }
        div[data-testid="stExpander"] details { border-color:var(--primary-border)!important; border-radius:10px!important; background:#fff!important; }
        .status-ok { color:var(--success); font-size:11.5px; font-weight:700; }
        .status-warn { color:var(--warning); font-size:11.5px; font-weight:700; }
        .status-danger { color:var(--danger); font-size:11.5px; font-weight:700; }
        .muted { color:var(--text-muted); font-size:11.5px; }
        .badge { display:inline-block; padding:2px 7px; border-radius:999px; font-size:10px; line-height:1.3; font-weight:800; letter-spacing:.2px; }
        .badge-blue { color:var(--primary); background:var(--primary-soft); border:1px solid #BAD4E7; }
        .badge-gray { color:#566371; background:#F1F5F9; border:1px solid #CBD5E1; }
        .badge-green { color:#166534; background:#F0FDF4; border:1px solid #BBF7D0; }
        .badge-amber { color:#92400E; background:#FFFBEB; border:1px solid #FDE68A; }
        .compact-hint { color:#64748B; font-size:11px; margin-top:-5px; }
        .panel-divider { height:1px; background:#EEF3F7; margin:4px 0 8px; }
        .profile-url { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; color:#475569; background:#F8FAFC; border:1px solid #E2E8F0; padding:8px 10px; border-radius:8px; }
        .block-container { padding-bottom:100px!important; }
        @media(max-width:900px){
            .summary-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
            .block-container{padding-left:12px!important;padding-right:12px!important;padding-bottom:112px!important;}
            .onboarding-steps{grid-template-columns:1fr;}
            .ux24-fixed-inner{padding:9px 12px;}
            .ux24-fixed-copy span{display:none;}
            .ux24-start-link,.ux24-start-disabled{min-width:155px;}
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# TELA 1 - CONFIGURAÇÃO
# =========================================================
if not st.session_state.iniciado:
    perfil = perfil_por_id(config, active_profile_id)
    if perfil is None:
        active_profile_id = config["default_profile_id"]
        perfil = perfil_por_id(config, active_profile_id)

    paineis = perfil["paineis"]
    ativos = perfil_ativos(perfil)
    tempo_total = sum(int(p.get("tempo", 0)) for p in ativos)
    m, s = divmod(tempo_total, 60)
    tempo_fmt = f"{m}m {s:02d}s" if m else f"{s}s"
    urls_invalidas = sum(1 for p in paineis if p.get("ativo", True) and p.get("link", "").strip() and not url_valida(p.get("link", "")))
    preservados = sum(1 for p in paineis if p.get("preserve_session", False) or not p.get("reload_enabled", True))
    invalid_active = [p for p in paineis if p.get("ativo", True) and p.get("link", "").strip() and not url_valida(p.get("link", ""))]

    def iniciar_monitoramento_ux24():
        atuais = perfil_ativos(perfil)
        invalidos = [p for p in perfil.get("paineis", []) if p.get("ativo", True) and p.get("link", "").strip() and not url_valida(p.get("link", ""))]
        if not atuais:
            st.error("Ative e configure pelo menos um painel com URL válida.")
            return
        if invalidos:
            st.error("Existem painéis ativos com URL inválida. Corrija-os antes de iniciar.")
            return
        salvar_config(config)
        st.session_state.iniciado = True
        st.query_params["perfil"] = active_profile_id
        st.query_params["iniciado"] = "true"
        st.rerun()

    top_left, top_right = st.columns([1.6, 1])
    with top_left:
        st.image("https://www.ssinformatica.net/wp-content/uploads/2023/03/Grupo-SS.png", width=250)
        st.markdown('<div class="app-title">Painel de Monitoramento</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-subtitle">Organize as telas, defina o tempo de exibição e inicie a rotação automática do monitor.</div>', unsafe_allow_html=True)
    with top_right:
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        profile_ids = list(config["profiles"].keys())
        selected = st.selectbox(
            "Perfil deste monitor",
            options=profile_ids,
            index=profile_ids.index(active_profile_id),
            format_func=lambda pid: config["profiles"][pid]["nome"],
            key="perfil_select_v23",
            help="Um perfil é um conjunto de painéis. Cada TV ou monitor pode usar um perfil diferente.",
        )
        st.markdown('<div class="profile-help">Define quais painéis serão exibidos neste monitor.</div>', unsafe_allow_html=True)
        if selected != active_profile_id:
            st.query_params["perfil"] = selected
            st.query_params["iniciado"] = "false"
            st.session_state.iniciado = False
            st.rerun()
        if st.button("▶ Iniciar monitoramento", type="primary", use_container_width=True, key="start_top_v24"):
            iniciar_monitoramento_ux24()

    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-card" title="Quantidade total de painéis cadastrados neste perfil."><div class="summary-label">Painéis cadastrados</div><div class="summary-value">{len(paineis)}</div></div>
            <div class="summary-card" title="Painéis habilitados e com endereço válido que participarão da rotação."><div class="summary-label">Painéis ativos</div><div class="summary-value">{len(ativos)}</div></div>
            <div class="summary-card" title="Tempo necessário para exibir todos os painéis ativos uma vez."><div class="summary-label">Duração de uma volta</div><div class="summary-value">{tempo_fmt}</div></div>
            <div class="summary-card" title="Painéis mantidos carregados em segundo plano para preservar login, filtros ou estado da página."><div class="summary-label">Painéis mantidos abertos</div><div class="summary-value">{preservados}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    last_saved = st.session_state.get("ultima_gravacao")
    if last_saved:
        st.markdown(f'<div class="save-line" title="Última gravação às {last_saved}">✓ Salvo automaticamente</div>', unsafe_allow_html=True)

    if ativos:
        nomes_preview = [html.escape(str(p.get("nome") or "Painel")) for p in ativos]
        if len(nomes_preview) > 5:
            visiveis = nomes_preview[:5]
            preview = " → ".join(visiveis) + f" → +{len(nomes_preview)-5}"
        else:
            preview = " → ".join(nomes_preview)
        st.markdown(
            f'<div class="rotation-preview"><strong>Ordem de exibição:</strong><span>{preview}</span><span>→ repetir</span></div>',
            unsafe_allow_html=True,
        )

    if "ux24_onboarding_dismissed" not in st.session_state:
        st.session_state["ux24_onboarding_dismissed"] = False
    if not st.session_state["ux24_onboarding_dismissed"]:
        with st.container(border=False):
            g1, g2 = st.columns([5, 1])
            with g1:
                st.markdown(
                    """
                    <div class="onboarding-card">
                        <div class="onboarding-title">Primeiro acesso? Configure o monitor em 3 passos</div>
                        <div class="onboarding-steps">
                            <div class="onboarding-step"><b>1. Escolha o perfil</b>Selecione o conjunto de painéis que esta tela deve mostrar.</div>
                            <div class="onboarding-step"><b>2. Confira os painéis</b>Ajuste ordem, tempo na tela e atualização automática.</div>
                            <div class="onboarding-step"><b>3. Inicie a rotação</b>Clique em “Iniciar monitoramento” e deixe a exibição rodar.</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with g2:
                st.markdown("<div style='height:19px'></div>", unsafe_allow_html=True)
                if st.button("Entendi", use_container_width=True, key="dismiss_guide_v24"):
                    st.session_state["ux24_onboarding_dismissed"] = True
                    st.rerun()

    # Perfis
    with st.expander("Perfis de monitoramento", expanded=False):
        p1, p2, p3, p4 = st.columns([2.2, 1, 1, 1])
        with p1:
            novo_nome = st.text_input("Novo perfil", placeholder="Ex.: Coordenação, eSocial, SAT...", key="novo_perfil_v23")
        with p2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Criar", use_container_width=True, key="criar_perfil_v23"):
                nome = novo_nome.strip()
                if not nome:
                    st.warning("Informe o nome do perfil.")
                elif any(p["nome"].strip().lower() == nome.lower() for p in config["profiles"].values()):
                    st.warning("Já existe um perfil com esse nome.")
                else:
                    pid = novo_id("pr_")
                    new_profile = copy.deepcopy(_DEFAULT_PROFILE)
                    new_profile.update({"id": pid, "nome": nome, "paineis": []})
                    config["profiles"][pid] = new_profile
                    salvar_config(config, force=True)
                    st.query_params["perfil"] = pid
                    st.toast("Perfil criado.")
                    st.rerun()
        with p3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Duplicar", use_container_width=True, key="duplicar_perfil_v23"):
                clone = regenerar_ids(perfil)
                base = perfil["nome"]
                used = {p["nome"] for p in config["profiles"].values()}
                n = 1
                candidate = f"{base} - Cópia"
                while candidate in used:
                    n += 1
                    candidate = f"{base} - Cópia {n}"
                clone["nome"] = candidate
                config["profiles"][clone["id"]] = clone
                salvar_config(config, force=True)
                st.query_params["perfil"] = clone["id"]
                st.toast("Perfil duplicado.")
                st.rerun()
        with p4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Excluir", use_container_width=True, key="pedir_excluir_perfil_v23", disabled=len(config["profiles"]) <= 1):
                st.session_state["confirmar_exclusao_perfil_v23"] = True
                st.rerun()

        r1, r2, r3 = st.columns([2.2, 1, 1])
        with r1:
            nome_editado = st.text_input("Nome do perfil selecionado", value=perfil["nome"], key=f"rename_{active_profile_id}")
        with r2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Renomear", use_container_width=True, key="rename_btn_v23"):
                nome = nome_editado.strip()
                if nome and not any(pid != active_profile_id and p["nome"].strip().lower() == nome.lower() for pid, p in config["profiles"].items()):
                    perfil["nome"] = nome
                    salvar_config(config, force=True)
                    st.toast("Perfil renomeado.")
                    st.rerun()
                else:
                    st.warning("Use um nome válido e não repetido.")
        with r3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            is_default = active_profile_id == config.get("default_profile_id")
            if st.button("Perfil padrão ✓" if is_default else "Definir como padrão", use_container_width=True, key="default_profile_v23", disabled=is_default):
                config["default_profile_id"] = active_profile_id
                salvar_config(config, force=True)
                st.toast("Perfil padrão atualizado.")
                st.rerun()

        st.markdown("**URL fixa para esta TV/perfil**")
        st.markdown(f'<div class="profile-url">?perfil={active_profile_id}&amp;iniciado=true</div>', unsafe_allow_html=True)
        st.caption("Use essa combinação de parâmetros ao fixar uma TV em um perfil específico.")

        if st.session_state.get("confirmar_exclusao_perfil_v23"):
            st.warning(f"Excluir o perfil **{perfil['nome']}** e todos os painéis dele?")
            x1, x2 = st.columns(2)
            with x1:
                if st.button("Cancelar", use_container_width=True, key="cancelar_excluir_perfil_v23"):
                    st.session_state["confirmar_exclusao_perfil_v23"] = False
                    st.rerun()
            with x2:
                if st.button("Confirmar exclusão", type="primary", use_container_width=True, key="confirmar_excluir_perfil_v23"):
                    del config["profiles"][active_profile_id]
                    if config.get("default_profile_id") == active_profile_id:
                        config["default_profile_id"] = next(iter(config["profiles"]))
                    next_id = config["default_profile_id"]
                    salvar_config(config, force=True)
                    st.session_state["confirmar_exclusao_perfil_v23"] = False
                    st.query_params["perfil"] = next_id
                    st.rerun()

    # Cabeçalho dos painéis
    header_l, header_m, header_r = st.columns([3.25, 1.35, 1])
    with header_l:
        st.markdown('<div class="section-title">Painéis e ordem de exibição</div>', unsafe_allow_html=True)
        st.caption("Os painéis ativos entram na rotação na ordem abaixo. Atualização automática e manter a página aberta são configurações independentes.")
    with header_m:
        view_options = ["compact", "detailed"]
        perfil["config_view"] = st.selectbox(
            "Visualização",
            view_options,
            index=view_options.index(perfil.get("config_view", "compact")),
            format_func=lambda x: "Compacta" if x == "compact" else "Detalhada",
            key=f"view_{active_profile_id}",
            help="Compacta recolhe as configurações avançadas. Detalhada deixa essas opções abertas.",
        )
    with header_r:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("＋ Adicionar painel", use_container_width=True, key="add_painel_v23"):
            paineis.append(painel_padrao(f"Novo Painel {len(paineis) + 1}", "", 20, True))
            salvar_config(config, force=True)
            st.toast("Painel adicionado.")
            st.rerun()

    pending_delete = st.session_state.get("painel_pendente_exclusao_v23")

    for i, painel in enumerate(paineis):
        pid = painel["id"]
        nome_cabecalho = html.escape(str(painel.get("nome") or "Painel sem nome"))
        ativo_badge = '<span class="badge badge-blue">ATIVO</span>' if painel.get("ativo", True) else '<span class="badge badge-gray">INATIVO</span>'
        f5_badge = '<span class="badge badge-blue">F5 ON</span>' if painel.get("reload_enabled", True) else '<span class="badge badge-gray">F5 OFF</span>'
        preserve_badge = '<span class="badge badge-green">MANTIDO ABERTO</span>' if (painel.get("preserve_session", False) or not painel.get("reload_enabled", True)) else ''

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="panel-headline">
                    <div class="panel-headline-left">
                        <span class="panel-number">{i+1:02d}</span>
                        <span class="panel-headline-name">{nome_cabecalho}</span>
                    </div>
                    <div class="panel-badges">{ativo_badge}{f5_badge}{preserve_badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            row = st.columns([0.46, 0.46, 1.05, 3.15, 1.0, 1.45, 1.0, 0.9])
            with row[0]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("▲", key=f"up_{pid}", help="Mover este painel para cima", disabled=i == 0, use_container_width=True):
                    paineis[i - 1], paineis[i] = paineis[i], paineis[i - 1]
                    salvar_config(config, force=True)
                    st.toast("Ordem atualizada.")
                    st.rerun()
            with row[1]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("▼", key=f"down_{pid}", help="Mover este painel para baixo", disabled=i == len(paineis)-1, use_container_width=True):
                    paineis[i + 1], paineis[i] = paineis[i], paineis[i + 1]
                    salvar_config(config, force=True)
                    st.toast("Ordem atualizada.")
                    st.rerun()
            with row[2]:
                painel["ativo"] = st.toggle(
                    "Exibir",
                    value=bool(painel.get("ativo", True)),
                    key=f"ativo_{pid}",
                    help="Liga ou desliga este painel na rotação. Desligado, ele continua cadastrado.",
                )
            with row[3]:
                painel["nome"] = st.text_input("Nome do painel", value=painel["nome"], key=f"nome_{pid}")
            with row[4]:
                painel["tempo"] = st.number_input(
                    "Tempo na tela", 5, 600, int(painel.get("tempo", 20)), 5, key=f"tempo_{pid}",
                    help="Quantidade de segundos que este painel ficará visível antes de passar para o próximo.",
                )
            with row[5]:
                painel["reload_enabled"] = st.toggle(
                    "Atualização",
                    value=bool(painel.get("reload_enabled", True)),
                    key=f"reload_{pid}",
                    help="Liga ou desliga a atualização automática (F5) deste painel. O estado também aparece no selo do cabeçalho.",
                )
            with row[6]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("⧉ Duplicar", key=f"dup_{pid}", help="Criar uma cópia deste painel", use_container_width=True):
                    clone = copy.deepcopy(painel)
                    clone["id"] = novo_id("p_")
                    clone["nome"] = f"{clone['nome']} - Cópia"
                    paineis.insert(i + 1, clone)
                    salvar_config(config, force=True)
                    st.toast("Painel duplicado.")
                    st.rerun()
            with row[7]:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑 Excluir", key=f"del_{pid}", help="Excluir este painel", use_container_width=True):
                    st.session_state["painel_pendente_exclusao_v23"] = pid
                    st.rerun()

            u1, u2, u3 = st.columns([6.0, 1.05, 1.2])
            with u1:
                painel["link"] = st.text_input("Endereço da página (URL)", value=painel["link"], key=f"link_{pid}", placeholder="https://...")
            with u2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if painel["link"].strip():
                    if url_valida(painel["link"]):
                        st.markdown('<span class="status-ok">✓ URL válida</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-warn">⚠ URL inválida</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="muted">URL pendente</span>', unsafe_allow_html=True)
            with u3:
                st.markdown("<div style='height:21px'></div>", unsafe_allow_html=True)
                if url_valida(painel.get("link", "")):
                    link_safe = html.escape(painel["link"], quote=True)
                    st.markdown(f'<a href="{link_safe}" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;color:#0E5285;font-size:12px;font-weight:700;border:1px solid #C7D9E7;padding:7px 10px;border-radius:8px;">Abrir página ↗</a>', unsafe_allow_html=True)

            # Configurações avançadas: abertas somente na visualização detalhada.
            with st.expander("Configurações avançadas", expanded=perfil.get("config_view") == "detailed"):
                a1, a2, a3, a4 = st.columns([1.1, 1.2, 1.1, 1.25])
                with a1:
                    painel["tipo"] = st.selectbox(
                        "Tipo do painel",
                        ["normal", "sim", "personalizado"],
                        index=["normal", "sim", "personalizado"].index(painel.get("tipo", "normal")),
                        format_func=lambda x: {"normal":"Normal", "sim":"SIM", "personalizado":"Personalizado"}[x],
                        key=f"tipo_{pid}",
                    )
                with a2:
                    if painel["reload_enabled"]:
                        painel["reload_strategy"] = st.selectbox(
                            "Quando atualizar",
                            ["on_show", "interval"],
                            index=["on_show", "interval"].index(painel.get("reload_strategy", "on_show")),
                            format_func=lambda x: "Ao exibir" if x == "on_show" else "Por intervalo",
                            key=f"strategy_{pid}",
                            help="Ao exibir: garante uma carga recente quando o painel entra na tela. Por intervalo: atualiza repetidamente conforme o tempo configurado.",
                        )
                    else:
                        st.selectbox("Quando atualizar", ["Desativado"], disabled=True, key=f"strategy_off_{pid}")
                with a3:
                    painel["reload_interval"] = st.number_input(
                        "Intervalo de atualização (s)", 5, 3600, int(painel.get("reload_interval", 60)), 5,
                        key=f"interval_{pid}", disabled=(not painel["reload_enabled"] or painel.get("reload_strategy") != "interval"),
                    )
                with a4:
                    if not painel["reload_enabled"]:
                        st.toggle(
                            "Manter painel aberto",
                            value=True,
                            key=f"preserve_auto_{pid}",
                            disabled=True,
                            help="Com F5 OFF, o painel é mantido aberto automaticamente para não recarregar quando voltar à tela.",
                        )
                    else:
                        painel["preserve_session"] = st.toggle(
                            "Manter painel aberto",
                            value=bool(painel.get("preserve_session", False)),
                            key=f"preserve_{pid}",
                            help="Mantém esta página carregada em segundo plano para preservar login, filtros ou posição, mesmo quando outro painel estiver visível.",
                        )
                if not painel["reload_enabled"]:
                    st.info("Com **F5 OFF**, este painel é mantido carregado automaticamente. Ao sair e voltar para ele, o monitoramento reutiliza o mesmo iframe e não executa F5.")
                elif painel["preserve_session"]:
                    st.markdown('<span class="badge badge-green">PAINEL MANTIDO ABERTO</span>', unsafe_allow_html=True)

            if pending_delete == pid:
                st.warning(f"Excluir o painel **{painel['nome']}**? Esta ação remove apenas este cadastro do perfil.")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("Cancelar", key=f"cancel_del_{pid}", use_container_width=True):
                        st.session_state["painel_pendente_exclusao_v23"] = None
                        st.rerun()
                with d2:
                    if st.button("Confirmar exclusão", key=f"confirm_del_{pid}", type="primary", use_container_width=True):
                        perfil["paineis"] = [p for p in paineis if p["id"] != pid]
                        st.session_state["painel_pendente_exclusao_v23"] = None
                        salvar_config(config, force=True)
                        st.toast("Painel excluído.")
                        st.rerun()

    # Salva somente se houve alteração efetiva.
    salvar_config(config)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Estabilidade e operação
    with st.container(border=True):
        st.markdown('<div class="section-title">Estabilidade e operação</div>', unsafe_allow_html=True)
        st.caption("Watchdog, pré-carregamento inteligente e reinício seguro para uso contínuo.")
        e1, e2, e3, e4 = st.columns([1.35, 1.0, 1.0, 1.0])
        with e1:
            allowed_hours = [0, 1, 2, 4, 6, 8, 12, 24]
            current_hours = perfil.get("horas_reload_geral", 0)
            if current_hours not in allowed_hours:
                current_hours = 0
            perfil["horas_reload_geral"] = st.selectbox(
                "Reinício completo",
                allowed_hours,
                index=allowed_hours.index(current_hours),
                format_func=lambda x: "Desativado" if x == 0 else ("A cada 1 hora" if x == 1 else f"A cada {x} horas"),
                key=f"reload_geral_{active_profile_id}",
            )
        with e2:
            perfil["preload_seconds"] = st.number_input(
                "Pré-carregar antes (s)", 0, 30, int(perfil.get("preload_seconds", 8)), 1,
                key=f"preload_{active_profile_id}",
                help="O próximo iframe só é criado perto da troca, reduzindo consumo de memória/CPU.",
            )
        with e3:
            perfil["watchdog_seconds"] = st.number_input(
                "Watchdog (s)", 30, 600, int(perfil.get("watchdog_seconds", 90)), 10,
                key=f"watchdog_{active_profile_id}",
                help="Se a rotação deixar de emitir sinais por esse tempo, o monitor tenta se recuperar automaticamente.",
            )
        with e4:
            perfil["auto_ocultar_controles"] = st.toggle(
                "Ocultar controles",
                value=bool(perfil.get("auto_ocultar_controles", True)),
                key=f"autohide_{active_profile_id}",
            )

    # Experiência e visual
    with st.container(border=True):
        st.markdown('<div class="section-title">Experiência e visual</div>', unsafe_allow_html=True)
        st.caption("Ajustes específicos para distância de visualização, posição da barra e modo TV.")
        v1, v2, v3, v4 = st.columns(4)
        with v1:
            perfil["modo_tv_padrao"] = st.toggle("Iniciar em Modo TV", value=bool(perfil.get("modo_tv_padrao", False)), key=f"tv_{active_profile_id}")
            perfil["show_status"] = st.toggle("Mostrar status", value=bool(perfil.get("show_status", True)), key=f"showstatus_{active_profile_id}")
        with v2:
            scales = [90, 100, 110, 125]
            perfil["ui_scale"] = st.selectbox("Escala da barra", scales, index=scales.index(perfil.get("ui_scale", 100)), format_func=lambda x: f"{x}%", key=f"scale_{active_profile_id}")
            perfil["show_clock"] = st.toggle("Mostrar relógio", value=bool(perfil.get("show_clock", True)), key=f"clock_{active_profile_id}")
        with v3:
            positions = ["top", "bottom"]
            perfil["toolbar_position"] = st.selectbox("Posição da barra", positions, index=positions.index(perfil.get("toolbar_position", "top")), format_func=lambda x: "Superior" if x == "top" else "Inferior", key=f"barpos_{active_profile_id}")
            perfil["show_dots"] = st.toggle("Mostrar indicadores", value=bool(perfil.get("show_dots", True)), key=f"dots_{active_profile_id}")
        with v4:
            trans = [0, 150, 220, 400]
            perfil["transition_ms"] = st.selectbox("Transição", trans, index=trans.index(perfil.get("transition_ms", 220)), format_func=lambda x: "Instantânea" if x == 0 else f"Fade {x} ms", key=f"transition_{active_profile_id}")

    salvar_config(config)

    # Backup/importação/diagnóstico
    with st.expander("Backup, importação, restauração e diagnóstico", expanded=False):
        b1, b2, b3 = st.columns(3)
        with b1:
            st.download_button(
                "Exportar configuração",
                data=json.dumps(config, ensure_ascii=False, indent=2),
                file_name=f"monitoramento_config_v{APP_VERSION.replace('.', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with b2:
            if BACKUP_PATH.exists() and st.button("Restaurar último backup", use_container_width=True, key="restore_backup_v23"):
                try:
                    restored = normalizar_config(json.loads(BACKUP_PATH.read_text(encoding="utf-8")))
                    st.session_state.config_v23 = restored
                    salvar_config(restored, force=True)
                    st.toast("Backup restaurado.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Falha ao restaurar backup: {exc}")
        with b3:
            if st.button("Restaurar perfil padrão SS", use_container_width=True, key="restore_profile_default_v23"):
                novo = copy.deepcopy(_DEFAULT_PROFILE)
                novo["id"] = active_profile_id
                novo["nome"] = perfil["nome"]
                # novos IDs evitam conflito com estados antigos do navegador
                for p in novo["paineis"]:
                    p["id"] = novo_id("p_")
                config["profiles"][active_profile_id] = novo
                salvar_config(config, force=True)
                st.toast("Perfil restaurado para a configuração padrão.")
                st.rerun()

        imported = st.file_uploader("Importar configuração JSON", type=["json"], key="import_v23")
        if imported is not None:
            try:
                raw_import = json.loads(imported.getvalue().decode("utf-8"))
                erros, avisos = validar_config_importada(raw_import)
                normalized_import = normalizar_config(raw_import) if not erros else None
                if normalized_import:
                    total_profiles = len(normalized_import["profiles"])
                    total_panels = sum(len(p["paineis"]) for p in normalized_import["profiles"].values())
                    total_active = sum(len(perfil_ativos(p)) for p in normalized_import["profiles"].values())
                    st.info(f"Prévia da importação: {total_profiles} perfil(is), {total_panels} painel(is), {total_active} painel(is) ativo(s) com URL válida.")
                for aviso in avisos[:8]:
                    st.warning(aviso)
                for erro in erros[:8]:
                    st.error(erro)
                if normalized_import and st.button("Confirmar importação", type="primary", use_container_width=True, key="confirm_import_v23"):
                    st.session_state.config_v23 = normalized_import
                    salvar_config(normalized_import, force=True)
                    st.query_params["perfil"] = normalized_import["default_profile_id"]
                    st.toast("Configuração importada.")
                    st.rerun()
            except Exception as exc:
                st.error(f"JSON inválido: {exc}")

        st.markdown("**Diagnóstico da configuração**")
        st.write(f"Versão: `{APP_VERSION}` / esquema `{CONFIG_VERSION}`")
        st.write(f"Perfil desta tela: `{perfil['nome']}` (`{active_profile_id}`)")
        st.write(f"Perfil padrão global: `{config['profiles'][config['default_profile_id']]['nome']}`")
        st.write(f"Painéis ativos com URL válida: `{len(ativos)}`")
        st.write(f"URLs inválidas ativas: `{urls_invalidas}`")
        st.write(f"Painéis mantidos abertos: `{preservados}`")
        st.write(f"Persistência local: `{CONFIG_PATH.name}` com gravação atômica + backup")
        st.info("Em hospedagens Streamlit com filesystem efêmero, o arquivo local pode ser recriado após redeploy/reinício da infraestrutura. O backup/exportação continua recomendado para mudanças importantes.")
        if st.session_state.get("config_corrompida_backup"):
            st.warning(f"Uma configuração corrompida foi preservada como `{st.session_state['config_corrompida_backup']}`.")
        if st.session_state.get("ultimo_erro_persistencia"):
            st.error(f"Último erro de persistência: {st.session_state['ultimo_erro_persistencia']}")

    with st.expander("Novidades desta versão", expanded=False):
        st.markdown(
            """
            **2.2 – Estabilidade e Operação:** perfil por URL/monitor, IDs permanentes, F5 temporário sem sobrescrever configuração, preservação independente de sessão, pré-carregamento inteligente, timer por horário-alvo, watchdog, status de conexão, reinício no fim do ciclo, diagnóstico expandido e gravação atômica com backup.

            **2.3 – Experiência e Visual:** modo compacto/detalhado, barra superior/inferior, escala para TV, indicadores/relógio opcionais, transição configurável, badges de estado e refinamento completo na paleta `#0E5285`.

            **2.4 – Primeiro Uso:** linguagem mais simples, guia inicial em 3 passos, resumo mais autoexplicativo, prévia da ordem de rotação, cards numerados, estados visuais claros, controles com tooltips, visualização compacta/detalhada e ação “Iniciar monitoramento” sempre acessível.

            **2.4.1 – Refinamento visual:** cor ativa dos controles alinhada ao azul #0E5285, campos dos cards redistribuídos para evitar cortes e remoção da indicação F5 duplicada na linha do painel.

            **2.4.2 – Correções operacionais:** F5 OFF agora mantém o iframe automaticamente em memória, evitando recarregar ao retornar ao painel; o botão Ajustes usa navegação robusta para sair do iframe e voltar à tela de configuração.
            """
        )

    st.markdown(f'<span class="version-pill">Painel de Monitoramento v{APP_VERSION}</span>', unsafe_allow_html=True)
    st.markdown("<div style='height:9px'></div>", unsafe_allow_html=True)

    if st.button("▶ Iniciar monitoramento", type="primary", use_container_width=True, key="start_bottom_v24"):
        iniciar_monitoramento_ux24()

    # Barra fixa: mantém a ação principal acessível mesmo em páginas com muitos painéis.
    fixed_ativos = perfil_ativos(perfil)
    fixed_invalid = [p for p in perfil.get("paineis", []) if p.get("ativo", True) and p.get("link", "").strip() and not url_valida(p.get("link", ""))]
    perfil_nome_safe = html.escape(str(perfil.get("nome", "Perfil")))
    if fixed_ativos and not fixed_invalid:
        fixed_action = f'<a class="ux24-start-link" href="?perfil={active_profile_id}&amp;iniciado=true" target="_self">▶ Iniciar monitoramento</a>'
    else:
        fixed_action = '<span class="ux24-start-disabled" title="Corrija os painéis antes de iniciar">▶ Iniciar monitoramento</span>'
    st.markdown(
        f"""
        <div class="ux24-fixed-bar">
            <div class="ux24-fixed-inner">
                <div class="ux24-fixed-copy"><strong>✓ Salvo automaticamente</strong><span> &nbsp;•&nbsp; Perfil: {perfil_nome_safe} &nbsp;•&nbsp; {len(fixed_ativos)} painel(is) ativo(s)</span></div>
                {fixed_action}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TELA 2 - APRESENTAÇÃO
# =========================================================
else:
    st.markdown(
        """
        <style>
            .block-container {max-width:100%!important;width:100%!important;height:100vh!important;padding:0!important;margin:0!important;overflow:hidden!important;}
            .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {overflow:hidden!important;height:100vh!important;}
            iframe[title="streamlit.components.v1.html"] {width:100%!important;height:100vh!important;display:block!important;border:0!important;}
            div[data-testid="stElementContainer"] {margin:0!important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    active_profile_id = perfil_id_da_url(config)
    perfil = perfil_por_id(config, active_profile_id)
    if perfil is None:
        st.session_state.iniciado = False
        st.query_params["iniciado"] = "false"
        st.error("Perfil não encontrado.")
        st.stop()

    paineis_ativos = perfil_ativos(perfil)
    if not paineis_ativos:
        st.session_state.iniciado = False
        st.query_params["iniciado"] = "false"
        st.warning("Não há painéis ativos com URL válida.")
        if st.button("Voltar para configurações"):
            st.rerun()
        st.stop()

    # Base64 evita injetar strings de usuário diretamente dentro do JavaScript.
    payload_b64 = b64_json({
        "panels": paineis_ativos,
        "profile": {"id": active_profile_id, "nome": perfil["nome"]},
        "settings": {
            "generalReloadMs": int(perfil.get("horas_reload_geral", 0)) * 3600 * 1000,
            "autoHide": bool(perfil.get("auto_ocultar_controles", True)),
            "kioskDefault": bool(perfil.get("modo_tv_padrao", False)),
            "preloadSeconds": int(perfil.get("preload_seconds", 8)),
            "watchdogSeconds": int(perfil.get("watchdog_seconds", 90)),
            "uiScale": int(perfil.get("ui_scale", 100)),
            "toolbarPosition": perfil.get("toolbar_position", "top"),
            "transitionMs": int(perfil.get("transition_ms", 220)),
            "showClock": bool(perfil.get("show_clock", True)),
            "showDots": bool(perfil.get("show_dots", True)),
            "showStatus": bool(perfil.get("show_status", True)),
        },
    })

    html_painel = r'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <style>
            :root{
                --blue:#0E5285;--blue-dark:#093D63;--blue-light:#54A3D8;--toolbar-h:42px;--progress-h:3px;--scale:1;--fade:220ms;
            }
            *{box-sizing:border-box}html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#fff;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
            #control-shell{position:fixed;left:0;width:100%;z-index:10000;transition:transform .18s ease,opacity .18s ease;transform-origin:center;}
            body.bar-top #control-shell{top:0} body.bar-bottom #control-shell{bottom:0}
            body.bar-top #control-shell.hidden{transform:translateY(calc(-1*(var(--toolbar-h) + var(--progress-h))));opacity:0;pointer-events:none}
            body.bar-bottom #control-shell.hidden{transform:translateY(calc(var(--toolbar-h) + var(--progress-h)));opacity:0;pointer-events:none}
            #toolbar{height:var(--toolbar-h);background:var(--blue);color:#fff;display:grid;grid-template-columns:minmax(220px,1.25fr) minmax(160px,.85fr) auto;align-items:center;gap:12px;padding:0 11px 0 14px;box-shadow:0 2px 7px rgba(0,0,0,.18);font-size:calc(12px * var(--scale))}
            .toolbar-left{min-width:0;display:flex;align-items:center;gap:8px;overflow:hidden;white-space:nowrap}.state-dot{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 2px rgba(255,255,255,.16);flex:0 0 auto}.state-dot.offline{background:#ef4444}.state-dot.recovering{background:#f59e0b}
            #panel-name{overflow:hidden;text-overflow:ellipsis;font-weight:780}#panel-order{color:#C9E0F1;font-size:.92em;flex-shrink:0}.toolbar-center{display:flex;align-items:center;justify-content:center;gap:9px;color:#EAF3FA;font-size:.92em}#dots{display:flex;gap:5px;align-items:center}.dot{width:7px;height:7px;border-radius:50%;border:1px solid rgba(255,255,255,.68);background:transparent;opacity:.8;cursor:pointer}.dot.active{background:#fff;opacity:1}
            .toolbar-right{display:flex;align-items:center;justify-content:flex-end;gap:4px}.btn{height:29px;min-width:30px;padding:0 8px;border-radius:6px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.08);color:#fff;cursor:pointer;font-size:.91em;font-weight:720;display:inline-flex;align-items:center;justify-content:center;gap:4px;user-select:none}.btn:hover{background:rgba(255,255,255,.18)}.btn.active{background:#1C70A9;border-color:#8CC4E8}.btn.off{background:#334155;border-color:#94A3B8}.btn.warn{background:#92400e;border-color:#fbbf24}.btn.pause{background:#7f1d1d;border-color:#f87171}.status-text{font-size:.88em;color:#DCEEFF;white-space:nowrap}.hidden-item{display:none!important}#clock{min-width:50px;text-align:right;font-weight:720;color:#DCEEFF}
            #progress-container{width:100%;height:var(--progress-h);background:var(--blue-dark);overflow:hidden}body.bar-bottom #progress-container{order:-1}#control-shell{display:flex;flex-direction:column}#progress{width:100%;height:100%;background:var(--blue-light);transform-origin:left;transform:scaleX(1)}
            #stage{position:fixed;left:0;width:100%;background:#fff;overflow:hidden;transition:top .18s ease,height .18s ease,bottom .18s ease}body.bar-top #stage{top:calc(var(--toolbar-h) + var(--progress-h));height:calc(100vh - var(--toolbar-h) - var(--progress-h))}body.bar-bottom #stage{top:0;height:calc(100vh - var(--toolbar-h) - var(--progress-h))}body.controls-hidden #stage{top:0!important;height:100vh!important;bottom:auto!important}
            .iframe-panel{position:absolute;inset:0;visibility:hidden;opacity:0;pointer-events:none;background:#fff;transition:opacity var(--fade) ease}.iframe-panel.active{visibility:visible;opacity:1;pointer-events:auto;z-index:2}.iframe-panel.preload{visibility:hidden;opacity:0;z-index:1}.iframe-panel iframe{width:100%;height:100%;border:0;display:block;background:#fff}
            .loading-overlay{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;background:#F5F9FC;color:#334155;z-index:3;font-size:13px;text-align:center;padding:20px}.loading-overlay small{color:#64748B;max-width:620px}.loading-overlay.hidden{display:none}.overlay-actions{display:flex;gap:8px;margin-top:5px}.overlay-btn{border:1px solid #C7D9E7;background:#fff;color:#0E5285;border-radius:7px;padding:7px 10px;cursor:pointer;font-weight:700}
            #diag{position:fixed;right:10px;width:min(520px,calc(100vw - 20px));max-height:60vh;z-index:10020;background:rgba(15,23,42,.97);color:#E2E8F0;border:1px solid rgba(255,255,255,.12);border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.3);padding:12px;display:none;overflow:auto;font-size:11px}body.bar-top #diag{top:50px}body.bar-bottom #diag{bottom:50px}#diag.open{display:block}#diag h4{margin:0 0 8px;color:#fff}.diag-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px 10px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,.12)}.diag-k{color:#94A3B8}.diag-v{color:#F8FAFC;text-align:right}.hint{color:#94A3B8;line-height:1.35;margin-bottom:8px}#diag-log{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;line-height:1.45}
            #restart-notice{position:fixed;left:50%;transform:translateX(-50%);z-index:10030;background:#0F172A;color:#fff;border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:7px 11px;font-size:11px;display:none}body.bar-top #restart-notice{bottom:10px}body.bar-bottom #restart-notice{top:10px}
            body.kiosk.controls-hidden{cursor:none}
            @media(max-width:980px){#toolbar{grid-template-columns:1fr auto}.toolbar-center{display:none}.btn .label{display:none}.btn{padding:0 7px}.status-text{display:none}}
        </style>
    </head>
    <body class="bar-top">
        <div id="control-shell">
            <div id="toolbar">
                <div class="toolbar-left"><span id="state-dot" class="state-dot"></span><span id="panel-name">Carregando...</span><span id="panel-order"></span><span id="network-status" class="status-text">Online</span></div>
                <div class="toolbar-center"><div id="dots"></div><span id="countdown">--:--</span><span id="runtime-status" class="status-text"></span></div>
                <div class="toolbar-right">
                    <button class="btn" onclick="mudarTela(-1)" title="Painel anterior (←)">←</button>
                    <button class="btn" id="pause-btn" onclick="alternarPausa()" title="Pausar/retomar (Espaço)">Ⅱ <span class="label">Pausar</span></button>
                    <button class="btn" onclick="mudarTela(1)" title="Próximo painel (→)">→</button>
                    <button class="btn" id="reload-toggle" onclick="alternarRecarregamentoTemporario()" title="Alteração temporária do F5; não altera a configuração salva">↻ <span class="label">F5</span></button>
                    <button class="btn" onclick="recarregarAgora()" title="Atualizar agora (R)">⟳</button>
                    <button class="btn" id="kiosk-btn" onclick="alternarModoTV()" title="Modo TV (K)">▣ <span class="label">TV</span></button>
                    <button class="btn" onclick="alternarTelaCheia()" title="Tela cheia (F)">⛶</button>
                    <button class="btn" onclick="toggleDiag()" title="Diagnóstico">i</button>
                    <button class="btn" onclick="irParaAjustes()" title="Ajustes">⚙</button>
                    <span id="clock"></span>
                </div>
            </div>
            <div id="progress-container"><div id="progress"></div></div>
        </div>
        <div id="stage"></div>
        <div id="restart-notice"></div>
        <div id="diag">
            <h4>Diagnóstico do monitoramento</h4>
            <div class="diag-grid">
                <span class="diag-k">Perfil</span><span class="diag-v" id="d-profile"></span>
                <span class="diag-k">Tempo ativo</span><span class="diag-v" id="d-uptime"></span>
                <span class="diag-k">Frames em memória</span><span class="diag-v" id="d-frames"></span>
                <span class="diag-k">Trocas de painel</span><span class="diag-v" id="d-switches"></span>
                <span class="diag-k">F5 realizados</span><span class="diag-v" id="d-reloads"></span>
                <span class="diag-k">Watchdog</span><span class="diag-v" id="d-watchdog"></span>
                <span class="diag-k">Última troca</span><span class="diag-v" id="d-last-switch"></span>
                <span class="diag-k">Conexão</span><span class="diag-v" id="d-network"></span>
            </div>
            <div class="hint">Sites de outros domínios podem bloquear iframe por X-Frame-Options/CSP. O evento de carga confirma apenas que o navegador concluiu a navegação do iframe; não garante que o conteúdo interno esteja operacional.</div>
            <div id="diag-log"></div>
        </div>

        <script>
            const PAYLOAD_B64 = '__PAYLOAD_B64__';
            const decodePayload = (s) => JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(s), c => c.charCodeAt(0))));
            const payload = decodePayload(PAYLOAD_B64);
            const panels = payload.panels;
            const profile = payload.profile;
            const settings = payload.settings;

            document.documentElement.style.setProperty('--scale', String(settings.uiScale / 100));
            document.documentElement.style.setProperty('--fade', `${settings.transitionMs}ms`);
            document.body.classList.toggle('bar-top', settings.toolbarPosition !== 'bottom');
            document.body.classList.toggle('bar-bottom', settings.toolbarPosition === 'bottom');

            let index = 0;
            let paused = false;
            let pauseRemainingMs = 0;
            let targetEndMs = 0;
            let timer = null;
            let intervalReloadTimer = null;
            let preloadTimer = null;
            let hideTimer = null;
            let watchdogTimer = null;
            let kioskMode = false;
            let pool = new Map();
            let logs = [];
            let runtimeReloadOverrides = {}; // nunca persistido: nova sessão = configuração salva
            let pendingGeneralReload = false;
            let appStartedAt = Date.now();
            let lastHeartbeat = Date.now();
            let lastSwitchAt = Date.now();
            let switchCount = 0;
            let reloadCount = 0;
            let watchdogRecoveries = 0;
            let visibilityHiddenAt = null;

            const stage = document.getElementById('stage');
            const controlShell = document.getElementById('control-shell');
            const panelName = document.getElementById('panel-name');
            const panelOrder = document.getElementById('panel-order');
            const countdown = document.getElementById('countdown');
            const runtimeStatus = document.getElementById('runtime-status');
            const progress = document.getElementById('progress');
            const pauseBtn = document.getElementById('pause-btn');
            const reloadToggle = document.getElementById('reload-toggle');
            const kioskBtn = document.getElementById('kiosk-btn');
            const clock = document.getElementById('clock');
            const dots = document.getElementById('dots');
            const diag = document.getElementById('diag');
            const diagLog = document.getElementById('diag-log');
            const networkStatus = document.getElementById('network-status');
            const stateDot = document.getElementById('state-dot');
            const restartNotice = document.getElementById('restart-notice');

            const indexKey = `monitor_v23_panel_${profile.id}`;
            const savedPanelId = localStorage.getItem(indexKey);
            if (savedPanelId) {
                const found = panels.findIndex(p => p.id === savedPanelId);
                if (found >= 0) index = found;
            }

            if (!settings.showClock) clock.classList.add('hidden-item');
            if (!settings.showDots) dots.classList.add('hidden-item');
            if (!settings.showStatus) { networkStatus.classList.add('hidden-item'); runtimeStatus.classList.add('hidden-item'); }

            function nowStamp(){ return new Date().toLocaleTimeString('pt-BR',{hour12:false}); }
            function log(msg){ logs.unshift(`${nowStamp()}  ${msg}`); logs=logs.slice(0,120); diagLog.textContent=logs.join('\n'); updateDiag(); }
            function escapeHtml(s){ return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
            function formatDuration(ms){ const sec=Math.max(0,Math.floor(ms/1000)); const h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60),s=sec%60; return h?`${h}h ${String(m).padStart(2,'0')}m`:m?`${m}m ${String(s).padStart(2,'0')}s`:`${s}s`; }
            function formatCountdown(ms){ const sec=Math.max(0,Math.ceil(ms/1000)); const m=Math.floor(sec/60),s=sec%60; return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }
            function nextIndex(){ return (index+1)%panels.length; }
            function getPanelById(id){ return panels.find(p=>p.id===id); }
            function effectiveReload(p){ return typeof runtimeReloadOverrides[p.id]==='boolean' ? runtimeReloadOverrides[p.id] : !!p.reload_enabled; }
            function setState(kind){ stateDot.classList.remove('offline','recovering'); if(kind==='offline')stateDot.classList.add('offline'); if(kind==='recovering')stateDot.classList.add('recovering'); }

            function showOverlayActions(item,message){
                item.overlay.classList.remove('hidden');
                item.overlay.innerHTML = `<strong>${escapeHtml(message)}</strong><small>Verifique conexão, sessão do sistema ou bloqueio de iframe.</small><div class="overlay-actions"><button class="overlay-btn" data-action="retry">Tentar novamente</button><button class="overlay-btn" data-action="skip">Pular painel</button></div>`;
                item.overlay.querySelector('[data-action="retry"]').onclick=()=>reloadItem(item,true);
                item.overlay.querySelector('[data-action="skip"]').onclick=()=>mudarTela(1);
            }

            function createPanelFrame(i,role='preload'){
                const p=panels[i]; if(!p)return null;
                if(pool.has(p.id))return pool.get(p.id);
                const container=document.createElement('div'); container.className=`iframe-panel ${role}`; container.dataset.panelId=p.id;
                const overlay=document.createElement('div'); overlay.className='loading-overlay'; overlay.innerHTML=`<strong>Carregando ${escapeHtml(p.nome)}...</strong><small>Preparando o painel de monitoramento.</small>`;
                const iframe=document.createElement('iframe'); iframe.allow='fullscreen'; iframe.referrerPolicy='no-referrer-when-downgrade';
                const item={container,iframe,overlay,panel:p,createdAt:Date.now(),loadedAt:0,loadTimeout:null};
                iframe.addEventListener('load',()=>{ clearTimeout(item.loadTimeout); item.loadedAt=Date.now(); overlay.classList.add('hidden'); log(`Navegação concluída: ${p.nome}`); });
                container.appendChild(iframe); container.appendChild(overlay); stage.appendChild(container); pool.set(p.id,item);
                iframe.src=p.link;
                item.loadTimeout=setTimeout(()=>{ if(!overlay.classList.contains('hidden')){ showOverlayActions(item,`O carregamento de ${p.nome} está demorando.`); log(`Aviso de carregamento: ${p.nome}`); } },18000);
                return item;
            }

            function reloadItem(item,manual=false){
                if(!item)return;
                clearTimeout(item.loadTimeout);
                item.overlay.classList.remove('hidden');
                item.overlay.innerHTML=`<strong>Atualizando ${escapeHtml(item.panel.nome)}...</strong><small>${manual?'Atualização manual solicitada.':'Atualização automática do painel.'}</small>`;
                item.iframe.src=item.panel.link;
                item.loadedAt=0; reloadCount++; lastHeartbeat=Date.now();
                item.loadTimeout=setTimeout(()=>showOverlayActions(item,`A atualização de ${item.panel.nome} está demorando.`),18000);
                log(`${manual?'F5 manual':'F5 automático'}: ${item.panel.nome}`);
            }

            function cleanupPool(){
                const currentId=panels[index].id;
                for(const [id,item] of pool.entries()){
                    const p=getPanelById(id);
                    const mustKeep=id===currentId || (p && (p.preserve_session===true || effectiveReload(p)===false));
                    const isNextPreloaded=id===panels[nextIndex()].id && item.container.classList.contains('preload');
                    if(!mustKeep && !isNextPreloaded){ item.container.remove(); pool.delete(id); log(`Liberado da memória: ${item.panel.nome}`); }
                }
            }

            function showCurrent(){
                const current=panels[index];
                let item=createPanelFrame(index,'active');
                for(const [id,it] of pool.entries()){ it.container.classList.remove('active','preload'); if(id===current.id)it.container.classList.add('active'); else it.container.classList.add('preload'); }
                // Para estratégia on_show, evita F5 duplicado se o pré-carregamento acabou de ocorrer.
                if(effectiveReload(current) && current.reload_strategy==='on_show'){
                    const freshWindow=Math.max(3000,(settings.preloadSeconds+3)*1000);
                    if(item.loadedAt && Date.now()-item.loadedAt>freshWindow) reloadItem(item,false);
                }
                cleanupPool();
            }

            function schedulePreload(){
                clearTimeout(preloadTimer); preloadTimer=null;
                if(panels.length<2 || settings.preloadSeconds<=0)return;
                const msUntilPreload=Math.max(0,targetEndMs-Date.now()-settings.preloadSeconds*1000);
                preloadTimer=setTimeout(()=>{
                    if(paused)return;
                    const ni=nextIndex(); const np=panels[ni];
                    if(!pool.has(np.id)){ createPanelFrame(ni,'preload'); log(`Pré-carregado: ${np.nome}`); }
                },msUntilPreload);
            }

            function renderDots(){ dots.innerHTML=''; panels.forEach((p,i)=>{ const d=document.createElement('span'); d.className='dot'+(i===index?' active':''); d.title=p.nome; d.onclick=()=>{index=i;afterIndexChange('Indicador');}; dots.appendChild(d); }); }
            function renderReloadButton(){ const p=panels[index], on=effectiveReload(p), overridden=typeof runtimeReloadOverrides[p.id]==='boolean'; reloadToggle.classList.toggle('active',on); reloadToggle.classList.toggle('off',!on); reloadToggle.innerHTML=on?`↻ <span class="label">F5 ON${overridden?'*':''}</span>`:`▣ <span class="label">F5 OFF${overridden?'*':''}</span>`; reloadToggle.title='F5 temporário nesta apresentação. * indica valor diferente da configuração salva.'; }
            function updateHeader(){ const p=panels[index]; panelName.textContent=p.nome; panelOrder.textContent=`${index+1}/${panels.length}`; renderDots(); renderReloadButton(); localStorage.setItem(indexKey,p.id); }

            function stopTimers(){ clearInterval(timer); clearInterval(intervalReloadTimer); clearTimeout(preloadTimer); timer=null; intervalReloadTimer=null; preloadTimer=null; }
            function setupIntervalReload(){ clearInterval(intervalReloadTimer); intervalReloadTimer=null; const p=panels[index]; if(!effectiveReload(p)||p.reload_strategy!=='interval')return; const every=Math.max(5,parseInt(p.reload_interval||60,10)); intervalReloadTimer=setInterval(()=>{ if(!paused && panels[index].id===p.id && effectiveReload(p)){ const item=pool.get(p.id)||createPanelFrame(index,'active'); reloadItem(item,false); } },every*1000); runtimeStatus.textContent=`F5 ${every}s`; }

            function startTimerWith(ms){
                clearInterval(timer); if(paused)return;
                targetEndMs=Date.now()+ms; lastHeartbeat=Date.now();
                progress.style.transition='none'; progress.style.transform='scaleX(1)';
                requestAnimationFrame(()=>requestAnimationFrame(()=>{ progress.style.transition=`transform ${ms}ms linear`; progress.style.transform='scaleX(0)'; }));
                timer=setInterval(()=>{
                    if(paused)return;
                    const remaining=targetEndMs-Date.now(); countdown.textContent=formatCountdown(remaining); lastHeartbeat=Date.now();
                    if(remaining<=0){ clearInterval(timer); mudarTela(1); }
                },250);
                schedulePreload(); setupIntervalReload();
            }

            function restartTimer(){ const total=Math.max(5,parseInt(panels[index].tempo||20,10))*1000; countdown.textContent=formatCountdown(total); startTimerWith(total); }

            function afterIndexChange(reason='Troca'){
                if(pendingGeneralReload){ reloadApplication(); return; }
                showCurrent(); updateHeader(); restartTimer(); lastSwitchAt=Date.now(); switchCount++; lastHeartbeat=Date.now(); log(`${reason}: ${panels[index].nome}`); updateDiag();
            }

            function mudarTela(direction){ if(!panels.length)return; index=(index+direction+panels.length)%panels.length; afterIndexChange(direction>0?'Próximo painel':'Painel anterior'); }

            function alternarPausa(){
                paused=!paused;
                if(paused){ pauseRemainingMs=Math.max(1000,targetEndMs-Date.now()); stopTimers(); pauseBtn.classList.add('pause'); pauseBtn.innerHTML='▶ <span class="label">Retomar</span>'; countdown.textContent='PAUSA'; progress.style.transition='none'; runtimeStatus.textContent='Pausado'; log('Rotação pausada'); }
                else { pauseBtn.classList.remove('pause'); pauseBtn.innerHTML='Ⅱ <span class="label">Pausar</span>'; runtimeStatus.textContent=''; startTimerWith(pauseRemainingMs||Math.max(5,panels[index].tempo)*1000); log('Rotação retomada'); }
            }

            function alternarRecarregamentoTemporario(){ const p=panels[index]; const current=effectiveReload(p); runtimeReloadOverrides[p.id]=!current; renderReloadButton(); setupIntervalReload(); log(`F5 temporário ${!current?'ON':'OFF'}: ${p.nome}`); }
            function recarregarAgora(){ const p=panels[index]; const item=pool.get(p.id)||createPanelFrame(index,'active'); reloadItem(item,true); }
            function alternarTelaCheia(){ if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(()=>{});}else if(document.exitFullscreen){document.exitFullscreen().catch(()=>{});} }

            function showControls(){ controlShell.classList.remove('hidden'); document.body.classList.remove('controls-hidden'); document.body.style.cursor=''; clearTimeout(hideTimer); if(settings.autoHide||kioskMode)hideTimer=setTimeout(hideControls,kioskMode?2200:4300); }
            function hideControls(){ if(!(settings.autoHide||kioskMode))return; controlShell.classList.add('hidden'); document.body.classList.add('controls-hidden'); if(kioskMode)document.body.style.cursor='none'; }
            function alternarModoTV(force=null){ kioskMode=force===null?!kioskMode:!!force; document.body.classList.toggle('kiosk',kioskMode); kioskBtn.classList.toggle('active',kioskMode); kioskBtn.innerHTML=kioskMode?'▣ <span class="label">TV ON</span>':'▣ <span class="label">TV</span>'; if(kioskMode&&!document.fullscreenElement)document.documentElement.requestFullscreen().catch(()=>{}); showControls(); log(`Modo TV ${kioskMode?'ativado':'desativado'}`); }
            function toggleDiag(){ diag.classList.toggle('open'); showControls(); updateDiag(); }

            function buildAppUrl(iniciado){
                const started = iniciado ? 'true' : 'false';

                // document.referrer normalmente aponta para a página principal do Streamlit
                // e pode ser lido mesmo quando o componente está em um iframe isolado.
                try{
                    if(document.referrer){
                        const u=new URL(document.referrer);
                        u.searchParams.set('iniciado',started);
                        u.searchParams.set('perfil',profile.id);
                        return u.toString();
                    }
                }catch(e){}

                // Fallback para apps publicados na raiz do domínio (caso do Streamlit Cloud).
                return `/?perfil=${encodeURIComponent(profile.id)}&iniciado=${started}`;
            }

            function navegarAplicacao(iniciado){
                const target=buildAppUrl(iniciado);

                // Não tenta ler window.parent.location.href, pois isso pode gerar
                // SecurityError dentro do iframe do Streamlit. Apenas navega o ancestral.
                try{
                    window.parent.location.href=target;
                    return;
                }catch(e){}

                try{
                    window.top.location.href=target;
                    return;
                }catch(e){}

                try{
                    window.open(target,'_top');
                    return;
                }catch(e){}

                window.location.href=target;
            }

            function irParaAjustes(){
                log('Abrindo ajustes');
                navegarAplicacao(false);
            }

            function reloadApplication(){
                navegarAplicacao(true);
            }

            function updateClock(){ const d=new Date(); clock.textContent=d.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}); }
            function updateNetwork(){ const online=navigator.onLine; networkStatus.textContent=online?'Online':'Sem conexão'; setState(online?'online':'offline'); document.getElementById('d-network').textContent=online?'Online':'Offline'; if(online)log('Conexão restabelecida'); }
            window.addEventListener('online',updateNetwork); window.addEventListener('offline',updateNetwork);

            function updateDiag(){
                document.getElementById('d-profile').textContent=profile.nome;
                document.getElementById('d-uptime').textContent=formatDuration(Date.now()-appStartedAt);
                document.getElementById('d-frames').textContent=String(pool.size);
                document.getElementById('d-switches').textContent=String(switchCount);
                document.getElementById('d-reloads').textContent=String(reloadCount);
                document.getElementById('d-watchdog').textContent=`${watchdogRecoveries} recuperação(ões)`;
                document.getElementById('d-last-switch').textContent=new Date(lastSwitchAt).toLocaleTimeString('pt-BR',{hour12:false});
                document.getElementById('d-network').textContent=navigator.onLine?'Online':'Offline';
            }

            function startWatchdog(){
                clearInterval(watchdogTimer);
                watchdogTimer=setInterval(()=>{
                    if(paused)return;
                    const elapsed=Date.now()-lastHeartbeat;
                    if(elapsed>settings.watchdogSeconds*1000){
                        watchdogRecoveries++; setState('recovering'); log(`Watchdog: ausência de atividade por ${Math.round(elapsed/1000)}s. Recuperando rotação.`);
                        stopTimers(); showCurrent(); updateHeader(); restartTimer(); lastHeartbeat=Date.now();
                        setTimeout(()=>setState(navigator.onLine?'online':'offline'),1500);
                    }
                    updateDiag();
                },10000);
            }

            document.addEventListener('visibilitychange',()=>{
                if(document.hidden){ visibilityHiddenAt=Date.now(); log('Aba em segundo plano'); }
                else { const away=visibilityHiddenAt?Date.now()-visibilityHiddenAt:0; visibilityHiddenAt=null; log(`Aba retomada após ${Math.round(away/1000)}s`); if(!paused && Date.now()>=targetEndMs)mudarTela(1); else lastHeartbeat=Date.now(); }
            });

            document.addEventListener('mousemove',showControls,{passive:true}); document.addEventListener('touchstart',showControls,{passive:true});
            document.addEventListener('keydown',(e)=>{ if(e.key==='ArrowLeft')mudarTela(-1);else if(e.key==='ArrowRight')mudarTela(1);else if(e.code==='Space'){e.preventDefault();alternarPausa();}else if(e.key.toLowerCase()==='f')alternarTelaCheia();else if(e.key.toLowerCase()==='r')recarregarAgora();else if(e.key.toLowerCase()==='k')alternarModoTV(); });

            if(settings.generalReloadMs>0){ setTimeout(()=>{ pendingGeneralReload=true; restartNotice.style.display='block'; restartNotice.textContent='Reinício programado: a aplicação será reiniciada ao fim do painel atual.'; runtimeStatus.textContent='Reinício pendente'; log('Reinício geral aguardando o fim do painel atual'); },settings.generalReloadMs); }

            updateClock(); setInterval(updateClock,1000); setInterval(updateDiag,1000); updateNetwork(); startWatchdog();
            log(`Aplicação iniciada - perfil ${profile.nome}`); log(`Painéis ativos: ${panels.length}`); afterIndexChange('Inicial'); showControls();
            if(settings.kioskDefault)setTimeout(()=>alternarModoTV(true),600);
        </script>
    </body>
    </html>
    '''
    html_painel = html_painel.replace("__PAYLOAD_B64__", payload_b64)
    components.html(html_painel, height=960, scrolling=False)
