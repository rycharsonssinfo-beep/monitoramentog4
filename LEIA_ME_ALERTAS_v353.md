
## Atualização de interface v3.54.0 — Alertas globais e barra segura

- O monitor consulta os Portais do Contribuinte a cada **15 segundos**, inclusive quando outro painel está em exibição; cada monitor aberto faz sua própria consulta ao Supabase e recebe seu aviso local.
- As notificações **somem automaticamente em 20 segundos** (padrão); em **Alertas → Configurações**, o período pode ser escolhido entre 10, 15, 20, 30 ou 45 segundos.
- A regra de **queda confirmada há 10 minutos**, a proteção contra dados desatualizados, os avisos de recuperação e o controle de duplicidade foram mantidos.
- O indicador de duração permanece grande e o mascote original continua presente.
- A área dos painéis reserva um espaço fixo quando a barra está na parte superior (ou inferior): o cabeçalho não é coberto quando os controles aparecem e o iframe não sofre redimensionamento ao abrir/fechar a barra.
- Telas em computadores e navegadores distintos precisam abrir a mesma versão do Monitor, estar conectadas e ter as notificações habilitadas; ao implantar, atualize a aplicação **uma vez em cada tela**. O áudio poderá exigir interação local em cada navegador.
- O teste automatizado simula dois monitores independentes, descarte e fechamento automático de alertas, além dos testes de regressão do Mapa de Sistemas.

# Monitor Grupo S&S — Alertas dos Portais v3.53.0

## O que foi integrado
O arquivo principal da raiz, **main.py**, inicia automaticamente o controlador
portal_alerts_v353.js. O monitor já instalado fornece informações de
portais_monitor_atual (Supabase), sem criar tabelas ou alterar o coletor.

- Alerta visual com mascote de indisponibilidade usado pelo próprio Monitor S&S.
- Gatilho padrão: portal com estado **offline**, verificado recentemente, e
  duração confirmada de pelo menos **10 minutos** desde **mudou_em**.
- O anúncio não dispara por uma simples falha na consulta ao Supabase, nem
  para dados sem atualização recente (mais de 3 minutos).
- Som de aviso e configurações de volume/repetição.
- Aviso opcional de recuperação, inclusive se o alerta anterior foi silenciado.
- Fila de avisos de recuperação: quando vários municípios voltam simultaneamente, nenhum dos avisos é descartado.
- Carregamento do mascote já existente na Central de Comunicados como alternativa ao mascote configurado.
- Memória local para não reapresentar a mesma queda após fechar a janela.
- Enquanto o Monitor está aberto, o estado dos portais é consultado em segundo
  plano a cada 60 segundos quando não há coleta recente pela tela de portais.
- Não afeta as consultas dos módulos Fluxus, Veículos e SIM.

## Testes automatizados disponíveis
Executar a partir da raiz:

```bash
node scripts/test_portal_alerts_v353.cjs
node scripts/test_portal_alerts_homologacao_v353.cjs
```

A validação automatizada verifica regras de tempo, dados recentes, áudio simulado, avisos repetidos, várias recuperações e consulta em segundo plano. O GitHub Actions também confere a sintaxe Python/JavaScript, a integração única no `main.py` e os testes já existentes do mapa. **Esses testes não substituem a homologação visual e sonora em um navegador real.**

## Como homologar
1. Na branch de desenvolvimento, abrir **Iniciar Monitoramento**.
2. Na tela **Portal do Contribuinte**, localizar os botões **Alertas** e
   **Testar alerta**, na barra superior.
3. Clicar em **Testar alerta** e depois em **Testar som**. Essa interação pode
   ser necessária para o navegador autorizar áudio.
4. Abrir **Alertas** e conferir as preferências: ativado, tempo mínimo
   5/10/15/30 min (padrão 10), som, volume, repetição e recuperação.
5. Usar uma ocorrência real confirmada há mais de 10 min para verificar o modal.
   Conferir os dados de HTTP, município, última verificação e horário de início.
6. Fechar/silenciar e observar se o mesmo incidente não reaparece.
7. Confirmar o retorno do portal e verificar o aviso de recuperação.
8. Testar a atualização com outro módulo do monitor em exibição.

## Observações
- As opções e a memória de alertas são locais ao navegador e não sincronizam
  confirmações entre computadores.
- O alerta é exibido dentro do Monitor aberto; não é notificação push do
  sistema operacional quando a aba/browser está fechado.
- Navegadores podem bloquear a reprodução automática de áudio. Para autorizar,
  clicar no botão de teste com o navegador aberto.
- Não foi feito merge para a branch main. Validar em ambiente de homologação
  antes de publicar em produção.

## Arquivos
- main.py — integração na aplicação principal.
- portal_alerts_v353.js — interface, regras, áudio e persistência local.
- integrar_alertas_v353.py — patch idempotente, se necessário refazer.
- scripts/test_portal_alerts_v353.cjs — testes de regras de elegibilidade.
- scripts/test_portal_alerts_homologacao_v353.cjs — testes de ponta a ponta simulados de interface, áudio e notificações.
- .github/workflows/integrar_alertas_v353.yml — integração/validação automatizada.
