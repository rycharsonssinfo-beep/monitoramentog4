<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Monitoramento Pro</title>
    <style>
        /* --- Variáveis de Cores (Tema Claro, Moderno e Clean) --- */
        :root {
            --bg-app: #f4f6f9;         /* Fundo geral da página */
            --bg-card: #ffffff;        /* Fundo da caixa de configuração */
            --bg-input: #f8fafc;       /* Fundo dos campos de texto */
            --text-main: #1e293b;      /* Texto principal escuro */
            --text-muted: #64748b;     /* Texto secundário/ajuda */
            --accent: #2563eb;         /* Azul vibrante moderno */
            --accent-hover: #1d4ed8;   /* Azul escuro ao passar o mouse */
            --danger: #ef4444;         /* Cor para botão de alterar */
            --danger-hover: #dc2626;
            --border: #e2e8f0;         /* Cor das bordas limpas */
            --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body, html { 
            width: 100%; 
            height: 100%; 
            background-color: var(--bg-app); 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            overflow: hidden; 
            color: var(--text-main);
        }

        /* --- TELA 1: Configuração (Centralizada) --- */
        #config-screen {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            opacity: 1;
            transition: opacity 0.4s ease;
        }

        #config-screen.hidden-panel {
            opacity: 0;
            pointer-events: none;
            position: absolute;
        }

        .config-box {
            background: var(--bg-card);
            padding: 40px;
            border-radius: 16px;
            width: 100%;
            max-width: 550px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }

        .app-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .icon-monitor {
            font-size: 36px;
            background: #eff6ff;
            padding: 10px;
            border-radius: 12px;
        }

        .config-box h2 { 
            font-size: 22px; 
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.5px;
        }

        .form-group {
            margin-bottom: 22px;
        }

        .config-box label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: var(--text-main);
            font-size: 14px;
        }

        .config-box textarea, 
        .config-box input[type="number"] {
            width: 100%; 
            padding: 14px; 
            background: var(--bg-input); 
            border: 1px solid var(--border); 
            color: var(--text-main); 
            border-radius: 10px; 
            font-family: 'SF Mono', Menlo, Monaco, Consolas, monospace;
            font-size: 13px;
            transition: all 0.2s;
        }

        .config-box textarea:focus, 
        .config-box input[type="number"]:focus {
            outline: none;
            border-color: var(--accent);
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
        }

        .config-box textarea { 
            height: 160px; 
            resize: none;
            line-height: 1.5;
        }

        ::placeholder { color: var(--text-muted); opacity: 0.6; }

        .btn-start {
            background: var(--accent); 
            color: white; 
            border: none; 
            padding: 15px 20px; 
            font-size: 15px; 
            font-weight: 600; 
            border-radius: 10px; 
            cursor: pointer; 
            width: 100%; 
            transition: all 0.2s ease;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }

        .btn-start:hover { background: var(--accent-hover); transform: translateY(-1px); }
        .btn-start:active { transform: translateY(0); }

        .helper-text {
            margin-top: 15px;
            font-size: 13px;
            color: var(--text-muted);
            text-align: center;
        }

        /* --- TELA 2: Exibição em Rotação --- */
        #display-screen {
            display: none;
            width: 100%; 
            height: 100%; 
            position: relative;
            opacity: 0;
            transition: opacity 0.4s ease;
        }

        #display-screen.active-display {
            opacity: 1;
        }

        iframe { 
            width: 100%; 
            height: 100%; 
            border: none; 
            display: block; 
            background: #ffffff; 
        }
        
        /* Barra de Status Estilizada (Rodapé Flutuante Clean) */
        #status-bar {
            position: fixed; 
            bottom: 25px; 
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(255, 255, 255, 0.9);
            color: var(--text-main); 
            padding: 10px 22px; 
            border-radius: 40px; 
            display: flex; 
            align-items: center; 
            gap: 18px;
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
            z-index: 9999;
            border: 1px solid var(--border);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            backdrop-filter: blur(8px);
        }

        #status-bar.show-bar {
            transform: translateX(-50%) translateY(0); 
        }

        .status-info {
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
        }

        .status-divider {
            width: 1px;
            height: 16px;
            background-color: var(--border);
        }

        .tip-text {
            font-size: 12px;
            color: var(--text-muted);
        }

        .btn-config {
            background: #f1f5f9;
            border: 1px solid var(--border);
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 20px;
            cursor: pointer;
            color: var(--text-muted);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .btn-config:hover {
            background: var(--danger);
            border-color: var(--danger);
            color: white;
        }

    </style>
</head>
<body>

    <!-- TELA 1: Configuração -->
    <div id="config-screen">
        <div class="config-box">
            <div class="app-header">
                <div class="icon-monitor">📊</div>
                <h2>Painel de Monitoramento</h2>
            </div>
            
            <div class="form-group">
                <label for="links-input">Links das páginas (um por linha):</label>
                <textarea id="links-input" placeholder="https://exemplo.com/painel-1&#10;https://exemplo.com/painel-2"></textarea>
            </div>
            
            <div class="form-group">
                <label for="tempo-input">Tempo de exibição de cada tela (segundos):</label>
                <input type="number" id="tempo-input" value="30" min="5" step="5">
            </div>

            <button class="btn-start" onclick="iniciarPainel()">
                Iniciar Apresentação
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            </button>
            
            <p class="helper-text">Os links salvos ficam memorizados no navegador.</p>
        </div>
    </div>

    <!-- TELA 2: Exibição em Rotação -->
    <div id="display-screen">
        <iframe id="tela-monitor" src=""></iframe>
        
        <div id="status-bar">
            <div class="status-info" id="info-link">Carregando...</div>
            <div class="status-divider"></div>
            <div class="tip-text">Pressione F11 para Tela Cheia</div>
            <button class="btn-config" onclick="pararPainel()">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                Alterar Links
            </button>
        </div>
    </div>

    <script>
        let indiceAtual = 0;
        let intervaloId = null;
        let linksArray = [];
        let tempoSegundos = 30;
        let barraTimeout;

        const configScreen = document.getElementById('config-screen');
        const displayScreen = document.getElementById('display-screen');
        const linksInput = document.getElementById('links-input');
        const tempoInput = document.getElementById('tempo-input');
        const iframe = document.getElementById('tela-monitor');
        const infoLink = document.getElementById('info-link');
        const statusBar = document.getElementById('status-bar');

        window.onload = function() {
            const salvoLinks = localStorage.getItem('painel_links');
            const salvoTempo = localStorage.getItem('painel_tempo');
            if (salvoLinks) linksInput.value = salvoLinks;
            if (salvoTempo) tempoInput.value = salvoTempo;
        };

        function iniciarPainel() {
            const textoLinks = linksInput.value.trim();
            tempoSegundos = parseInt(tempoInput.value) || 30;

            if (!textoLinks) {
                alert('Por favor, insira pelo menos um link.');
                return;
            }

            linksArray = textoLinks.split('\n').map(l => l.trim()).filter(l => l.length > 0);

            if (linksArray.length === 0) {
                alert('Nenhum link válido encontrado.');
                return;
            }

            localStorage.setItem('painel_links', textoLinks);
            localStorage.setItem('painel_tempo', tempoSegundos);

            configScreen.classList.add('hidden-panel');
            setTimeout(() => {
                displayScreen.style.display = 'block';
                displayScreen.offsetWidth; 
                displayScreen.classList.add('active-display');
            }, 50);

            indiceAtual = 0;
            proximaTela();

            if (intervaloId) clearInterval(intervaloId);
            intervaloId = setInterval(proximaTela, tempoSegundos * 1000);
        }

        function proximaTela() {
            if (linksArray.length === 0) return;

            iframe.src = linksArray[indiceAtual];
            infoLink.innerText = `Tela ${indiceAtual + 1} de ${linksArray.length}`;

            indiceAtual = (indiceAtual + 1) % linksArray.length;
        }

        function pararPainel() {
            if (intervaloId) clearInterval(intervaloId);
            
            displayScreen.classList.remove('active-display');
            setTimeout(() => {
                displayScreen.style.display = 'none';
                configScreen.classList.remove('hidden-panel');
            }, 400);
        }

        document.addEventListener('mousemove', () => {
            if (displayScreen.style.display === 'block') {
                statusBar.classList.add('show-bar');
                clearTimeout(barraTimeout);
                barraTimeout = setTimeout(() => {
                    statusBar.classList.remove('show-bar');
                }, 3000);
            }
        });
    </script>

</body>
</html>
