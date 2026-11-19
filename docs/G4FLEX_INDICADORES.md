# Indicadores e Desempenho · G4Flex

## Tela do painel

O botão **Indicadores**, disponível no Layout S&S e Layout G4Flex, abre uma visualização dedicada sem sair do monitor e sem gerar novas requisições. O botão **Voltar ao atendimento** retorna ao layout anterior.

A tela possui:
- **Agora:** total de atendentes monitorados, disponíveis, em pausa e conversas em atendimento, derivados do snapshot atual após aplicar a exclusão de atendentes fora do suporte.
- **Histórico:** totais da matriz horária, gráfico de abertas versus atendidas, tabela horária completa e **Ranking de filas** (classificação publicada como `ranking_motivos` na versão atual).
- **Estado pendente:** se o robô ainda não envia históricos, a tela informa explicitamente a ausência dos dados. NUNCA cria valores fictícios nem tenta calcular resultados históricos a partir do estado instantâneo.

## Relatório do dia

O botão **Relatório do dia**, dentro da tela Indicadores, gera uma página independente e imprimível contendo data e horário da última captura, totais por faixa horária, matriz horária completa e ranking de filas.

O relatório utiliza a logomarca oficial do Grupo S&S embutida em PNG (`scripts/logo_grupo_ss_oficial.js`), evitando dependências de links externos na impressão. O cabeçalho, os cards, a matriz, o ranking e o rodapé foram refinados para leitura e emissão em **A4 paisagem**. Os títulos foram padronizados como **Resumo dos atendimentos** e **Soma dos atendimentos**. A aplicação continua somando exclusivamente os valores efetivamente recebidos em `resumo.matriz_horaria`. Na nova página, clique **Imprimir / Salvar como PDF** e selecione *Salvar como PDF* no navegador.

- Não faz consultas adicionais ao G4Flex ou Supabase: usa o último snapshot recebido.
- Não inventa um fechamento definitivo; apresenta **dados parciais até a última coleta**.
- A referência temporal é `resumo.indicadores_historicos_coletados_em`, em horário de Fortaleza/CE, com fallback para as datas do snapshot quando necessário.
- O relatório não mistura os indicadores instantâneos individuais do suporte com a matriz histórica geral do G4Flex.
- Se o navegador bloquear abertura de uma nova aba, o usuário recebe um arquivo HTML imprimível como alternativa.
- Caso não exista matriz horária nem ranking, o usuário recebe uma mensagem informando a ausência de dados históricos.

## Contrato de dados aceito pelo painel

Sem alteração de banco, o coletor pode adicionar ao campo JSONB `resumo` da mesma linha `g4flex_monitor_atual`:

```json
{
  "resumo": {
    "matriz_horaria": [
      {
        "horario": "08:00 - 09:00",
        "abertas": 19,
        "atendidas": 17,
        "nao_atendidas": 2,
        "encerradas": 3,
        "abandonadas": 0,
        "tme": "00:01:45",
        "tma": "02:05:10",
        "tmo": "01:49:51",
        "tta": "39:38:28",
        "primeira_resposta": "00:01:58",
        "tmr": "00:02:12",
        "tm_atribuicao": "02:06:56",
        "nivel_servico": "0%",
        "nivel_atendimento": "89.47%",
        "volume_projetado": 0,
        "volume_total": 20
      }
    ],
    "ranking_motivos": [
      {"motivo": "Folha de Pagamento", "quantidade": 19}
    ]
  }
}
```

**Os números acima são apenas exemplos para documentação; não são valores inseridos em produção.** Os nomes das métricas seguem a nomenclatura do relatório G4Flex da captura fornecida pelo usuário. TME, TMA, TMO, TTA etc. são apresentados tal qual a origem, sem definições inferidas.

O ranking exibido como **filas** corresponde atualmente a `ranking_motivos`; a correspondência exata com as filas operacionais do G4Flex ainda precisa ser confirmada. O painel priorizará `ranking_filas` quando o robô passar a fornecer esse campo. A matriz e o ranking do G4Flex podem ter **escopo global**, incluindo pessoas ocultas individualmente do monitor. O painel distingue os históricos globais dos indicadores instantâneos do suporte; **não** denominar dados globais como desempenho exclusivo do suporte.

## Requisitos da captura

O robô Python `1.5.1-py-fil-ind`, em operação em 19/11/2026, já publica a matriz horária e o ranking de motivos no Supabase. A versão `1.6.0-inst` foi utilizada anteriormente, mas não deve ser confundida com o coletor atual. Evitar iniciar um segundo robô e evitar requisições adicionais: ler os elementos da página já aberta, respeitar alterações no DOM e confirmar a integridade da tabela/índices antes de publicar. Não expor credenciais, cookies ou dados brutos de outras páginas.

O `main.py` contém uma cópia integrada de `scripts/g4flex_indicadores.js`, `scripts/g4flex_relatorio_dia.js`, `scripts/g4flex_tooltip_filas.js` e `scripts/g4flex_indicadores.css`. Para atualizar CSS ou JS, execute `python scripts/integrar_g4flex_indicadores.py` após alterar os módulos, valide `node scripts/test_g4flex_indicadores.cjs` e `node scripts/test_g4flex_relatorio_dia.cjs` e `python -m py_compile main.py`.
