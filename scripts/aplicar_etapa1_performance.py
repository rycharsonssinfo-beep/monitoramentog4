#!/usr/bin/env python3
"""Etapa 1 (v3.52.0) — patch idempotente do main.py, com validação de sintaxe.

O script só atua na versão 3.51.0 e falha se algum trecho mudou.
Nenhum segredo, configuração, tabela, permissão ou URL de sistema é alterado.
"""
from pathlib import Path
import os

APP = Path(__file__).resolve().parents[1] / "main.py"
source = APP.read_text(encoding="utf-8")
if 'APP_VERSION = "3.52.0"' in source:
    for marker in ("_portal_sync_pool_v352", "_iframe_probe_pool_v352", "ss_monitor_fast_start_bridge_v352"):
        if marker not in source:
            raise SystemExit(f"Versão 3.52.0 incompleta: {marker}")
    print("Etapa 1 já aplicada.")
    raise SystemExit(0)
if 'APP_VERSION = "3.51.0"' not in source:
    raise SystemExit("Versão base inesperada. Patch recusado para evitar sobrescrita.")
changes = []

def replace(old, new, label):
    global source
    if source.count(old) != 1:
        raise RuntimeError(f"Âncora incompatível em {label}: {source.count(old)} ocorrências")
    source = source.replace(old, new, 1)
    changes.append(label)

def replace_range(start, end, replacement, label):
    global source
    i = source.find(start)
    j = source.find(end, i + len(start))
    if i == -1 or j == -1:
        raise RuntimeError(f"Faixa incompatível: {label}")
    source = source[:i] + replacement + source[j:]
    changes.append(label)

replace('APP_VERSION = "3.51.0"', 'APP_VERSION = "3.52.0"', "versão")

replace(
    '        user = _monitor_auth_current_user(force=True)\n'
    '    except Exception:\n'
    '        st.error("Não foi possível verificar sua conta no Supabase. Faça login novamente.")',
    '        # Cache por token; revalida identidade no Supabase após 30 segundos.\n'
    '        user = _monitor_auth_current_user()\n'
    '    except Exception:\n'
    '        st.error("Não foi possível verificar sua conta no Supabase. Faça login novamente.")',
    "reaproveitar verificação Auth",
)

replace(
    '''def _auth_login(email, password):
    return _auth_request(
        "/auth/v1/token?grant_type=password",
        method="POST",
        payload={"email": email.strip(), "password": password},
    )''',
    '''def _auth_login(email, password):
    started = time.perf_counter()
    try:
        return _auth_request(
            "/auth/v1/token?grant_type=password",
            method="POST",
            payload={"email": email.strip(), "password": password},
        )
    finally:
        # Registrar somente tempo; nunca guardar senha, e-mail ou tokens no diagnóstico.
        st.session_state["_monitor_perf_login_http_ms_v352"] = round(
            (time.perf_counter() - started) * 1000
        )''',
    "medição de login",
)

