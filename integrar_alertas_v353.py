#!/usr/bin/env python3
"""Integra alertas dos Portais do Contribuinte ao main.py da raiz (v3.53.0).

Execução: python integrar_alertas_v353.py
Não exige novas tabelas; utiliza dados existentes do monitoramento no Supabase.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
main = root / "main.py"
javascript = root / "portal_alerts_v353.js"

if not main.is_file() or not javascript.is_file():
    sys.exit("Arquivos main.py e portal_alerts_v353.js não encontrados na raiz.")

source = main.read_text(encoding="utf-8")
# Quando a integração já existe, atualiza somente as referências ao mascote,
# sem duplicar a inicialização, os controles nem as leituras.
if 'window.ssPortalAlerts353.start({' in source:
    replacements = {
        "window.ssPortalAlerts353?.mount(host, settings.mascotAlert || '');":
            "window.ssPortalAlerts353?.mount(host, settings.mascotAlert || '__MASCOTE_COMUNICADO_DATA_URI__');",
        "mascot:settings.mascotAlert||''":
            "mascot:settings.mascotAlert||'__MASCOTE_COMUNICADO_DATA_URI__'",
    }
    changed = False
    for old, new in replacements.items():
        if old in source:
            if source.count(old) != 1:
                sys.exit("Marcador de mascote duplicado; main.py não alterado.")
            source = source.replace(old, new, 1)
            changed = True
        elif new not in source:
            sys.exit("Referência de mascote inesperada; main.py não alterado.")
    compile(source, str(main), "exec")
    if changed:
        main.write_text(source, encoding="utf-8")
    print("Integração v3.53.0 validada; mascote preservado.", "Atualizada." if changed else "Sem alterações.")
    sys.exit(0)

anchors = {
    "mount": "  host.querySelectorAll('[data-portal-mode]').forEach(btn=>btn.onclick=()=>portalChooseService(btn.dataset.portalMode));",
    "receive": "    portalDatas[mode]=data;",
    "start": "function portalStart(host){",
    "html": '    html_painel = html_painel.replace("__PAYLOAD_B64__", payload_b64)',
}
for name, value in anchors.items():
    if source.count(value) != 1:
        sys.exit(f"Marcador {name} ausente ou ambíguo. main.py mantido inalterado.")

# Usa a própria coleta do painel, sem requisições extras.
source = source.replace(
    anchors["receive"],
    anchors["receive"] + "\n    if(mode==='portais')window.ssPortalAlerts353?.receive(data);",
    1,
)

# Insere controles visuais no cabeçalho apenas depois da construção do DOM.
source = source.replace(
    anchors["mount"],
    "  window.ssPortalAlerts353?.mount(host, settings.mascotAlert || '__MASCOTE_COMUNICADO_DATA_URI__');\n" + anchors["mount"],
    1,
)

# Adiciona o controlador imediatamente antes do módulo de abertura dos portais.
# A consulta de 60 s é independente da aba selecionada (SIM/Fluxus/Veículos).
boot = (
    "window.ssPortalAlerts353.start({"
    "mascot:settings.mascotAlert||'__MASCOTE_COMUNICADO_DATA_URI__',"
    "state:portalState,"
    "fetch:()=>portalFetchTable('portais_monitor_atual',"
    "'id,municipio,uf,url,estado,ultima_verificacao,ultima_online,http_status,latencia_ms,detalhe,mudou_em',"
    "'order=municipio.asc&limit=500')"
    "});"
)
inject = (
    '    html_painel = html_painel.replace(\n'
    '        "function portalStart(host){",\n'
    '        Path(__file__).with_name("portal_alerts_v353.js").read_text(encoding="utf-8")\n'
    '        + "\\n' + boot + '\\nfunction portalStart(host){",\n'
    '        1,\n'
    '    )\n'
)
source = source.replace(anchors["html"], inject + anchors["html"], 1)

# Evita sintaxe Python inválida e mudanças parciais.
compile(source, str(main), "exec")
main.write_text(source, encoding="utf-8")
print("Integração v3.53.0 concluída no main.py da raiz.")
