# Indicadores e Desempenho · G4Flex

## Tela do painel

O botão **Indicadores**, disponível no Layout S&S e Layout G4Flex, abre uma visualização dedicada sem sair do monitor e sem gerar novas requisições. O botão **Voltar ao atendimento** retorna ao layout anterior.

A tela possui:
- **Agora:** total de atendentes monitorados, disponíveis, em pausa e conversas em atendimento, derivados do snapshot atual após aplicar a exclusão de atendentes fora do suporte.
- **Histórico:** totais da matriz horária, gráfico de abertas versus atendidas, tabela horária completa e ranking dos principais motivos.
- **Estado pendente:** se o robô ainda não envia históricos, a tela informa explicitamente a ausência dos dados. NUNCA cria valores fictícios nem tenta calcular resultados históricos a partir do estado instantâneo.

## Contrato de dados para futura atualização do coletor Windows

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

A matriz e o ranking do G4Flex podem ter **escopo global**, incluindo pessoas ocultas individualmente do monitor. O painel distingue os históricos globais dos indicadores instantâneos do suporte; **não** denominar dados globais como desempenho exclusivo do suporte.

## Requisitos da captura

A versão atual `1.6.0-inst` envia somente resumo instantâneo; os históricos não estão disponíveis no Supabase em novembro de 2026. A captura da matriz e do ranking precisa ser integrada ao coletor instalado no Windows e recompilada no `.exe`. Evitar iniciar um segundo robô e evitar requisições adicionais: ler os elementos da página já aberta, respeitar alterações no DOM e confirmar a integridade da tabela/índices antes de publicar. Não expor credenciais, cookies ou dados brutos de outras páginas.

O `main.py` contém uma cópia integrada de `scripts/g4flex_indicadores.js` e `scripts/g4flex_indicadores.css`. Para atualizar CSS ou JS, execute `python scripts/integrar_g4flex_indicadores.py` após alterar os módulos, valide `node scripts/test_g4flex_indicadores.cjs` e `python -m py_compile main.py`.