portal_code = '''@st.cache_resource(show_spinner=False)
def _portal_sync_pool_v352():
    return {"lock": threading.Lock(),
            "executor": ThreadPoolExecutor(max_workers=1, thread_name_prefix="ss_portal"),
            "jobs": {}}


def _portal_sync_nonblocking_v352(email, senha, days, interval):
    state = _portal_sync_pool_v352()
    # Identificador irreversível da configuração, sem armazenamento de senha em chave aberta.
    key = hashlib.sha256((email + chr(0) + senha + chr(0) + str(days)).encode("utf-8")).hexdigest()
    with state["lock"]:
        now = time.monotonic()
        jobs = state["jobs"]
        job = jobs.get(key)
        if job is None or (job["future"].done() and now - job["started"] >= interval * 60):
            job = {"future": state["executor"].submit(_portal_sync_data, email, senha, days),
                   "started": now}
            jobs[key] = job
        if len(jobs) > 16:
            for oldkey, oldjob in list(jobs.items()):
                if oldkey != key and oldjob["future"].done():
                    jobs.pop(oldkey, None)
                if len(jobs) <= 12:
                    break
    return job["future"].result() if job["future"].done() else None


'''
replace(
    "def sincronizar_portal_ticker(ticker, force=False):",
    portal_code + "def sincronizar_portal_ticker(ticker, force=False):",
    "pool de sincronização externa",
)
replace(
    '        news, agenda = _portal_sync_data(email, senha, int(ticker.get("portal_agenda_days", 7)))\n'
    '        cache["news"] = news',
    '''        days = int(ticker.get("portal_agenda_days", 7))
        # Atualização automática não bloqueia a interface; ação manual continua síncrona.
        result = (_portal_sync_data(email, senha, days) if force
                  else _portal_sync_nonblocking_v352(email, senha, days, interval))
        if result is None:
            return False, "pending"
        news, agenda = result
        cache["news"] = copy.deepcopy(news)''',
    "sincronização assíncrona do portal",
)
replace('        cache["agenda"] = agenda\n        cache["last_sync"]',
        '        cache["agenda"] = copy.deepcopy(agenda)\n        cache["last_sync"]',
        "cópia isolada do resultado do portal",
)

iframe_code = '''@st.cache_resource(show_spinner=False)
def _iframe_probe_pool_v352():
    return {"lock": threading.Lock(),
            "executor": ThreadPoolExecutor(max_workers=6, thread_name_prefix="ss_iframe"),
            "checks": {}}


'''
replace(
    "def verificar_paineis_iframe(paineis):",
    iframe_code + "def verificar_paineis_iframe(paineis):",
    "pool de testes de URLs",
)

replace_range(
    "    if automaticos:\n        workers = min(6, max(1, len(automaticos)))",
    '    for p in paineis:\n        if p.get("tipo") in ("g4flex", "portais")',
    '''    if automaticos:
        state = _iframe_probe_pool_v352()
        pending = {}
        with state["lock"]:
            now = time.monotonic()
            checks = state["checks"]
            for p in automaticos:
                url = str(p.get("link") or "").strip()
                entry = checks.get(url)
                if entry is None or (entry["future"].done() and now - entry["started"] >= 300):
                    entry = {"future": state["executor"].submit(detectar_bloqueio_iframe, url),
                             "started": now}
                    checks[url] = entry
                pending[p.get("id")] = entry["future"]
            if len(checks) > 256:
                active = {str(p.get("link") or "").strip() for p in automaticos}
                for url, entry in list(checks.items()):
                    if url not in active and entry["future"].done():
                        checks.pop(url, None)
                    if len(checks) <= 200:
                        break
        for pid, future in pending.items():
            if future.done():
                try:
                    resultados[pid] = future.result()
                except Exception as exc:
                    resultados[pid] = {"blocked": False, "status": "unknown",
                                        "reason": f"Falha na verificação: {str(exc)[:160]}"}
            else:
                resultados[pid] = {"blocked": False, "status": "pending",
                                    "reason": "Verificação de compatibilidade em segundo plano."}

''',
    "testes de URLs não bloqueantes",
)
replace(
    "def _sim_mapas_municipais_ipece_2026():",
    "@st.cache_data(ttl=3600, show_spinner=False)\ndef _sim_mapas_municipais_ipece_2026():",
    "cache do mapa estático",
)
replace(
    "_render_login_gate()\n_monitor_change_temporary_password()\n"
    "_monitor_profile, _monitor_account_active = _monitor_access_role()",
    '''_monitor_perf_gate_t0_v352 = time.perf_counter()
_render_login_gate()
_monitor_change_temporary_password()
_monitor_profile, _monitor_account_active = _monitor_access_role()
st.session_state["_monitor_perf_gate_ms_v352"] = round(
    (time.perf_counter() - _monitor_perf_gate_t0_v352) * 1000
)''',
    "medição de autorização",
)
replace(
    "    ativos = perfil_ativos(perfil)\n    tempo_total =",
    "    ativos = perfil_ativos(perfil)\n"
    "    verificar_paineis_iframe(ativos)  # Pré-aquecimento sem bloquear a configuração.\n"
    "    tempo_total =",
    "pré-aquecimento de URLs",
)
replace(
    "        salvar_config(config)\n        st.session_state.iniciado = True",
    "        salvar_config(config)\n"
    "        st.session_state['_monitor_perf_start_t0_v352'] = time.perf_counter()\n"
    "        st.session_state.iniciado = True",
    "medição de entrada no monitor",
)
replace(
    '''footer_cta = f'<a class="cfg-footer-start" href="?perfil=''', 
    '''footer_cta = f'<a class="cfg-footer-start" data-ss-fast-start="1" href="?perfil=''', 
    "marcador do botão iniciar",
)

