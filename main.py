import streamlit as st

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para limpar a interface e maximizar o espaço
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
            height: 100vh !important;
        }
        .stApp { background-color: #f8fafc !important; }
        
        /* Estilização das abas para maior destaque visual */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #0d5c58;
            padding: 8px 12px;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            background-color: #ffffff;
            border-radius: 6px;
            font-weight: 700;
            color: #0d5c58;
            padding: 0 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2dd4bf !important;
            color: #094744 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Verificação de estado na URL
if "iniciado" not in st.session_state:
    if st.query_params.get("iniciado") == "true":
        st.session_state.iniciado = True
    else:
        st.session_state.iniciado = False

# Inicialização dos painéis
if "paineis_config" not in st.session_state:
    st.session_state.paineis_config = [
        {
            "link": "https://ssinformatica.g4flex.com.br:9090/monitoring/queues",
            "nome": "Fila de Voz / Zoiper"
        },
        {
            "link": "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues",
            "nome": "Grade de Filas Chat"
        },
        {
            "link": "https://ssinformatica.g4flex.com.br:9090/admin/monitoring/chat/conversation",
            "nome": "Dados Sintéticos de Monitoramento"
        }
    ]

def adicionar_painel():
    st.session_state.paineis_config.append({
        "link": "",
        "nome": f"Novo Painel {len(st.session_state.paineis_config) + 1}"
    })

def remover_painel(index):
    if len(st.session_state.paineis_config) > 1:
        st.session_state.paineis_config.pop(index)
    else:
        st.warning("O painel deve conter pelo menos uma tela configurada.")

# --- TELA 1: CONFIGURAÇÃO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2.5, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.image("https://www.ssinformatica.net/wp-content/uploads/2023/03/Grupo-SS.png", width=280)
        
        st.markdown("### Configuração do Painel de Monitoramento")
        st.markdown("<p style='color: #64748b !important; font-size: 13px; margin-top: -5px;'>Gerencie os nomes e links dos painéis.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        for i, painel in enumerate(st.session_state.paineis_config):
            cols = st.columns([2.5, 3, 0.5])
            with cols[0]:
                st.session_state.paineis_config[i]["nome"] = st.text_input(f"Nome {i+1}", value=painel["nome"], key=f"nome_{i}", label_visibility="collapsed")
            with cols[1]:
                st.session_state.paineis_config[i]["link"] = st.text_input(f"Link {i+1}", value=painel["link"], key=f"link_{i}", label_visibility="collapsed")
            with cols[2]:
                if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                    remover_painel(i)
                    st.rerun()

        if st.button("➕ Adicionar Novo Painel", use_container_width=True):
            adicionar_painel()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Painel por Abas", type="primary", use_container_width=True):
            links_validos = [p["link"].strip() for p in st.session_state.paineis_config if p["link"].strip()]
            if not links_validos:
                st.error("Por favor, preencha pelo menos um link válido.")
            else:
                st.session_state.iniciado = True
                st.query_params["iniciado"] = "true"
                st.rerun()

# --- TELA 2: EXIBIÇÃO POR ABAS (SEM CORTES) ---
else:
    telas = st.session_state.paineis_config
    
    # Barra de controlo superior com botão para voltar aos ajustes
    col_topo1, col_topo2 = st.columns([8, 1])
    with col_topo2:
        if st.button("⚙️ Ajustes", use_container_width=True):
            st.session_state.iniciado = False
            st.query_params["iniciado"] = "false"
            st.rerun()

    # Criação das abas nativas para cada painel configurado
    nomes_abas = [f"📊 {t['nome']}" for t in telas]
    abas = st.tabs(nomes_abas)
    
    for i, aba in enumerate(abas):
        with aba:
            link_atual = telas[i]["link"]
            st.components.v1.iframe(link_atual, height=830, scrolling=True)
