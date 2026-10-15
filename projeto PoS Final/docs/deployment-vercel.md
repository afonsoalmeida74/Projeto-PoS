# Deploy na Vercel

## Entry point e diretório raiz

O projeto exporta a instância Flask `app` em `app.py` na raiz. `pyproject.toml` declara também `tool.vercel.entrypoint = "app:app"`, para indicar explicitamente à Vercel o módulo e a variável WSGI.

No painel Vercel, confirma que **Root Directory** aponta para a raiz deste repositório (a pasta que contém `app.py`, `pyproject.toml` e `vercel.json`). Se o erro listar apenas `moto_pos/__main__.py` e `tests/conftest.py`, o deploy provavelmente está a usar uma versão sem o `app.py` da raiz, ou uma Root Directory diferente.

## Base de dados e variáveis

A Vercel precisa de uma base PostgreSQL externa persistente; SQLite local não é adequado ao filesystem efémero das Functions. Provisiona PostgreSQL e configura nos ambientes Vercel necessários:

- `DATABASE_URL`: URL PostgreSQL fornecida pelo serviço de base de dados.
- `SECRET_KEY`: segredo aleatório próprio para cada ambiente.
- `ADMIN_USERNAME` e `ADMIN_PASSWORD`: credenciais iniciais fortes; a palavra-passe tem mínimo de 12 caracteres.
- `COOKIE_SECURE=1` em produção.

Não coloques valores reais destas variáveis no Git nem nesta documentação. O `build.py` inicializa as tabelas e a conta inicial durante o build usando as variáveis disponíveis nesse ambiente. A inicialização das tabelas é idempotente e não altera a palavra-passe de uma conta já criada. Usa bases distintas para Preview e Production.

## Deploy

Com a Vercel CLI instalada e autenticada, a partir da raiz do projeto:

```powershell
vercel.cmd link
vercel.cmd env pull
vercel.cmd deploy --target=preview
```

Depois de validar o preview, publica em produção com `vercel.cmd deploy --prod`. Também podes importar o repositório no painel Vercel. Em ambos os casos, o código com `app.py`, `pyproject.toml` e esta configuração tem de estar presente na origem do deploy.

## Estado e limitações

A configuração local declara o entrypoint e o build. A ligação a uma base PostgreSQL real e o deploy na Vercel dependem de provisionar a base, configurar as variáveis e enviar esta versão do projeto para a origem que a Vercel está a construir; ainda não foram verificados aqui. O adaptador PostgreSQL não tem migrações versionadas nem migração de dados desde SQLite. Antes de utilização real, planeia backups/restauro, monitorização, rotação de credenciais e revisão dos requisitos fiscais e de proteção de dados.
