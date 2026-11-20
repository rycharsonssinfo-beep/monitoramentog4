# AGENTS.md — Monitor Grupo S&S

Estas instruções orientam agentes de programação (incluindo Codex) que atuam neste repositório.

## Escopo atual autorizado

- Trabalhar **somente** no projeto hospedado no GitHub e, após autorização explícita do usuário, na integração com o Supabase.
- **Não** operar nem modificar os robôs/coletores locais instalados no Windows (por exemplo, `C:\Monitor_G4Flex`, `MonitorG4Flex.exe`, pastas de sessão Playwright, serviços do Windows ou scripts de inicialização).
- **Não** aumentar a frequência, simultaneidade ou volume de requisições ao G4Flex, aos Portais do Contribuinte ou aos sistemas de Veículos.
- No primeiro contato, ler `docs/CODEX_CONTINUIDADE.md` e `docs/G4FLEX_INDICADORES.md`, revisar a branch `main` e apresentar um diagnóstico antes de editar arquivos ou banco.
- Preferir **branch específica + testes + pull request**. Não efetuar merge para `main` sem aprovação do usuário.

## Estrutura e regras de implementação

- A aplicação principal é Streamlit, concentrada em `main.py`. A tela G4Flex possui JavaScript/CSS incorporado no arquivo principal e módulos fonte em `scripts/`.
- O integrador `scripts/integrar_g4flex_indicadores.py` sincroniza o código dos módulos com `main.py`. Após editar módulos, atualizar a cópia incorporada e executar os testes correspondentes.
- Arquivos relevantes: `scripts/g4flex_indicadores.js`, `scripts/g4flex_indicadores.css`, `scripts/g4flex_relatorio_dia.js`, `scripts/g4flex_tooltip_filas.js`, `scripts/logo_grupo_ss_oficial.js`.
- Preservar os módulos existentes SIM, Fluxus, Veículos, Portais do Contribuinte, G4Flex, autenticação, permissões e alertas.
- O painel de atendimento G4Flex exclui visualmente três nomes fora da equipe de suporte; preservar esse filtro e o fato de que exclusão visual **não** é regra de segurança de banco.
- Cores do estado do atendente: **ligação roxa**, **pausa amarela**, **atribuições pendentes vermelhas**. Preservar a barra lateral junto à foto e as visualizações Lista/Cards.
- Não assumir que a primeira fila exibida no cartão é a fila da conversa atual; `filas_logadas` é uma lista distinta.
- O relatório diário usa dados já recebidos no snapshot. **Não** inventar números, equivalência entre filas e motivos ou dados ainda não coletados.
- O ranking pode vir de `resumo.ranking_filas` ou, por compatibilidade, `resumo.ranking_motivos`. A equivalência com filas operacionais ainda requer confirmação.
- Manter a logomarca oficial do projeto em relatórios e a opção **Imprimir/Salvar como PDF**.

## Supabase: segurança e rastreabilidade

- Projeto utilizado pelo painel G4Flex: `gtkeacejcplkrhpbmkoj`; tabela principal conhecida `public.g4flex_monitor_atual`.
- A ligação do Codex ao Supabase deve ser **feita e autorizada separadamente**. Começar com acesso **somente leitura**, restrito ao projeto, e consultar os dados antes de propor mudanças.
- Não modificar tabelas, RLS, políticas, dados, funções, secrets, autenticação ou permissões sem pedido e aprovação explícita.
- Antes de qualquer mudança aprovada no banco: verificar esquema real, fazer proposta de migração, avaliar impacto e rollback, validar em ambiente seguro e confirmar que backups estão disponíveis.
- Não inserir tokens, senhas, strings de conexão ou `service_role` no código, commits, documentação ou respostas.
- Não usar `Supabase` ou rede externa como substituto para testes locais de lógica e UI quando fixtures são suficientes.

## Verificação antes de PR

- `node --check scripts/g4flex_indicadores.js`
- `node --check scripts/g4flex_relatorio_dia.js`
- `node --check scripts/g4flex_tooltip_filas.js`
- `node scripts/test_g4flex_indicadores.cjs`
- `node scripts/test_g4flex_relatorio_dia.cjs`
- `python scripts/integrar_g4flex_indicadores.py`
- `python -m py_compile main.py`
- `git diff --check`
- Validar que `main.py` e os módulos em `scripts/` permaneçam sincronizados.
- Descrever o que foi testado e o que ainda exige verificação visual no navegador/produção.

**Documento de transição:** `docs/CODEX_CONTINUIDADE.md`.
