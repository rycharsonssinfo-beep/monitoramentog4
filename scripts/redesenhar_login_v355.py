#!/usr/bin/env python3
"""Redesenho da tela de login do Monitor S&S v3.55, sem modificar autenticação."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/"main.py"
MARKER="login-v355-layout-marker"

NEW_CSS = '''def _auth_login_css():
    st.markdown(
        """
        <style>
        /* Base dos formulários públicos de autenticação */
        header[data-testid="stHeader"] {background:transparent!important}
        div[data-testid="stToolbar"] {visibility:hidden}
        section[data-testid="stSidebar"] {display:none!important}
        :root,html,body,.stApp{color-scheme:light!important}
        .stApp{color:#172F4E!important;background:
          radial-gradient(ellipse at -4% -8%,rgba(48,208,235,.27),transparent 29%),
          radial-gradient(ellipse at 100% 100%,rgba(3,126,211,.19),transparent 35%),
          linear-gradient(140deg,#E9F7FC 0%,#FFFFFF 46%,#F1F9FE 100%)!important}
        .block-container{max-width:610px!important;padding:30px 16px 40px!important}
        div[data-testid="stVerticalBlockBorderWrapper"]{
          border:1px solid #D7E4EE!important;border-radius:22px!important;
          background:rgba(255,255,255,.96)!important;
          box-shadow:0 24px 65px rgba(22,84,131,.11)!important}
        div[data-testid="stTextInput"] label,div[data-testid="stSelectbox"] label,
        div[data-testid="stTextArea"] label{font-size:13px!important;color:#173756!important;font-weight:750!important}
        div[data-testid="stTextInput"] input{
          min-height:44px!important;border-radius:11px!important;
          background:#FFFFFF!important;color:#15314D!important;
          -webkit-text-fill-color:#15314D!important;caret-color:#1265A1!important;
          border:1px solid #C4D4E4!important}
        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder{
          color:#8190A5!important;-webkit-text-fill-color:#8190A5!important;opacity:1!important}
        div[data-testid="stTextInput"] [data-baseweb="input"],
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextArea"] [data-baseweb="textarea"],
        div[data-testid="stSelectbox"] [data-baseweb="select"]>div{
          color:#15314D!important;background:#FFF!important;border-color:#CBD8E7!important;color-scheme:light!important}
        div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
        div[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within{
          outline:2px solid rgba(13,119,218,.28)!important;outline-offset:1px!important}
        div[data-testid="stCheckbox"] label,div[data-testid="stRadio"] label,
        div[data-testid="stForm"] p,div[data-testid="stForm"] span{color:#244563!important}
        .stButton>button,.stFormSubmitButton>button{
          min-height:45px!important;border-radius:12px!important;font-weight:800!important}
        .stFormSubmitButton>button{
          min-height:50px!important;border:0!important;color:#fff!important;
          background:linear-gradient(105deg,#096FBF,#0752A0)!important;
          box-shadow:0 9px 19px rgba(6,89,165,.22)!important}
        .stFormSubmitButton>button:hover{background:linear-gradient(105deg,#087DCC,#0866BA)!important;
          box-shadow:0 12px 23px rgba(6,89,165,.26)!important;transform:translateY(-1px)}
        .auth-security-note{margin-top:18px;padding:14px 12px;border-top:1px solid #E0EAF4;
          color:#5B7085;text-align:center;font-size:12px;line-height:1.55}
        .auth-security-note strong{color:#244563}
        .auth-reset-title{color:#122D51;font-size:25px;font-weight:850;margin:12px 0 6px}

        /* Layout premium somente na página principal: não afeta troca de senha. */
        .stApp:has(.login-v355-layout-marker) .block-container{
          width:100%!important;max-width:1460px!important;min-height:calc(100vh - 40px);
          padding:clamp(20px,4.5vh,60px) clamp(20px,4.6vw,84px) 48px!important}
        .stApp:has(.login-v355-layout-marker) .block-container>div{width:100%}
        .login-v355-layout-marker{height:0;max-height:0;overflow:hidden}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stHorizontalBlock"]{
          align-items:center!important;gap:clamp(32px,5vw,90px)!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stColumn"]{
          min-width:0!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stVerticalBlockBorderWrapper"]{
          border-radius:28px!important;border:1px solid rgba(197,219,236,.8)!important;
          box-shadow:0 28px 72px rgba(25,101,155,.16),0 6px 18px rgba(25,101,155,.07)!important;
          background:linear-gradient(155deg,#FFF 0%,#F9FCFF 100%)!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stVerticalBlockBorderWrapper"]>div{
          padding:clamp(15px,1.5vw,28px)!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stRadio"] [role="radiogroup"]{
          display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:6px!important;
          padding:5px!important;border-radius:13px!important;background:#EEF4FA!important;
          border:1px solid #DFEAF4!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stRadio"] [role="radiogroup"]>label{
          display:flex!important;justify-content:center!important;align-items:center!important;
          border:0!important;border-radius:10px!important;padding:9px 4px!important;
          min-height:42px!important;min-width:0!important;cursor:pointer!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stRadio"] [role="radiogroup"]>label:has(input:checked){
          background:linear-gradient(110deg,#1166BA,#07539E)!important;box-shadow:0 5px 13px rgba(11,82,158,.18)!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stRadio"] [role="radiogroup"]>label:has(input:checked) p{
          color:#FFF!important;font-weight:800!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stRadio"] [role="radiogroup"]>label p{
          font-size:14px!important;font-weight:700!important;color:#1B3C60!important}
        /* O próprio input nativo continua acessível pelo teclado. */
        .stApp:has(.login-v355-layout-marker) div[data-testid="stRadio"] [role="radiogroup"]>label [data-testid="stMarkdownContainer"]{
          margin:0!important}
        .stApp:has(.login-v355-layout-marker) .auth-reset-title{
          font-size:clamp(25px,2.2vw,32px);margin-top:13px;margin-bottom:4px}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stForm"]{
          border:1px solid #D6E2EE!important;background:rgba(249,252,255,.6)!important;
          border-radius:17px!important;padding:clamp(14px,1.5vw,23px)!important}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stFormSubmitButton"] button{
          width:100%!important;min-height:52px!important}
        .stApp:has(.login-v355-layout-marker) .auth-security-note{
          border-top:1px solid #DCE8F1;background:transparent;border-radius:0}
        .stApp:has(.login-v355-layout-marker) div[data-testid="stCaptionContainer"]{
          font-size:13px!important;line-height:1.5!important}

        /* Coluna de identidade visual com o mascote oficial. */
        .auth-brand{text-align:center;margin-bottom:5px}
        .auth-brand .auth-hero{display:block;width:100%;max-width:510px;
          height:auto;object-fit:contain;margin:0 auto 4px;
          filter:drop-shadow(0 14px 21px rgba(15,78,132,.12))}
        .auth-brand h1{font-weight:900;font-size:30px;line-height:1.13;
          color:#0B315E;letter-spacing:-.025em;margin:4px 0}
        .auth-brand h1 strong{color:#0767B6;font-weight:900}
        .auth-brand p{color:#687E94;font-size:13px;margin:8px 0 0}
        .auth-brand .auth-overline{display:none}
        .auth-brand .auth-accent{width:73px;height:5px;border-radius:999px;
          margin:16px auto 8px;background:linear-gradient(90deg,#1BC1B6,#149FCA)}
        .auth-features{display:none}
        .stApp:has(.login-v355-layout-marker) .auth-brand{
          text-align:left;max-width:660px;margin:0 auto}
        .stApp:has(.login-v355-layout-marker) .auth-hero{
          max-width:650px;max-height:min(42vh,435px);object-fit:contain;
          object-position:left bottom;margin:0 0 9px;
          filter:drop-shadow(0 22px 24px rgba(17,94,146,.13))}
        .stApp:has(.login-v355-layout-marker) .auth-brand h1{
          font-size:clamp(38px,4vw,66px);line-height:1.05;letter-spacing:-.04em;
          max-width:630px;margin:0;color:#0B315E}
        .stApp:has(.login-v355-layout-marker) .auth-brand h1 strong{display:block}
        .stApp:has(.login-v355-layout-marker) .auth-brand p{
          font-size:clamp(15px,1.4vw,18px);margin:8px 0 0;color:#60748D}
        .stApp:has(.login-v355-layout-marker) .auth-brand .auth-accent{margin:18px 0 12px;width:83px}
        .stApp:has(.login-v355-layout-marker) .auth-features{
          display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;
          margin-top:clamp(25px,4vh,40px);padding-top:18px;border-top:1px solid rgba(193,214,230,.8)}
        .auth-feature{display:flex;align-items:center;gap:9px;min-width:0;
          color:#23435E;font-weight:600;font-size:12px;line-height:1.35}
        .auth-feature-icon{flex:none;display:flex;align-items:center;justify-content:center;
          width:41px;height:41px;border-radius:12px;
          background:linear-gradient(145deg,#D9F6FC,#E8F2FF);color:#0573BD}
        .auth-feature-icon svg{width:23px;height:23px;stroke:currentColor;stroke-width:1.8;fill:none;
          stroke-linecap:round;stroke-linejoin:round}

        @media (max-width: 1000px) {
          .stApp:has(.login-v355-layout-marker) .block-container{
            max-width:800px!important;padding:24px 20px 40px!important}
          .stApp:has(.login-v355-layout-marker) div[data-testid="stHorizontalBlock"]{
            flex-wrap:wrap!important;gap:18px!important}
          .stApp:has(.login-v355-layout-marker) div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{
            min-width:100%!important;width:100%!important;flex:1 1 100%!important}
          .stApp:has(.login-v355-layout-marker) .auth-brand{text-align:center;max-width:620px}
          .stApp:has(.login-v355-layout-marker) .auth-hero{max-width:420px;max-height:260px;margin:0 auto 4px;object-position:center}
          .stApp:has(.login-v355-layout-marker) .auth-brand h1{font-size:clamp(28px,5vw,43px);max-width:none}
          .stApp:has(.login-v355-layout-marker) .auth-brand h1 strong{display:inline}
          .stApp:has(.login-v355-layout-marker) .auth-brand .auth-accent{margin:13px auto}
          .stApp:has(.login-v355-layout-marker) .auth-features{margin-top:16px;padding-top:12px;gap:8px}
        }
        @media (max-width: 600px) {
          .block-container{width:100%!important;max-width:100%!important;padding:14px 14px 35px!important}
          .stApp:has(.login-v355-layout-marker) .block-container{padding:14px 12px 28px!important}
          .stApp:has(.login-v355-layout-marker) .auth-hero{max-width:310px;max-height:180px}
          .stApp:has(.login-v355-layout-marker) .auth-brand h1{font-size:31px}
          .stApp:has(.login-v355-layout-marker) .auth-brand p{font-size:13px}
          .stApp:has(.login-v355-layout-marker) .auth-features{display:none}
          .stApp:has(.login-v355-layout-marker) div[data-testid="stVerticalBlockBorderWrapper"]{
            border-radius:17px!important}
          .stApp:has(.login-v355-layout-marker) div[data-testid="stVerticalBlockBorderWrapper"]>div{
            padding:10px!important}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
'''

NEW_BRAND = '''def _render_auth_brand(subtitle="Acesso ao Painel de Monitoramento"):
    # Ilustração oficial já incluída no projeto, sem dependências de rede nem arquivos novos.
    monitor_icon = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8m-4-4v4"/></svg>'
    bell_icon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"/></svg>'
    chart_icon = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="8" width="4" height="13" rx="1"/><rect x="17" y="3" width="4" height="18" rx="1"/></svg>'
    st.markdown(
        f"""
        <div class="auth-brand">
          <img class="auth-hero" src="data:image/png;base64,{LOGIN_HERO_B64}" alt="Mascote oficial do Grupo S&S ao lado de um painel de monitoramento">
          <h1>Painel de <strong>Monitoramento</strong></h1>
          <div class="auth-accent" aria-hidden="true"></div>
          <p>{html.escape(subtitle)}</p>
          <div class="auth-features" aria-label="Recursos do painel">
            <div class="auth-feature"><span class="auth-feature-icon">{monitor_icon}</span><span>Acompanhe os<br>seus sistemas</span></div>
            <div class="auth-feature"><span class="auth-feature-icon">{bell_icon}</span><span>Receba alertas<br>em tempo real</span></div>
            <div class="auth-feature"><span class="auth-feature-icon">{chart_icon}</span><span>Monitore indicadores<br>e ocorrências</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
'''

def replace_single(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: {n} âncoras; abortado sem alterar.")
    return text.replace(old,new,1)

def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a=text.find(start)
    b=text.find(end,a+len(start))
    if a < 0 or b < 0 or text.count(start)!=1 or text.count(end)!=1:
        raise RuntimeError(f"{label}: não foi possível localizar os limites únicos.")
    return text[:a]+replacement+text[b:]

def apply(text: str) -> str:
    if MARKER in text:
        ast.parse(text, filename="main.py")
        print("Login v3.55 já presente; verificação apenas.")
        return text
    text=replace_between(text,"def _auth_login_css():","def _render_auth_brand(",
                         NEW_CSS+"\n\n","folha de estilo")
    text=replace_between(text,"def _render_auth_brand(", "def _render_set_password(",
                         NEW_BRAND+"\n\n","hero do login")
    start = '    _auth_login_css()\n    _render_auth_brand()\n\n    notice = st.session_state.pop('
    end = '\n\n\ndef _render_account_sidebar():'
    if text.count(start)!=1 or text.count(end)!=1:
        raise RuntimeError("Corpo do login alterado; âncoras inesperadas.")
    a=text.find(start)
    b=text.find(end,a+len(start))
    existing=text[a:b]
    assert existing.startswith('    _auth_login_css()\n    _render_auth_brand()\n\n')
    body='    notice = st.session_state.pop('+existing.split('    notice = st.session_state.pop(',1)[1]
    if not body.rstrip().endswith('st.stop()'):
        raise RuntimeError("Limite de st.stop não encontrado; não alterar formulário.")
    indented="".join(("    "+line if line.strip() else line) for line in body.splitlines(keepends=True))
    wrapper=(
        "    _auth_login_css()\n"
        "    st.markdown('<div class=\"login-v355-layout-marker\" aria-hidden=\"true\"></div>', unsafe_allow_html=True)\n"
        "    login_hero_col, login_form_col = st.columns([1.08, 1], gap=\"large\", vertical_alignment=\"center\")\n"
        "    with login_hero_col:\n"
        "        _render_auth_brand()\n\n"
        "    with login_form_col:\n"+indented
    )
    text=text[:a]+wrapper+text[b:]
    text=replace_single(text,'APP_VERSION = "3.54.0"','APP_VERSION = "3.55.0"',"versão")
    ast.parse(text, filename="main.py")
    assert text.count('<div class="login-v355-layout-marker"')==1, "Marcador de layout duplicado ou ausente"
    assert text.count('with st.form("monitor_auth_login"') == 1
    assert text.count('with st.form("monitor_request_access_v336"') == 1
    assert text.count('login_hero_col, login_form_col = st.columns(') == 1
    assert text[text.index('def _render_login_gate():'):text.index('def _render_account_sidebar():')].count('_auth_login(email, password)') == 1
    assert text.count('st.session_state["_monitor_auth_remember_v342"] = bool(remember_device)') == 1
    assert text.count('_monitor_render_formspree_browser_form()') >= 1
    return text

if __name__=="__main__":
    original=MAIN.read_text(encoding="utf-8")
    result=apply(original)
    if result!=original:
        MAIN.write_text(result,encoding="utf-8")
        print("OK: design SaaS aplicado; autenticação, solicitação de acesso e troca de senha preservadas.")
