import streamlit as st
import streamlit.components.v1 as components

# Configuração da página para ocupar a largura inteira (Modo Wide)
st.set_page_config(
    page_title="Painel de Monitoramento Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS customizada
st.markdown("""
    <style>
        header {visibility: hidden;}
        .stApp { background-color: #f4f6f9; }
        
        .main-title {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1e293b;
            font-weight: 700;
            font-size: 24px;
            margin-bottom: 5px;
        }
        .sub-text {
            color: #64748b;
            font-size: 14px;
            margin-bottom: 25px;
        }
        /* Estilo customizado para os botões de controle */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Inicializa o estado da sessão
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False
if "indice_atual" not in st.session_state:
    st.session_state.indice_atual = 0

# --- TELA DE CONFIGURAÇÃO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<p class="main-title">📊 Configurar Painel de Monitoramento</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-text">Insira os links que deseja rotacionar na tela de suporte.</p>', unsafe_allow_html=True)
        
        links_texto = st.text_area(
            "Links das páginas (um por linha):",
            value="https://exemplo.com/painel-1\nhttps://exemplo.com/painel-2",
            height=160
        )
        
        tempo_segundos = st.number_input(
            "Tempo de exibição de cada tela (segundos):",
            min_value=5,
            max_value=300,
            value=30,
            step=5
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Apresentação", type="primary", use_container_width=True):
            lista_links = [l.strip() for l in links_texto.split("\n") if l.strip()]
            
            if not lista_links:
                st.error("Por favor, insira pelo menos um link válido.")
            else:
                st.session_state.links = lista_links
                st.session_state.tempo = tempo_segundos
                st.session_state.indice_atual = 0
                st.session_state.iniciado = True
                st.rerun()

# --- TELA DE EXIBIÇÃO EM ROTAÇÃO ---
else:
    links = st.session_state.links
    tempo = st.session_state.tempo
    
    # Barra de controle superior com botões interativos
    col_info, col_ant, col_prox, col_full, col_btn = st.columns([4, 1, 1, 1, 1.5])
    
    with col_info:
        st.markdown(f"**Painel Ativo** | Total: `{len(links)}` | Intervalo: `{tempo}s`")
        
    with col_ant:
        if st.button("⬅️ Anterior", use_container_width=True):
            st.session_state.indice_atual = (st.session_state.indice_atual - 1) % len(links)
            st.rerun()
            
    with col_prox:
        if st.button("Próxima ➡️", use_container_width=True):
            st.session_state.indice_atual = (st.session_state.indice_atual + 1) % len(links)
            st.rerun()

    with col_full:
        # Botão de Tela Cheia via JavaScript injetado
        if st.button("🖥️ Tela Cheia", use_container_width=True):
            components.html("""
                <script>
                    function toggleFullScreen() {
                        if (!document.fullscreenElement) {
                            document.documentElement.requestFullscreen();
                        } else {
                            if (document.exitFullscreen) {
                                document.exitFullscreen();
                            }
                        }
                    }
                    toggleFullScreen();
                </script>
            """, height=0)

    with col_btn:
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()

    # Link atual selecionado pelo estado
    link_atual = links[st.session_state.indice_atual]
    indice_exibicao = st.session_state.indice_atual + 1

    # Código HTML/JS para exibição do iframe e rotação automática controlada por tempo
    html_rotacao = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body, html {{
                margin: 0; padding: 0; width: 100%; height: calc(100vh - 70px); overflow: hidden; background: #fff;
            }}
            iframe {{
                width: 100%; height: 100%; border: none; display: block;
            }}
            #barra-status {{
                position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
                background: rgba(30, 41, 59, 0.9); color: #fff; padding: 8px 18px;
                border-radius: 20px; font-family: sans-serif; font-size: 13px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999;
                pointer-events: none;
            }}
        </style>
    </head>
    <body>
        <iframe id="frame-tela" src="{link_atual}"></iframe>
        <div id="barra-status">Exibindo painel {indice_exibicao} de {len(links)} ({link_atual})</div>

        <script>
            // Rotação automática baseada no tempo configurado caso o usuário não clique em nada
            const tempoMs = {tempo} * 1000;
            
            setTimeout(function() {{
                // Recarrega a página inteira do Streamlit para avançar o índice automaticamente
                window.location.reload();
            }}, tempoMs);
        </script>
    </body>
    </html>
    """
    
    components.html(html_rotacao, height=750, scrolling=False)
