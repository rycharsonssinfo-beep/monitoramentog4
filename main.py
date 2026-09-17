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
        
        .stTextArea textarea {
            border-color: #cbd5e1 !important;
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Inicialização das variáveis de sessão com suporte a salvamento persistente no navegador via query/session
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

# Padrão inicial com os 3 links e tempo padrão de 20 segundos para cada caso não especificado
padrao_links_tempos = (
    "https://ssinformatica.g4flex.com.br:9090/monitoring/queues | 20\n"
    "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues | 20\n"
    "https://ssinformatica.g4flex.com.br:9090/admin/monitoring/chat/conversation | 20"
)

if "config_texto_salva" not in st.session_state:
    st.session_state.config_texto_salva = padrao_links_tempos

# --- TELA 1: CONFIGURAÇÃO COM SUPORTE A TEMPO POR LINK E SALVAMENTO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Configuração do Painel de Monitoramento")
        st.markdown("<p style='color: #64748b !important; font-size: 13px; margin-top: -5px;'>Insira o link seguido de <b>| [segundos]</b> para definir tempos diferentes por tela. Exemplo: <code>https://site.com | 15</code></p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        config_texto = st.text_area(
            "Links e Tempos (um por linha):",
            value=st.session_state.config_texto_salva,
            height=180
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            btn_salvar = st.button("💾 Salvar Configuração", use_container_width=True)
            
        with col_btn2:
            btn_iniciar = st.button("🚀 Iniciar Apresentação", type="primary", use_container_width=True)
            
        if btn_salvar:
            st.session_state.config_texto_salva = config_texto
            st.success("✅ Configurações salvas com sucesso!")
            
        if btn_iniciar or btn_salvar:
            if btn_iniciar:
                linhas = [l.strip() for l in config_texto.split("\n") if l.strip()]
                lista_dados = []
                
                for linha in linhas:
                    if "|" in linha:
                        partes = linha.split("|")
                        link = partes[0].strip()
                        try:
                            tempo = int(partes[1].strip())
                        except ValueError:
                            tempo = 20 # Padrão caso o usuário digite errado
                    else:
                        link = linha.strip()
                        tempo = 20
                    
                    if link:
                        lista_dados.append({"link": link, "tempo": tempo})
                
                if not lista_dados:
                    st.error("Por favor, insira pelo menos um link válido.")
                else:
                    st.session_state.config_texto_salva = config_texto
                    st.session_state.telas_configuradas = lista_dados
                    st.session_state.iniciado = True
                    st.rerun()

# --- TELA 2: EXIBIÇÃO COM TEMPOS INDIVIDUAIS E TODAS AS MELHORIAS ---
else:
    telas = st.session_state.telas_configuradas
    
    # Prepara listas para o JavaScript
    links_lista = [t["link"] for t in telas]
    tempos_lista = [t["tempo"] for t in telas]
    
    links_json = json.dumps(links_lista)
    tempos_json = json.dumps(tempos_lista)

    # Componente HTML/JS avançado com suporte a temporizadores individuais por tela
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
            #barra-status {{
                width: 100%; height: 45px; background: #0d5c58; color: #ffffff;
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 20px; font-size: 13px; font-weight: 600;
                position: fixed; top: 0; left: 0; z-index: 9999;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            }}
            #telas-wrapper {{
                width: 100%; height: calc(100vh - 45px); position: absolute; top: 45px; left: 0;
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
            .botoes-grupo {{
                display: flex; gap: 6px; align-items: center;
            }}
            .btn-controle {{
                background: #ffffff; color: #0d5c58; border: none; 
                height: 28px; padding: 0 10px;
                border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 700;
                display: inline-flex; align-items: center; justify-content: center;
                transition: background 0.2s, transform 0.1s;
            }}
            .btn-controle:hover {{
                background: #e2e8f0;
            }}
            .btn-controle:active {{
                transform: scale(0.96);
            }}
            #btn-pause {{
                background: #115e59; color: #ffffff; border: 1px solid #2dd4bf;
            }}
            #btn-pause.pausado {{
                background: #b91c1c; color: #ffffff; border-color: #f87171;
            }}
        </style>
    </head>
    <body>
        <div id="barra-status">
            <span id="info-texto">Carregando painéis...</span>
            
            <div class="botoes-grupo">
                <button class="btn-controle" onclick="mudarTela(-1)" title="Painel Anterior">⬅️ Anterior</button>
                <button class="btn-controle" onclick="mudarTela(1)" title="Próximo Painel">Próxima ➡️</button>
                <button class="btn-controle" id="btn-pause" onclick="alternarPausa()" title="Pausar/Retomar Rotação">⏸️ Pausar</button>
                <button class="btn-controle" onclick="alternarTelaCheia()" title="Tela Cheia">📺 Tela Cheia</button>
                <button class="btn-controle" onclick="voltarConfig()" title="Alterar Links e Configurações">⚙️ Ajustes</button>
                <span id="contador-tempo" style="margin-left: 8px; color: #e2e8f0; font-weight: 500; min-width: 90px; font-size: 12px;">Próxima em --s</span>
            </div>
        </div>

        <div id="telas-wrapper"></div>

        <script>
            const links = {links_json};
            const tempos = {tempos_json};
            let indiceAtual = 0;
            let iframes = [];
            let temporizador;
            let estaPausado = false;
            let tempoRestante = 20;

            const wrapperDiv = document.getElementById('telas-wrapper');
            const infoTexto = document.getElementById('info-texto');
            const contadorTempo = document.getElementById('contador-tempo');
            const btnPause = document.getElementById('btn-pause');

            const savedIndex = localStorage.getItem("painel_indice_atual");
            if (savedIndex !== null && parseInt(savedIndex) < links.length) {{
                indiceAtual = parseInt(savedIndex);
            }}

            links.forEach((link, index) => {{
                const container = document.createElement('div');
                container.className = 'iframe-container' + (index === indiceAtual ? ' ativo' : '');
                
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

            function atualizarExibicao() {{
                iframes.forEach((item, i) => {{
                    if (i === indiceAtual) {{
                        item.container.classList.add('ativo');
                    }} else {{
                        item.container.classList.remove('ativo');
                    }}
                }});
                infoTexto.innerHTML = "🟢 Painel <b>(" + (indiceAtual + 1) + "/" + links.length + ")</b> - " + tempos[indiceAtual] + "s";
                localStorage.setItem("painel_indice_atual", indiceAtual);
            }}

            function atualizarPainelAtual() {{
                const itemAtual = iframes[indiceAtual];
                const scrollKey = "scroll_pos_" + itemAtual.link;
                try {{
                    sessionStorage.setItem(scrollKey, JSON.stringify({{
                        x: itemAtual.iframe.contentWindow.scrollX,
                        y: itemAtual.iframe.contentWindow.scrollY
                    }}));
                }} catch(e) {{}}
                
                itemAtual.iframe.src = itemAtual.link;
            }}

            function irParaProxima() {{
                indiceAtual = (indiceAtual + 1) % links.length;
                atualizarExibicao();
                atualizarPainelAtual();
                reiniciarTemporizador();
            }}

            function mudarTela(direcao) {{
                indiceAtual = (indiceAtual + direcao + links.length) % links.length;
                atualizarExibicao();
                reiniciarTemporizador();
            }}

            function alternarPausa() {{
                estaPausado = !estaPausado;
                if (estaPausado) {{
                    clearInterval(temporizador);
                    btnPause.innerText = "▶️ Retomar";
                    btnPause.classList.add("pausado");
                    contadorTempo.innerText = "⏸️ Pausado";
                }} else {{
                    btnPause.innerText = "⏸️ Pausar";
                    btnPause.classList.remove("pausado");
                    reiniciarTemporizador();
                }}
            }}

            function alternarTelaCheia() {{
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen().catch(err => {{}} );
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }}
                }}
            }}

            function voltarConfig() {{
                window.parent.location.reload();
            }}

            atualizarExibicao();

            function reiniciarTemporizador() {{
                clearInterval(temporizador);
                if (estaPausado) return;
                
                // Pega o tempo específico configurado para esta tela atual
                tempoRestante = tempos[indiceAtual];
                contadorTempo.innerText = "Próxima em " + tempoRestante + "s";

                temporizador = setInterval(function() {{
                    if (estaPausado) return;
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
    
    st.components.v1.html(html_painel, height=930, scrolling=False)
