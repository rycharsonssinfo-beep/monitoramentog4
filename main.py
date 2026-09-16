import streamlit as st
import streamlit.components.v1 as components
import json

# Configuração da página em modo wide
st.set_page_config(
    page_title="Painel de Monitoramento - Grupo S&S",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado com as cores corporativas do Grupo S&S (#0d5c58)
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
        .stApp { background-color: #f8fafc !important; }
        
        h2, p, span, label { color: #0d5c58 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        
        .stButton button[kind="primary"] {
            background-color: #0d5c58 !important;
            color: #ffffff !important;
            border-radius: 8px;
            font-weight: 600;
            border: none;
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
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Cabeçalho visual idêntico ao site corporativo com o selo e nome Grupo S&S
        st.markdown("""
            <div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 20px;">
                <div style="width: 55px; height: 55px; border: 3px solid #0d5c58; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e6f2f2;">
                    <span style="font-size: 24px; font-weight: bold; color: #0d5c58;">S&S</span>
                </div>
                <div>
                    <h1 style="margin: 0; font-size: 28px; color: #0d5c58; font-weight: 800; letter-spacing: -0.5px;">Grupo S&S</h1>
                    <p style="margin: 0; font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Soluções para Gestão Municipal</p>
                </div>
            </div>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin-bottom: 25px;">
        """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Configuração do Painel de Monitoramento")
        st.markdown("<p style='color: #64748b !important; font-size: 14px; margin-top: -10px;'>Insira os links dos painéis que deseja rotacionar na tela de suporte.</p>", unsafe_allow_html=True)
        
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
    
    # Barra superior limpa com a marca corporativa
    col_logo, col_info, col_full, col_btn = st.columns([2, 3, 1.2, 1.2])
    
    with col_logo:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
                <div style="width: 32px; height: 32px; border: 2px solid #0d5c58; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #e6f2f2;">
                    <span style="font-size: 13px; font-weight: bold; color: #0d5c58;">S&S</span>
                </div>
                <span style="font-weight: 700; color: #0d5c58; font-size: 16px;">Grupo S&S</span>
            </div>
        """, unsafe_allow_html=True)
        
    with col_info:
        st.markdown(f"<p style='margin-top: 10px; font-weight: 600; color: #0d5c58 !important;'>🟢 Painel Ativo ({len(links)} telas) | <b>{tempo}s</b></p>", unsafe_allow_html=True)
        
    with col_full:
        st.markdown("<p style='margin-top: 10px; font-size: 13px;'>💡 <b>F11</b> Tela Cheia</p>", unsafe_allow_html=True)

    with col_btn:
        st.markdown("<div style='margin-top: 5px;'>", unsafe_allow_html=True)
        if st.button("⚙️ Alterar Links", use_container_width=True):
            st.session_state.iniciado = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    links_json = json.dumps(links)

    # HTML/JS customizado
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
            .iframe-container {{
                width: 100%; height: calc(100vh - 45px); display: none; background: #ffffff;
            }}
            .iframe-container.ativo {{
                display: block;
            }}
            iframe {{
                width: 100%; height: 100%; border: none; display: block;
            }}
            #barra-status {{
                width: 100%; height: 45px; background: #0d5c58; color: #ffffff;
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 15px; font-size: 13px; font-weight: 500;
                box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
            }}
            .botoes-grupo {{
                display: flex; gap: 8px; align-items: center;
            }}
            .btn-controle {{
                background: #ffffff; color: #0d5c58; border: none; padding: 5px 12px;
                border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 700;
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
                <span id="contador-tempo" style="margin-left: 10px; color: #e2e8f0;">Próxima em {tempo}s</span>
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
    
    components.html(html_painel, height=830, scrolling=False)
