# Continuidade no Codex — Monitor Grupo S&S

> Atualizado em 19/11/2026. Documento de transição para continuar o desenvolvimento **somente no GitHub e no Supabase**, sem operar os robôs instalados no Windows.

## 1. Onde começar

| Item | Referência |
|---|---|
| Repositório | [rycharsonssinfo-beep/monitoramentog4](https://github.com/rycharsonssinfo-beep/monitoramentog4) |
| Branch base | `main` |
| Último PR funcional incorporado | [#17 — Relatório G4Flex com logomarca oficial](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/17) |
| SHA de referência antes deste documento | `2081f2358d4071e7b447e684d3fd7decba8b5eff` |
| Supabase (referência de projeto, **não é chave**) | `gtkeacejcplkrhpbmkoj` |
| Tabela G4Flex confirmada | `public.g4flex_monitor_atual` |
| Documentação do relatório | `docs/G4FLEX_INDICADORES.md` |
| Instruções do agente | `AGENTS.md` |

A versão atual é a que estiver em `main` no momento da tarefa. O SHA acima serve apenas como marco de transição, **não** como instrução para voltar versões.

## 2. Objetivo e restrições desta etapa

O usuário desenvolve o Monitor Grupo S&S, aplicação web Streamlit que agrega indicadores de G4Flex e outros sistemas/serviços municipais.

**Escopo atual**: evoluir a interface web e, com confirmação explícita, investigar/propor mudanças no Supabase. **Não** acessar, modificar, iniciar, parar ou compilar os robôs Python/`.exe` que executam na máquina Windows do usuário. Não tocar na pasta de sessão nem nas credenciais do coletor.

**Requisitos de qualidade**:
- Preservar os demais módulos de monitoramento, login, permissões e notificações.
- Evitar novas requisições ao G4Flex/Veículos/Portais ou polling desnecessário.
- Priorizar alterações em módulos fonte de `scripts/` e sincronização com `main.py`.
- Criar PRs verificáveis, com testes e notas de implantação; não publicar em `main` automaticamente sem a autorização do usuário.

## 3. Histórico recente já entregue na main

| PR | Mudança principal |
|---:|---|
| [#9](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/9) | Mascote PNG exclusivo e borda verde no alerta de recuperação dos portais |
| [#10](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/10) | Cores de situação do atendente: pausa amarela; atribuição vermelha; ligação roxa preservada, Lista/Cards |
| [#11](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/11) | Filtro de apresentação para ocultar Cislena Cisne, Marla Lima e Emanuela Costa na tela G4Flex (não remove dados do banco) |
| [#12](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/12) | Tooltip preparado para exibir `filas_logadas`, distinto da primeira fila e da conversa atual |
| [#13](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/13) | Nova tela de Indicadores: KPI instantâneo, matriz horária, gráfico, ranking |
| [#14](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/14) | Melhorias no tooltip e correção de duplicidade do botão Indicadores |
| [#15](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/15) | Estado explícito **Aguardando captura** quando não há filas por atendente |
| [#16](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/16) | Ranking de filas e botão **Relatório do dia** com impressão/Salvar como PDF |
| [#17](https://github.com/rycharsonssinfo-beep/monitoramentog4/pull/17) | Logomarca oficial PNG no relatório, melhorias visuais A4 paisagem, textos **Resumo dos atendimentos** e **Soma dos atendimentos** |

**Cuidado:** PRs registram alterações realizadas, não comprovam que cada funcionalidade foi homologada visualmente em produção. Sempre conferir código/estado atual, dados recebidos e interface.

## 4. G4Flex — fontes e distinções importantes

O snapshot `public.g4flex_monitor_atual` tem dados de atendentes e de `resumo` utilizados pelo painel. Conferir sempre o esquema real antes de consultar.

- `atendentes`: nomes, status, atendimentos e, quando disponíveis, `filas_logadas`, horário da coleta dessas filas, `fila_exibida` e `fila_atendimento_atual`. **Não** substituir filas logadas pela primeira fila mostrada embaixo do nome.
- `resumo.matriz_horaria`: dados por período para gráficos/tabela e cálculo de agregados, quando publicados.
- `resumo.ranking_filas`: fonte preferencial de ranking de filas, se disponível.
- `resumo.ranking_motivos`: classificação existente no G4Flex usada como compatibilidade visual. **Não** afirmar que é o mesmo que filas operacionais sem validação.
- `resumo.indicadores_historicos_coletados_em`: referência de atualização dos históricos.
- KPIs instantâneos da equipe de suporte devem respeitar o filtro de nomes excluídos; indicadores históricos globais podem ser de toda a plataforma e precisam de rotulagem clara.

O filtro por nomes é apenas visual; **não** representa autenticação ou uma política RLS do Supabase.

### Filas logadas

O código do tooltip está no painel web, mas depende de o coletor produzir `filas_logadas`. A coleta no Windows foi discutida em outra conversa e não está dentro do escopo atual. Não prometer a atualização do robô local nem inventar conteúdo quando a lista não estiver no snapshot.

### Relatório do dia

- Gerador: `scripts/g4flex_relatorio_dia.js`.
- Interface: `scripts/g4flex_indicadores.js` e `scripts/g4flex_indicadores.css`.
- Logomarca oficial sem rede adicional: `scripts/logo_grupo_ss_oficial.js`.
- Integrador para `main.py`: `scripts/integrar_g4flex_indicadores.py`.
- Tests: `scripts/test_g4flex_indicadores.cjs`, `scripts/test_g4flex_relatorio_dia.cjs`.
- Emissão em A4 paisagem via HTML imprimível e opção do navegador **Imprimir / Salvar como PDF**.
- Texto padrão do resumo: **Resumo dos atendimentos** / **Soma dos atendimentos**.
- Os relatórios são **parciais até a última coleta**; não são fechamento definitivo de dia sem validação da fonte.

## 5. Outras regras que não podem regredir

- Alerta de portais: indisponibilidade com identidade vermelha; recuperação com mascote específico e identidade verde; preservar regras de disparo/fechamento existentes.
- Visualização Lista e Cards do G4Flex: barra colorida próxima à foto; ligação roxa tem precedência; pausa amarela e atribuição vermelha quando aplicável.
- Preservar os módulos da aplicação para SIM, Fluxus, Portais do Contribuinte e Veículos.
- O usuário relatou preocupação real com excesso de requisições aos sistemas Veículos. **Não** reativar robôs ou aumentar carga por conta própria.

## 6. Primeira tarefa recomendada para Codex

1. Conectar o repositório do GitHub e selecionar a branch `main`.
2. Ler `AGENTS.md`, este documento e `docs/G4FLEX_INDICADORES.md`.
3. Inspecionar a organização de `main.py`, as fontes `scripts/` e os testes atuais.
4. Resumir em português quais mudanças estão em produção, quais requerem validação e onde há risco de regressão.
5. Opcionalmente configurar conexão ao **projeto Supabase** em modo **somente leitura**, com autenticação própria no Codex; confirmar esquema sem modificar dados.
6. Propor um plano de melhorias por prioridade, com estimativa de impacto em performance e banco.
7. **Aguardar aprovação** antes de qualquer edição no código, criação de migration, mudança de permissões ou merge.

## 7. Como configurar o Supabase com segurança

O Supabase não é 'transportado' automaticamente junto com a autenticação desta conversa. Configurar e autorizar o conector/MCP no Codex, restringindo-o ao projeto escolhido e começando com `read_only=true`.

A documentação oficial do Supabase recomenda limitar o escopo do MCP por `project_ref`, usar apenas os grupos de ferramentas necessários e começar com leitura. Não inserir chaves `service_role`, senhas ou tokens em prompts ou arquivos versionados.

**Princípio de continuidade:** GitHub é a fonte do código; Supabase é a fonte dos dados/estado do banco; esta documentação preserva decisões de produto e limitações. Sempre validar com a fonte antes de assumir que um recurso está em produção.
