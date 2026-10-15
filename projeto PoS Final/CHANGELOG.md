# Changelog

## [0.2.0] - 2026-10-12

### Adicionado
- Entry point WSGI, assets e configuração para deteção Flask da Vercel.
- Adaptador PostgreSQL por `DATABASE_URL`, mantendo SQLite para desenvolvimento local.
- Bootstrap idempotente do esquema e conta inicial durante o build Vercel.
- Instruções de provisioning, bootstrap e deploy em `docs/deployment-vercel.md`.
- Guard para impedir execução na Vercel sem base persistente configurada.

### Segurança
- Placeholders seguros no README e `.env.example`; `.env.local` e `.vercel` ignorados pelo Git.

### Verificação
- 9 testes passaram em Python 3.14.8; sintaxe Python compilada e `vercel.json` validado como JSON.
- PostgreSQL externo e deploy Vercel ainda não configurados nem verificados.

## [0.1.0] - 2026-10-08

### Adicionado
- Estrutura inicial da aplicação Flask com persistência SQLite.
- Login com palavra-passe com hash, sessão e proteção CSRF.
- Registo e consulta de motas e clientes.
- Registo transacional de venda, atualização de stock, auditoria, histórico e recibo interno.
- Documentação de instalação, decisões, segurança e limitações.
- Testes automatizados para os principais fluxos e invariantes.

### Verificação
- Não executada nesta sessão: `python.exe` não estava acessível no ambiente. A execução dos testes e do lint permanece pendente.
