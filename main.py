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

if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

padrao_links = (
    "https://ssinformatica.g4flex.com.br:9090/monitoring/queues\n"
    "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues\n"
    "https://ssinformatica.g4flex.com.br:9090/admin/monitoring/chat/conversation"
)

if "links_texto_salvo" not in st.session_state:
    st.session_state.links_texto_salvo = padrao_links

if "tempos_salvos" not in st.session_state:
    st.session_state.tempos_salvos = {
        "https://ssinformatica.g4flex.com.br:9090/monitoring/queues": 20,
        "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues": 20,
        "https://ssinformatica.g4flex.com.br:9090/admin/monitoring/chat/conversation": 20
    }

if "nomes_salvos" not in st.session_state:
    st.session_state.nomes_salvos = {
        "https://ssinformatica.g4flex.com.br:9090/monitoring/queues": "Fila de Voz / Zoiper",
        "https://ssinformatica.g4flex.com.br:9090/monitoringChat/queues": "Grade de Filas Chat",
        "https://ssinformatica.g4flex.com.br:9090/admin/monitoring/chat/conversation": "Dados Sintéticos de Monitoramento"
    }

if "recarregar_salvo" not in st.session_state:
    st.session_state.recarregar_salvo = {}

# --- TELA 1: CONFIGURAÇÃO ---
if not st.session_state.iniciado:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Configuração do Painel de Monitoramento")
        st.markdown("<p style='color: #64748b !important; font-size: 13px; margin-top: -5px;'>Insira os links, defina os nomes personalizados e o tempo de exibição abaixo.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        links_texto = st.text_area(
            "Links das páginas (um por linha):",
            value=st.session_state.links_texto_salvo,
            height=120
        )
        
        links_atuais = [l.strip() for l in links_texto.split("\n") if l.strip()]
        
        st.markdown("<p style='font-weight: 600; font-size: 14px; margin-top: 15px;'>⚙️ Personalização dos Painéis (Nome e Tempo):</p>", unsafe_allow_html=True)
        
        tempos_temporarios = {}
        nomes_temporarios = {}
        
        # Nomes padrão sugeridos com base na ordem
        nomes_padrao_lista = [
            "Fila de Voz / Zoiper",
            "Grade de Filas Chat",
            "Dados Sintéticos de Monitoramento"
        ]
        
        for i, link in enumerate(links_atuais):
            nome_sugerido = nomes_padrao_lista[i] if i < len(nomes_padrao_lista) else f"Painel {i+1}"
            nome_atual = st.session_state.nomes_salvos.get(link, nome_sugerido)
            
            col_a, col_b = st.columns([2, 1])
            with col_a:
                nomes_temporarios[link] = st.text_input(
                    f"Nome do Painel {i+1}",
                    value=nome_atual,
                    key=f"nome_input_{i}"
                )
            with col_b:
                tempo_atual = st.session_state.tempos_salvos.get(link, 20)
                tempos_temporarios[link] = st.number_input(
                    f"Tempo (s) {i+1}",
                    min_value=5,
                    max_value=300,
                    value=int(tempo_atual),
                    step=5,
                    key=f"tempo_input_{i}"
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Iniciar Apresentação", type="primary", use_container_width=True):
            if not links_atuais:
                st.error("Por favor, insira pelo menos um link válido.")
            else:
                lista_final = []
                for link in links_atuais:
                    t = tempos_temporarios.get(link, 20)
                    n = nomes_temporarios.get(link, "Painel")
                    recarregar = st.session_state.recarregar_salvo.get(link, True)
                    lista_final.append({"link": link, "tempo": t, "nome": n, "recarregar": recarregar})
                
                st.session_state.links_texto_salvo = links_texto
                st.session_state.tempos_salvos = tempos_temporarios
                st.session_state.nomes_salvos = nomes_temporarios
                st.session_state.config_completa_salva = lista_final
                st.session_state.iniciado = True
                st.rerun()

# --- TELA 2: EXIBIÇÃO COM NOMES AMIGÁVEIS E BARRA DE PROGRESSO ---
else:
    telas = st.session_state.config_completa_salva
    
    links_lista = [t["link"] for t in telas]
    tempos_lista = [t["tempo"] for t in telas]
    nomes_lista = [t["nome"] for t in telas]
    recarregar_lista = [t.get("recarregar", True) for t in telas]
    
    links_json = json.dumps(links_lista)
    tempos_json = json.dumps(tempos_lista)
    nomes_json = json.dumps(nomes_lista)
    recarregar_json = json.dumps(recarregar_lista)

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
            #barra-progresso-container {{
                position: fixed; top: 45px; left: 0; width: 100%; height: 4px;
                background: #094744; z-index: 9999;
            }}
            #barra-progresso {{
                width: 100%; height: 100%; background: #2dd4bf;
                transform-origin: left; transform: scaleX(1);
                transition: transform 1s linear;
            }}
            #telas-wrapper {{
                width: 100%; height: calc(100vh - 49px); position: absolute; top: 49px; left: 0;
                overflow: hidden;
            }}
            .iframe-container {{
                width: 100%; height: 100%; 
                position: absolute; top: 0; left: -99999px;
                visibility: hidden;
                background: #ffffff;
            }}
            .iframe-container.ativo {{
                left: 0;
                visibility: visible;
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
            #btn-reload-toggle {{
                background: #0f766e; color: #ffffff; border: 1px solid #2dd4bf;
            }}
            #btn-reload-toggle.desativado {{
                background: #7f1d1d; color: #fca5a5; border-color: #f87171;
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
                <button class="btn-controle" id="btn-reload-toggle" onclick="alternarRecarregamento()" title="Ativar/Desativar F5 (Atualização) nesta tela">🔄 Atualizar: ON</button>
                <button class="btn-controle" onclick="alternarTelaCheia()" title="Tela Cheia">📺 Tela Cheia</button>
                <button class="btn-controle" onclick="voltarConfig()" title="Alterar Links e Configurações">⚙️ Ajustes</button>
                <span id="contador-tempo" style="margin-left: 8px; color: #e2e8f0; font-weight: 500; min-width: 90px; font-size: 12px;">Próxima em --s</span>
            </div>
        </div>

        <div id="barra-progresso-container">
            <div id="barra-progresso"></div>
        </div>

        <div id="telas-wrapper"></div>

        <script>
            const links = {links_json};
            const tempos = {tempos_json};
            const nomes = {nomes_json};
            let deveRecarregar = {recarregar_json};
            let indiceAtual = 0;
            let iframes = [];
            let temporizador;
            let estaPausado = false;
            let tempoRestante = 20;
            let tempoTotalPainel = 20;

            const wrapperDiv = document.getElementById('telas-wrapper');
            const infoTexto = document.getElementById('info-texto');
            const contadorTempo = document.getElementById('contador-tempo');
            const barraProgresso = document.getElementById('barra-progresso');
            const btnPause = document.getElementById('btn-pause');
            const btnReloadToggle = document.getElementById('btn-reload-toggle');

            const savedIndex = localStorage.getItem("painel_indice_atual");
            if (savedIndex !== null && parseInt(savedIndex) < links.length) {{
                indiceAtual = parseInt(savedIndex);
            }}

            links.forEach((link, index) => {{
                const container = document.createElement('div');
                container.className = 'iframe-container' + (index === indiceAtual ? ' ativo' : '');
                
                const iframe = document.createElement('iframe');
                iframe.src = link;

                container.appendChild(iframe);
                wrapperDiv.appendChild(container);
                iframes.push({{ container: container, iframe: iframe, link: link }});
            }});

            function atualizarBotaoRecarregarUI() {{
                if (deveRecarregar[indiceAtual]) {{
                    btnReloadToggle.innerText = "🔄 Atualizar: ON";
                    btnReloadToggle.classList.remove("desativado");
                }} else {{
                    btnReloadToggle.innerText = "🔒 Atualizar: OFF";
                    btnReloadToggle.classList.add("desativado");
                }}
            }}

            function atualizarBarraProgresso(progresso) {{
                barraProgresso.style.transition = 'transform 1s linear';
                barraProgresso.style.transform = 'scaleX(' + progresso + ')';
            }}

            function atualizarExibicao() {{
                iframes.forEach((item, i) => {{
                    if (i === indiceAtual) {{
                        item.container.classList.add('ativo');
                    }} else {{
                        item.container.classList.remove('ativo');
                    }}
                }});
                
                const nomePainel = nomes[indiceAtual] || ("Painel " + (indiceAtual + 1));
                infoTexto.innerHTML = "🟢 <b>" + nomePainel + "</b> <i>(" + (indiceAtual + 1) + "/" + links.length + ")</i> - " + tempos[indiceAtual] + "s";
                atualizarBotaoRecarregarUI();
                localStorage.setItem("painel_indice_atual", indiceAtual);
            }}

            function gerenciarAtualizacaoPainelAtual() {{
                const itemAtual = iframes[indiceAtual];
                if (deveRecarregar[indiceAtual]) {{
                    itemAtual.iframe.src = itemAtual.link;
                }}
            }}

            function irParaProxima() {{
                indiceAtual = (indiceAtual + 1) % links.length;
                atualizarExibicao();
                gerenciarAtualizacaoPainelAtual();
                reiniciarTemporizador();
            }}

            function mudarTela(direcao) {{
                indiceAtual = (indiceAtual + direcao + links.length) % links.length;
                atualizarExibicao();
                gerenciarAtualizacaoPainelAtual();
                reiniciarTemporizador();
            }}

            function alternarRecarregamento() {{
                deveRecarregar[indiceAtual] = !deveRecarregar[indiceAtual];
                atualizarBotaoRecarregarUI();
            }}

            function alternarPausa() {{
                estaPausado = !estaPausado;
                if (estaPausado) {{
                    clearInterval(temporizador);
                    btnPause.innerText = "▶️ Retomar";
                    btnPause.classList.add("pausado");
                    contadorTempo.innerText = "⏸️ Pausado";
                    barraProgresso.style.transition = 'none'; // congela barra
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
                
                tempoTotalPainel = tempos[indiceAtual];
                tempoRestante = tempoTotalPainel;
                
                contadorTempo.innerText = "Próxima em " + tempoRestante + "s";
                
                // Reseta a barra para cheia instantaneamente
                barraProgresso.style.transition = 'none';
                barraProgresso.style.transform = 'scaleX(1)';
                
                // Força reflow e aplica a transição gradual
                setTimeout(() => {{
                    if (!estaPausado) {{
                        barraProgresso.style.transition = 'transform ' + tempoTotalPainel + 's linear';
                        barraProgresso.style.transform = 'scaleX(0)';
                    }}
                }}, 50);

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
