# Monitor Grupo S&S — Login v3.55.0

## Novo visual
- Tela de acesso em duas colunas: ilustração/mascote já existente no projeto à esquerda; formulário funcional à direita
- Tipografia com hierarquia ampliada, botão primário azul e apresentação de recursos do Monitor
- Fundo com gradientes em azul/ciano e cartão com sombra sutil
- Opções Entrar e Solicitar acesso estilizadas como abas, preservando o controle nativo de rádio e o foco do teclado
- Responsivo em telas até 1000 px e até 600 px, sem dependência de CDN

## Funcionalidades preservadas
- Autenticação Supabase Auth, tratamento de erros e recuperação de sessão
- Opção Permanecer conectado, apresentação/ocultação da senha e validação existente
- Solicitação de acesso com as duas alternativas atuais (incluindo envio via navegador)
- Fluxo de recuperação/definição de senha
- Monitoramento SIM, G4Flex, Portais, Fluxus, Veículos, notificações e permissões

## Como conferir
1. Abra o endereço atual da aplicação após o deploy.
2. Em uma janela sem sessão ativa, atualize com Ctrl + F5 e confira a nova distribuição visual.
3. Verifique o formulário de Entrar e o alternador Solicitar acesso.
4. Teste em desktop e celular; garanta que formulário e ações não sejam cortados.

**Homologação:** testes automatizados verificam sintaxe, estrutura das duas colunas, existência dos fluxos anteriores e regressão do monitor. Renderização no navegador e login real devem ser validados pelo operador; não foram usados dados de usuários nem credenciais reais nos testes.
