import streamlit as st
import json

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para limpar a tela e ajustar o layout
st.markdown("""
    <style>
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        .block-container {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
            max-width: 100% !important;
            height: 100vh !important;
            overflow: hidden !important;
        }
        .stApp { background-color: #f8fafc !important; overflow: hidden !important; }
        
        h2, p, span, label { color: #0d5c58 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        
        .stButton button[kind="primary"] {
            background-color: #0d5c58 !important;
            color: #ffffff !important;
            border-radius: 8px;
            font-weight: 600;
            border: none;
        }
        .stButton button[kind="primary"] p {
            color: #ffffff !important;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #094744 !important;
        }
        
        .stTextArea textarea, .stNumberInput input {
            border-color: #cbd5e1 !important;
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Inicialização das variáveis de sessão
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False
if "links_salvos" not in st.session_state:
    st.session_state.links_salvos = "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues\nhttps://ssinformatica.g4flex.com.br:9090/admin/report/chat/performance"
if "tempo_salvo" not in st.session_state:
    st.session_state.tempo_salvo = 20
if "indice_atual" not in st.session_state:
    st.session_state.indice_atual = 0

# --- TELA 1: CONFIGURAÇÃO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Configuração do Painel de Monitoramento")
        st.markdown("<p style='color: #64748b !important; font-size: 14px; margin-top: -5px;'>Insira os links dos painéis que deseja rotacionar na tela de suporte.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        links_texto = st.text_area(
            "Links das páginas (um por linha):",
            value=st.session_state.links_salvos,
            height=150
        )
        
        tempo_segundos = st.number_input(
            "Tempo de exibição de cada tela (segundos):",
            min_value=5,
            max_value=300,
            value=st.session_state.tempo_salvo,
            step=5
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Apresentação", type="primary", use_container_width=True):
            lista_links = [l.strip() for l in links_texto.split("\n") if l.strip()]
            
            if not lista_links:
                st.error("Por favor, insira pelo menos um link válido.")
            else:
                st.session_state.links_salvos = links_texto
                st.session_state.tempo_salvo = tempo_segundos
                st.session_state.links = lista_links
                st.session_state.tempo = tempo_segundos
                st.session_state.indice_atual = 0
                st.session_state.iniciado = True
                st.rerun()

# --- TELA 2: EXIBIÇÃO COM CONTROLES NATIVOS DO PYTHON ---
else:
    links = st.session_state.links
    tempo = st.session_state.tempo
    indice = st.session_state.indice_atual
    
    link_atual = links[indice]
    links_json = json.dumps(links)

    # Barra superior integrada controlada diretamente pelo Streamlit
    col_info, col_btn_ant, col_btn_prox, col_full, col_config = st.columns([2.2, 0.9, 0.9, 1.2, 1.1])
    
    with col_info:
        st.markdown(f"<p style='margin: 8px 0px 0px 10px; font-size: 13px; font-weight: 700; color: #0d5c58 !important;'>🟢 Painel {indice + 1} de {len(links)}</p>", unsafe_allow_html=True)

    with col_btn_ant:
        if st.button("⬅️ Anterior", use_container_width=True):
            st.session_state.indice_atual = (indice - 1) % len(links)
            st.rerun()

    with col_btn_prox:
        if st.button("Próxima ➡️", use_container_width=True):
            st.session_state.indice_atual = (indice + 1) % len(links)
            st.rerun()

    with col_full:
        st.markdown("<p style='margin: 10px 0px 0px 5px; font-size: 11px;'>💡 <b>F11</b> Tela Cheia</p>", unsafe_allow_html=True)

    with col_config:
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()

    # HTML/JS limpo focado apenas em renderizar os iframes e manter a memória de scroll
    html_painel = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body, html {{
                width: 100%; height: 100vh; overflow: hidden; background: #ffffff;
            }}
            #telas-wrapper {{
                width: 100%; height: 100%; position: relative;
            }}
            .iframe-container {{
                width: 100%; height: 100%; 
                display: none;
                position: absolute; top: 0; left: 0;
                background: #ffffff;
            }}
            .iframe-container.ativo {{
                display: block;
            }}
            iframe {{
                width: 100%; height: 100%; border: none; display: block;
            }}
        </style>
    </head>
    <body>
        <div id="telas-wrapper"></div>

        <script>
            const links = {links_json};
            let indiceAtivo = {indice};
            let iframes = [];

            const wrapperDiv = document.getElementById('telas-wrapper');

            // Cria os iframes preservando o estado de todos
            links.forEach((link, index) => {{
                const container = document.createElement('div');
                container.className = 'iframe-container' + (index === indiceAtivo ? ' ativo' : '');
                
                const iframe = document.createElement('iframe');
                iframe.src = link;
                
                const scrollKey = "scroll_pos_" + link;
                
                iframe.onload = function() {{
                    try {{
                        const savedScroll = sessionStorage.getItem(scrollKey);
                        if (savedScroll) {{
                            const pos = JSON.parse(savedScroll);
                            iframe.contentWindow.scrollTo(pos.x, pos.y);
                        }}
                        
                        iframe.contentWindow.addEventListener('scroll', function() {{
                            sessionStorage.setItem(scrollKey, JSON.stringify({{
                                x: iframe.contentWindow.scrollX,
                                y: iframe.contentWindow.scrollY
                            }}));
                        }});
                    }} catch (e) {{}}
                }};

                container.appendChild(iframe);
                wrapperDiv.appendChild(container);
                iframes.push({{ container: container, iframe: iframe, link: link }});
            }});
        </script>
    </body>
    </html>
    """
    
    # Renderiza o componente ocupando o restante da tela
    st.components.v1.html(html_painel, height=920, scrolling=False)
