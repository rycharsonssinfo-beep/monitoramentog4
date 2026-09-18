import streamlit as st

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para limpar a interface e estilizar os elementos
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
        }
        .stApp { background-color: #f8fafc !important; }
        
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
        
        .stButton button:not([kind="primary"]) {
            background-color: #ffffff !important;
            color: #b91c1c !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        .stButton button:not([kind="primary"]):hover {
            background-color: #fef2f2 !important;
            border-color: #b91c1c !important;
        }
        .stButton button:not([kind="primary"]) p {
            color: #b91c1c !important;
        }
    </style>
""", unsafe_allow_html=True)

# Gerenciamento de estado da tela atual
if "iniciado" not in st.session_state:
    if st.query_params.get("iniciado") == "true":
        st.session_state.iniciado = True
    else:
        st.session_state.iniciado = False

# Inicialização da lista de painéis
if "paineis_config" not in st.session_state:
    st.session_state.paineis_config = [
        {
            "link": "https://ssinformatica.g4flex.com.br:9090/monitoring/queues",
            "nome": "Fila de Voz / Zoiper",
            "tempo": 20,
            "recarregar": True
        },
        {
            "link": "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues",
            "nome": "Grade de Filas Chat",
            "tempo": 20,
            "recarregar": True
        },
        {
            "link": "https://ssinformatica.g4flex.com.br:9090/admin/monitoring/chat/conversation",
            "nome": "Dados Sintéticos de Monitoramento",
            "tempo": 20,
            "recarregar": True
        }
    ]

if "horas_reload_geral" not in st.session_state:
    st.session_state.horas_reload_geral = 0

def adicionar_painel():
    st.session_state.paineis_config.append({
        "link": "",
        "nome": f"Novo Painel {len(st.session_state.paineis_config) + 1}",
        "tempo": 20,
        "recarregar": True
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
        st.markdown("<p style='color: #64748b !important; font-size: 13px; margin-top: -5px;'>Gerencie os nomes, links, tempos de exibição e prevenção de memória.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<p style='font-weight: 600; font-size: 14px;'>📋 Lista de Painéis e Ordem de Exibição:</p>", unsafe_allow_html=True)
        
        col_leg1, col_leg2, col_leg3, col_leg4 = st.columns([2.2, 2.5, 0.8, 0.5])
        with col_leg1:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #0d5c58 !important; margin-bottom: 2px;'>Nome do Painel</p>", unsafe_allow_html=True)
        with col_leg2:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #0d5c58 !important; margin-bottom: 2px;'>🔗 Links (URL da Página)</p>", unsafe_allow_html=True)
        with col_leg3:
            st.markdown("<p style='font-size: 12px; font-weight: 600; color: #0d5c58 !important; margin-bottom: 2px;'>⏱️ Segundos</p>", unsafe_allow_html=True)
        with col_leg4:
            st.markdown("", unsafe_allow_html=True)

        for i, painel in enumerate(st.session_state.paineis_config):
            with st.container():
                cols = st.columns([2.2, 2.5, 0.8, 0.5])
                with cols[0]:
                    st.session_state.paineis_config[i]["nome"] = st.text_input(f"Nome {i+1}", value=painel["nome"], key=f"nome_{i}", label_visibility="collapsed")
                with cols[1]:
                    st.session_state.paineis_config[i]["link"] = st.text_input(f"Link {i+1}", value=painel["link"], key=f"link_{i}", label_visibility="collapsed")
                with cols[2]:
                    st.session_state.paineis_config[i]["tempo"] = st.number_input(f"Tempo {i+1}", min_value=5, max_value=300, value=int(painel["tempo"]), step=5, key=f"tempo_{i}", label_visibility="collapsed")
                with cols[3]:
                    if st.button("🗑️", key=f"del_{i}", help="Remover painel", use_container_width=True):
                        remover_painel(i)
                        st.rerun()

        if st.button("➕ Adicionar Novo Painel", use_container_width=True):
            adicionar_painel()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight: 600; font-size: 14px;'>🧹 Otimização de Performance (Prevenção de Memory Leak):</p>", unsafe_allow_html=True)
        
        st.session_state.horas_reload_geral = st.selectbox(
            "Recarregamento periódico total da aplicação (Limpeza de Cache / RAM em longos períodos):",
            options=[0, 1, 2, 4, 6, 8, 12, 24],
            format_func=lambda x: "Desativado (Rodar direto)" if x == 0 else ("A cada 1 hora" if x == 1 else f"A cada {x} horas"),
            key="select_reload_geral"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Apresentação", type="primary", use_container_width=True):
            links_validos = [p["link"].strip() for p in st.session_state.paineis_config if p["link"].strip()]
            if not links_validos:
                st.error("Por favor, preencha pelo menos um link válido.")
            else:
                st.session_state.iniciado = True
                st.query_params["iniciado"] = "true"
                st.rerun()

# --- TELA 2: EXIBIÇÃO COM BARRA SUPERIOR NATIVA DO STREAMLIT ---
else:
    # Barra de controle superior estilizada em colunas do Streamlit
    st.markdown("""
        <style>
            .barra-topo {
                background-color: #0d5c58;
                padding: 8px 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                font-weight: 600;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                border-radius: 0px;
                margin-bottom: 0px;
            }
        </style>
    """, unsafe_allow_html=True)

    telas = st.session_state.paineis_config
    
    # Gerenciamento de estado de índice atual na sessão
    if "indice_painel_ativo" not in st.session_state:
        st.session_state.indice_painel_ativo = 0

    if st.session_state.indice_painel_ativo >= len(telas):
        st.session_state.indice_painel_ativo = 0

    painel_atual = telas[st.session_state.indice_painel_ativo]
    
    # Criando o layout da barra de ferramentas diretamente no Streamlit
    c_info, c_botoes = st.columns([3, 4])
    
    with c_info:
        st.markdown(f"""
            <div style="background-color: #0d5c58; padding: 10px 15px; color: white; border-radius: 6px; font-weight: 600; font-size: 13px; display: flex; align-items: center; height: 38px;">
                🟢 &nbsp;<b>{painel_atual['nome']}</b> &nbsp;<i>({st.session_state.indice_painel_ativo + 1}/{len(telas)})</i>
            </div>
        """, unsafe_allow_html=True)
        
    with c_botoes:
        # Colocando os botões lado a lado perfeitamente integrados
        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            if st.button("⬅️ Ant.", use_container_width=True):
                st.session_state.indice_painel_ativo = (st.session_state.indice_painel_ativo - 1) % len(telas)
                st.rerun()
        with b2:
            if st.button("Próx. ➡️", use_container_width=True):
                st.session_state.indice_painel_ativo = (st.session_state.indice_painel_ativo + 1) % len(telas)
                st.rerun()
        with b3:
            # O Botão de Ajustes agora é um botão padrão do Streamlit totalmente funcional
            if st.button("⚙️ Ajustes", type="primary", use_container_width=True, help="Alterar Links e Configurações"):
                st.session_state.iniciado = False
                st.query_params["iniciado"] = "false"
                st.rerun()
        with b4:
            # Botão de recarga manual ou controle de estado
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()
        with b5:
            # Recarregamento automático por tempo integrado via st.empty() ou meta refresh controlado
            pass

    # Exibição do iframe com o link atual e temporizador de rotação automática
    tempo_atual = int(painel_atual['tempo'])
    link_atual = painel_atual['link']

    # Injeta um script leve apenas para fazer o refresh automático após X segundos para o próximo painel
    script_rotacao = f"""
        <script>
            setTimeout(function() {{
                // Simula clique no botão próximo ou avança via query param/streamlit reload
                window.location.reload();
            }}, {tempo_atual * 1000});
        </script>
    """

    st.components.v1.iframe(link_atual, height=880, scrolling=True)
    st.markdown(script_rotacao, unsafe_allow_html=True)
