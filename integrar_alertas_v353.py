#!/usr/bin/env python3
"""Aplica integração dos alertas v3.53.0 ao main.py, sem mudar o coletor/Supabase.
Execute na raiz do repositório: python integrar_alertas_v353.py
Após aplicar, reinicie o Streamlit e teste pelo botão 'Testar alerta'.
"""
from pathlib import Path
import sys

main = Path(__file__).with_name("main.py")
script = Path(__file__).with_name("portal_alerts_v353.js")
if not main.is_file() or not script.is_file():
    sys.exit("main.py e portal_alerts_v353.js devem estar no mesmo diretório.")
source = main.read_text(encoding="utf-8")
if "ssPortalAlerts353.mount(host" in source:
    print("Integração já aplicada.")
    sys.exit(0)
marker = "  host.querySelectorAll('[data-portal-mode]').forEach(btn=>btn.onclick=()=>portalChooseService(btn.dataset.portalMode));"
poll = "  finally{portalBusy=false;portalDrawAll();}\n}\nfunction portalChooseService(mode)"
js_tag = "    html_painel = html_painel.replace(\"__PAYLOAD_B64__\", payload_b64)"
if marker not in source or poll not in source or js_tag not in source:
    sys.exit("Marcadores não encontrados; o arquivo mudou. Integração cancelada sem alterar main.py.")
source = source.replace(
    marker,
    "  window.ssPortalAlerts353?.mount(host, settings.mascotAlert || '');\n" + marker,
    1,
)
source = source.replace(
    poll,
    "  finally{portalBusy=false;portalDrawAll();window.ssPortalAlerts353?.check(portalDatas.portais, settings.mascotAlert || '');}\n}\nfunction portalChooseService(mode)",
    1,
)
# Insere o JS ao criar o HTML Streamlit, sem rede externa e com código local versionado.
insertion = (
    "    html_painel = html_painel.replace("
    '"function portalStart(host){", '
    'Path(__file__).with_name("portal_alerts_v353.js").read_text(encoding="utf-8") + "\\nfunction portalStart(host){")\n'
)
source = source.replace(js_tag, insertion + js_tag, 1)
# Preserva a estrutura original: se houver mais de uma instância HTML, só o painel é alterado.
compile(source, str(main), "exec")
backup = main.with_suffix(".py.pre_alert_v353.bak")
if not backup.exists():
    backup.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
main.write_text(source, encoding="utf-8")
print("Integração v3.53.0 aplicada. Backup:", backup.name)
