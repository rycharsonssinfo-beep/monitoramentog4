import streamlit as st
import streamlit.components.v1 as components

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS limpo, moderno e com TEMA CLARO (fundo claro, sem dark mode)
st.markdown("""
    <style>
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        .block-container {
            padding-top: 5px !important;
            padding-bottom: 0px !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
            max-width: 100% !important;
        }
        /* Fundo totalmente claro */
        .stApp { background-color: #f4f6f9 !important; }
        
        /* Estilização dos textos e botões para o tema claro */
        h2, p, span { color: #1e293b !important; }
    </style>
""", unsafe_allow_html=True)

# Inicializa o estado da sessão
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False
if "indice_atual" not in st.session_state:
    st.session_state.indice_atual = 0

# --- TELA DE CONFIGURAÇÃO (Tema Claro) ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 📊 Configurar Painel de Monitoramento")
        st.markdown("Insira os links que deseja rotacionar na tela de suporte.")
        
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
    
    # Barra de controle compacta no topo
    col_info, col_ant, col_prox, col_full, col_btn = st.columns([3.5, 1, 1, 1.3, 1.3])
    
    with col_info:
        st.markdown(f"🟢 **Painel Ativo** ({st.session_state.indice_atual + 1}/{len(links)}) | Intervalo: **{tempo}s**")
        
    with col_ant:
        if st.button("⬅️ Anterior", use_container_width=True):
            st.session_state.indice_atual = (st.session_state.indice_atual - 1) % len(links)
            st.rerun()
            
    with col_prox:
        if st.button("Próxima ➡️", use_container_width=True):
            st.session_state.indice_atual = (st.session_state.indice_atual + 1) % len(links)
            st.rerun()

    with col_full:
        # Orientação clara sobre o Tela Cheia padrão (F11)
        st.markdown("💡 **Aperte F11** p/ Tela Cheia", help="Pressione a tecla F11 no teclado da TV/Monitor para preencher a tela inteira.")

    with col_btn:
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()

    link_atual = links[st.session_state.indice_atual]

    # HTML/JS limpo e com fundo branco para evitar qualquer tela escura durante o carregamento
    html_painel = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body, html {{
                width: 100%; height: 100vh; overflow: hidden; background: #ffffff;
            }}
            iframe {{
                width: 100%; height: calc(100vh - 35px); border: none; display: block; background: #ffffff;
            }}
            #barra-status {{
                width: 100%; height: 35px; background: #e2e8f0; color: #1e293b;
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 15px; font-family: sans-serif; font-size: 12px; font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <iframe id="frame-tela" src="{link_atual}"></iframe>
        <div id="barra-status">
            <span>Exibindo: {link_atual}</span>
            <span>Próxima rotação em {tempo}s</span>
        </div>

        <script>
            // Rotação automática pelo tempo configurado
            const tempoMs = {tempo} * 1000;
            setTimeout(function() {{
                window.location.reload();
            }}, tempoMs);
        </script>
    </body>
    </html>
    """
    
    # Renderiza o iframe ocupando toda a altura sem barras de corte
    components.html(html_painel, height=830, scrolling=False)