footer = next((line for line in source.splitlines()
               if "st.markdown(f'''<a \"cfg-back-top\"" in line
               or "st.markdown(f'''<a class=\"cfg-back-top\"" in line), None)
if not footer:
    raise RuntimeError("Não foi encontrado o rodapé da configuração")

bridge = """
    # Ponte no DOM principal, preservando a sessão. O href segue como fallback.
    if fixed_ativos and not fixed_invalid and hasattr(st.components, "v2"):
        start_bridge = st.components.v2.component(
            "ss_monitor_fast_start_v352",
            html='<span aria-hidden="true"></span>',
            css=":host{display:none!important;height:0!important}",
            js=r\"\"\"
            export default function(component) {
                const {setTriggerValue} = component;
                const onStart = (event) => {
                    const target = event.target;
                    const link = target && target.closest
                        ? target.closest('a[data-ss-fast-start="1"]') : null;
                    if (!link) return;
                    event.preventDefault();
                    event.stopPropagation();
                    setTriggerValue('start', String(Date.now()) + ':' +
                        Math.random().toString(36).slice(2));
                };
                document.addEventListener('click', onStart, true);
                return () => document.removeEventListener('click', onStart, true);
            }
            \"\"\",
        )
        start_result = start_bridge(
            key="ss_monitor_fast_start_bridge_v352",
            on_start_change=lambda: None,
        )
        start_event = str(getattr(start_result, "start", "") or "")
        if start_event and start_event != st.session_state.get("_monitor_last_fast_start_v352"):
            st.session_state["_monitor_last_fast_start_v352"] = start_event
            iniciar_monitoramento_ux24()
"""
replace(footer, footer + "\n" + bridge.rstrip("\n"), "ponte de início sem reload")
replace(
    "    iframe_checks = verificar_paineis_iframe(paineis_ativos)",
    '''    _monitor_perf_iframe_t0_v352 = time.perf_counter()
    iframe_checks = verificar_paineis_iframe(paineis_ativos)
    st.session_state["_monitor_perf_iframe_ms_v352"] = round(
        (time.perf_counter() - _monitor_perf_iframe_t0_v352) * 1000
    )''',
    "medição de checagens",
)
replace(
    "    components.html(html_painel, height=960, scrolling=False)",
    '''    components.html(html_painel, height=960, scrolling=False)
    _monitor_perf_start_t0 = st.session_state.pop("_monitor_perf_start_t0_v352", None)
    if _monitor_perf_start_t0 is not None:
        st.session_state["_monitor_perf_start_python_ms_v352"] = round(
            (time.perf_counter() - _monitor_perf_start_t0) * 1000
        )''',
    "medição de preparação do monitor",
)
compile(source, str(APP), "exec")
tmp = APP.with_suffix(".py.etapa1.tmp")
tmp.write_text(source, encoding="utf-8")
os.replace(tmp, APP)
print("Etapa 1 aplicada: " + ", ".join(changes))
