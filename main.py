import streamlit as st
import time

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para ocupar 100% da tela em modo tela cheia (F11) sem margens
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
        
        /* Botão principal com fundo verde petróleo e texto branco visível */
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

# Inicializa o estado da sessão
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False
if "links_salvos" not in st.session_state:
    st.session_state.links_salvos = "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues\nhttps://ssinformatica.g4flex.com.br:9090/admin/report/chat/performance"
if "tempo_salvo" not in st.session_state:
    st.session_state.tempo_salvo = 20
if "indice_atual" not in st.session_state:
    st.session_state.indice_atual = 0

# --- TELA DE CONFIGURAÇÃO ---
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

# --- TELA DE EXIBIÇÃO EM ROTAÇÃO ---
else:
    links = st.session_state.links
    tempo = st.session_state.tempo
    indice = st.session_state.indice_atual
    
    link_atual = links[indice]

    # Barra superior limpa com os botões de controle de tela visíveis
    col_info, col_btn1, col_btn2, col_full, col_btn3 = st.columns([2.5, 0.9, 0.9, 0.9, 1.2])
    
    with col_info:
        st.markdown(f"<p style='margin: 0px 0px 5px 10px; font-size: 12px; font-weight: 600; color: #0d5c58 !important;'>🟢 Painel {indice + 1} de {len(links)} | <b>{tempo}s</b></p>", unsafe_allow_html=True)

    with col_btn1:
        if st.button("⬅️ Anterior", use_container_width=True):
            st.session_state.indice_atual = (indice - 1) % len(links)
            st.rerun()

    with col_btn2:
        if st.button("Próxima ➡️", use_container_width=True):
            st.session_state.indice_atual = (indice + 1) % len(links)
            st.rerun()
        
    with col_full:
        st.markdown("<p style='margin: 3px 0px 0px 5px; font-size: 11px;'>💡 <b>F11</b> Tela Cheia</p>", unsafe_allow_html=True)

    with col_btn3:
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()

    # Iframe injetado com script interno de captura/restauração de scroll (Simula F11/F5 cirúrgico)
    st.markdown(f"""
        <iframe id="meu-iframe" src="{link_atual}" style="width: 100%; height: calc(100vh - 40px); border: none; display: block;"></iframe>
        
        <script>
            // Chave única baseada no link atual para guardar a posição do scroll no navegador
            const scrollKey = "scroll_pos_" + "{link_atual}";
            const iframe = document.getElementById('meu-iframe');

            // Quando o iframe carregar, restauramos a posição exata de scroll que estava antes do F5
            iframe.onload = function() {{
                try {{
                    const savedScroll = sessionStorage.getItem(scrollKey);
                    if (savedScroll) {{
                        const pos = JSON.parse(savedScroll);
                        iframe.contentWindow.scrollTo(pos.x, pos.y);
                    }}
                }} catch (e) {{
                    console.log("Cross-origin restrição de scroll evitada ou não suportada pelo host.");
                }}
            }};
        </script>
    """, unsafe_allow_html=True)

    # Pausa o tempo determinado e avança para o próximo painel atualizando a página inteira
    time.sleep(tempo)
    st.session_state.indice_atual = (indice + 1) % len(links)
    st.rerun()
