import streamlit as st
import streamlit.components.v1 as components
import json

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para remover margens e rodapés excedentes do Streamlit
st.markdown("""
    <style>
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        .block-container {
            padding-top: 10px !important;
            padding-bottom: 0px !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
            max-width: 100% !important;
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

# Inicializa o estado da sessão e memórias persistentes
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False
if "links_salvos" not in st.session_state:
    st.session_state.links_salvos = "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues\nhttps://ssinformatica.g4flex.com.br:9090/admin/report/chat/performance"
if "tempo_salvo" not in st.session_state:
    st.session_state.tempo_salvo = 20

# --- TELA DE CONFIGURAÇÃO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
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
                st.session_state.iniciado = True
                st.rerun()

# --- TELA DE EXIBIÇÃO EM ROTAÇÃO ---
else:
    links = st.session_state.links
    tempo = st.session_state.tempo
    
    # Barra superior compacta
    col_info, col_full, col_btn = st.columns([4, 1.2, 1.2])
    
    with col_info:
        st.markdown(f"<p style='margin: 0px; font-size: 13px; font-weight: 600; color: #0d5c58 !important;'>🟢 Painel Ativo ({len(links)} telas) | <b>{tempo}s</b></p>", unsafe_allow_html=True)
        
    with col_full:
        st.markdown("<p style='margin: 0px; font-size: 12px;'>💡 <b>F11</b> Tela Cheia</p>", unsafe_allow_html=True)

    with col_btn:
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()

    links_json = json.dumps(links)

    # HTML/JS ajustado para preencher perfeitamente a altura sem sobras
    html_painel = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body, html {{
                width: 100%; height: 100vh; overflow: hidden; background: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            #telas-wrapper {{
                width: 100%; height: calc(100vh - 40px); position: relative;
            }}
            .iframe-container {{
                width: 100%; height: 100%; display: none; background: #ffffff; position: absolute; top: 0; left: 0;
            }}
            .iframe-container.ativo {{
                display: block;
            }}
            iframe {{
                width: 100%; height: 100%; border: none; display: block;
            }}
            #barra-status {{
                width: 100%; height: 40px; background: #0d5c58; color: #ffffff;
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 15px; font-size: 12px; font-weight: 500;
                position: fixed; bottom: 0; left: 0; z-index: 999;
                box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
            }}
            .botoes-grupo {{
                display: flex; gap: 6px; align-items: center;
            }}
            .btn-controle {{
                background: #ffffff; color: #0d5c58; border: none; padding: 3px 10px;
                border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 700;
                transition: background 0.2s;
            }}
            .btn-controle:hover {{
                background: #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div id="telas-wrapper"></div>
        
        <div id="barra-status">
            <span id="info-texto">Carregando painéis...</span>
            
            <div class="botoes-grupo">
                <button class="btn-controle" onclick="mudarTela(-1)">⬅️ Anterior</button>
                <button class="btn-controle" onclick="mudarTela(1)">Próxima ➡️</button>
                <span id="contador-tempo" style="margin-left: 8px; color: #e2e8f0;">Próxima em {tempo}s</span>
            </div>
        </div>

        <script>
            const links = {links_json};
            const tempoSegundos = {tempo};
            let indiceAtual = 0;
            let wrappers = [];
            let temporizador;

            const wrapperDiv = document.getElementById('telas-wrapper');
            const infoTexto = document.getElementById('info-texto');
            const contadorTempo = document.getElementById('contador-tempo');

            links.forEach((link, index) => {{
                const container = document.createElement('div');
                container.className = 'iframe-container' + (index === 0 ? ' ativo' : '');
                
                const iframe = document.createElement('iframe');
                iframe.src = link;
                
                container.appendChild(iframe);
                wrapperDiv.appendChild(container);
                wrappers.push(container);
            }});

            function atualizarExibicao() {{
                if (links.length === 0) return;

                wrappers.forEach((w, i) => {{
                    if (i === indiceAtual) {{
                        w.classList.add('ativo');
                    }} else {{
                        w.classList.remove('ativo');
                    }}
                }});

                infoTexto.innerText = "Painel " + (indiceAtual + 1) + " de " + links.length + " (" + links[indiceAtual] + ")";
            }}

            function irParaProxima() {{
                indiceAtual = (indiceAtual + 1) % links.length;
                atualizarExibicao();
                reiniciarTemporizador();
            }}

            function mudarTela(direcao) {{
                indiceAtual = (indiceAtual + direcao + links.length) % links.length;
                atualizarExibicao();
                reiniciarTemporizador();
            }}

            if(links.length > 0) {{
                atualizarExibicao();
            }}

            function reiniciarTemporizador() {{
                clearInterval(temporizador);
                let tempoRestante = tempoSegundos;
                contadorTempo.innerText = "Próxima em " + tempoRestante + "s";

                temporizador = setInterval(function() {{
                    tempoRestante--;
                    if (tempoRestante < 0) {{
                        irParaProxima();
                    }} else {{
                        contadorTempo.innerText = "Próxima em " + tempoRestante + "s";
                    }}
                }}, 1000);
            }}

            reiniciarTemporizador();
        </script>
    </body>
    </html>
    """
    
    # Altura dinâmica calculada para preencher a tela inteira com folga zero
    components.html(html_painel, height=890, scrolling=False)
