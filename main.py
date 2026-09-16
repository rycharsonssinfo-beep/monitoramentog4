import streamlit as st
import streamlit.components.v1 as components

# Configuração da página para ocupar a largura inteira (Modo Wide)
st.set_page_config(
    page_title="Painel de Monitoramento Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS customizada para deixar o visual limpo, moderno e sem poluição
st.markdown("""
    <style>
        /* Oculta o cabeçalho padrão do Streamlit para dar aspecto de app dedicado */
        header {visibility: hidden;}
        .stApp { background-color: #f4f6f9; }
        
        /* Estilização dos títulos e blocos */
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
    </style>
""", unsafe_allow_html=True)

# Inicializa o estado da sessão para controlar a exibição
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

# --- TELA DE CONFIGURAÇÃO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<p class="main-title">📊 Configurar Painel de Monitoramento</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-text">Insira os links que deseja rotacionar na tela de suporte.</p>', unsafe_allow_html=True)
        
        # Caixa de texto para os links
        links_texto = st.text_area(
            "Links das páginas (um por linha):",
            value="https://exemplo.com/painel-1\nhttps://exemplo.com/painel-2",
            height=160
        )
        
        # Tempo de rotação
        tempo_segundos = st.number_input(
            "Tempo de exibição de cada tela (segundos):",
            min_value=5,
            max_value=300,
            value=30,
            step=5
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Apresentação", type="primary", use_container_width=True):
            # Processa e limpa os links inseridos
            lista_links = [l.strip() for l in links_texto.split("\n") if l.strip()]
            
            if not lista_links:
                st.error("Por favor, insira pelo menos um link válido.")
            else:
                st.session_state.links = lista_links
                st.session_state.tempo = tempo_segundos
                st.session_state.iniciado = True
                st.rerun()

# --- TELA DE EXIBIÇÃO EM ROTAÇÃO ---
else:
    links = st.session_state.links
    tempo = st.session_state.tempo
    
    # Barra de controle superior discreta (com botão para voltar às configurações)
    col_info, col_btn = st.columns([8, 2])
    with col_info:
        st.markdown(f"**Modo de Rotação Ativo** | Total de painéis: `{len(links)}` | Intervalo: `{tempo}s`")
    with col_btn:
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()

    # Código HTML/JS injetado via componente para fazer a rotação automática dos iframes com o tempo escolhido
    # Isso garante que a página recarregue os dados e alterne de forma fluida sem travar o Streamlit
    html_rotacao = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body, html {{
                margin: 0; padding: 0; width: 100%; height: 100vh; overflow: hidden; background: #fff;
            }}
            iframe {{
                width: 100%; height: 100vh; border: none; display: block;
            }}
            #barra-status {{
                position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
                background: rgba(30, 41, 59, 0.9); color: #fff; padding: 8px 18px;
                border-radius: 20px; font-family: sans-serif; font-size: 13px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 9999;
                transition: opacity 0.3s;
            }}
        </style>
    </thhead>
    <body>
        <iframe id="frame-tela" src=""></iframe>
        <div id="barra-status">Carregando painel...</div>

        <script>
            const links = {links};
            const tempoMs = {tempo} * 1000;
            let index = 0;
            
            const iframe = document.getElementById('frame-tela');
            const status = document.getElementById('barra-status');

            function atualizarTela() {{
                if (links.length === 0) return;
                iframe.src = links[index];
                status.innerText = "Exibindo painel " + (index + 1) + " de " + links.length + " (" + links[index] + ")";
                index = (index + 1) % links.length;
            }}

            // Executa imediatamente e depois a cada intervalo
            atualizarTela();
            setInterval(atualizarTela, tempoMs);
        </script>
    </body>
    </html>
    """
    
    # Renderiza o componente HTML em tela cheia na aplicação
    components.html(html_rotacao, height=800, scrolling=False)
