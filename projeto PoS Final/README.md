# Moto PoS

Aplicação web local para apoiar as operações de um stand de motas novas e usadas. Esta versão inicial permite gerir inventário e clientes, registar uma venda de uma única mota, consultar o histórico e imprimir um comprovativo interno.

## Requisitos

- Python 3.11 ou superior
- pip

## Instalação e arranque (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edite `.env` e defina `SECRET_KEY` com uma chave aleatória de pelo menos 32 caracteres e `ADMIN_PASSWORD` com uma palavra-passe forte. O ficheiro `.env` não é carregado automaticamente: antes de executar, exporte os valores no terminal atual:

```powershell
$env:SECRET_KEY = "REPLACE_WITH_RANDOM_SECRET_OF_32_PLUS_CHARACTERS"
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "CHOOSE_A_STRONG_PASSWORD"
$env:DATABASE_PATH = "instance/moto_pos.sqlite3"
flask --app moto_pos.app init-db
flask --app moto_pos.app run
```

Abra `http://127.0.0.1:5000`. O servidor de desenvolvimento Flask destina-se a desenvolvimento local, não a produção. Configure `COOKIE_SECURE=1` quando servir por HTTPS.

## Verificação

```powershell
python -m pytest
python -m ruff check .
```

Os testes cobrem acesso autenticado, CSRF, unicidade do VIN, venda, recibo, atualização de estado e prevenção de venda repetida. A execução efetiva depende de Python e das dependências instaladas.

## Estrutura

```text
moto_pos/        Aplicação Flask, persistência e configuração
  templates/     Páginas HTML
public/          Assets estáticos servidos localmente e pela Vercel
tests/           Testes automatizados
docs/            Decisões, segurança e operação
```

## Âmbito e limitações atuais

- O sistema regista o método declarado de pagamento; não processa transações nem guarda dados de cartões.
- O comprovativo é interno e não substitui fatura fiscal. Integração fiscal, faturação legal e requisitos contabilísticos carecem de análise própria antes de utilização comercial.
- Não existem ainda gestão de utilizadores/roles, edição ou anulação de vendas, devoluções, exportação, cópias de segurança automatizadas, migrações versionadas nem integração com fornecedores.
- A aplicação não está preparada para publicação direta na Internet. Consulte [docs/security/security.md](docs/security/security.md).
