# Moto PoS

Aplicação web de ponto de venda para apoiar a operação diária de um stand de motas novas e usadas. O projeto é uma primeira versão académica/prototípica: permite manter inventário e clientes, registar a venda de uma mota e consultar o histórico com um comprovativo interno.

> **Estado:** adequado a desenvolvimento local e demonstração. Não considerar pronto para operação comercial ou produção sem validar requisitos fiscais, privacidade, contas, cópias de segurança, deployment e segurança operacional.

## Índice

- [O que a aplicação faz](#o-que-a-aplicação-faz)
- [Tecnologias e arquitetura](#tecnologias-e-arquitetura)
- [Requisitos](#requisitos)
- [Instalação e arranque local no Windows](#instalação-e-arranque-local-no-windows)
- [Testes e qualidade](#testes-e-qualidade)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Segurança e dados](#segurança-e-dados)
- [Limitações e decisões pendentes](#limitações-e-decisões-pendentes)
- [Deployment](#deployment)
- [Documentação do projeto](#documentação-do-projeto)
- [Resolução de problemas](#resolução-de-problemas)

## O que a aplicação faz

Depois de iniciar sessão, o operador pode:

- consultar um resumo do inventário disponível, das vendas e do valor vendido;
- registar motas novas ou usadas e consultar o inventário;
- registar clientes e consultar a lista de clientes;
- vender uma mota disponível a um cliente, indicando o método de pagamento;
- consultar o histórico de vendas e abrir um comprovativo interno;
- terminar a sessão.

A venda aplica o preço guardado no inventário, marca a mota como vendida e regista um evento de auditoria na mesma transação. A base de dados impede que a mesma mota seja associada a mais do que uma venda.

## Tecnologias e arquitetura

- **Python 3.12** como versão recomendada (a aplicação requer Python 3.11 ou superior).
- **Flask** para rotas HTTP, sessões e interface renderizada no servidor com Jinja.
- **SQLite** para execução local.
- **PostgreSQL** através de `psycopg` para um ambiente remoto persistente, se configurado.
- **pytest** e **Ruff** para testes e análise estática.

A interface e as regras de negócio estão no pacote `moto_pos`; os ficheiros públicos estão em `public/`. O valor monetário é guardado em cêntimos inteiros. A aplicação não integra um processador de pagamentos.

## Requisitos

- Windows com PowerShell (os comandos abaixo usam PowerShell).
- Python 3.12 instalado e disponível pelo launcher `py`; Python 3.11+ é suportado pelo pacote.
- `pip`, incluído na instalação normal de Python.
- Ligação à Internet durante a instalação das dependências.

## Instalação e arranque local no Windows

Abra o PowerShell e entre na pasta que contém `pyproject.toml` e `app.py`. Adapte o caminho se guardou o projeto noutro local:

```powershell
Set-Location "C:\caminho\para\projeto PoS Final"
Test-Path pyproject.toml
```

O último comando deve devolver `True`. Crie o ambiente virtual e instale a aplicação com as ferramentas de desenvolvimento:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

`Copy-Item` é necessário apenas na primeira instalação. Se `.env` já existir, não o substitua: contém a configuração local e não deve ser versionado.

### Configurar credenciais locais

Edite `.env` e defina:

- `SECRET_KEY`: segredo aleatório com pelo menos 32 caracteres;
- `ADMIN_USERNAME`: nome da conta inicial (por omissão, `admin`);
- `ADMIN_PASSWORD`: palavra-passe inicial com pelo menos 12 caracteres;
- `DATABASE_PATH`: caminho local da base SQLite (por omissão, `instance/moto_pos.sqlite3`).

Podes gerar um segredo no PowerShell com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copia o resultado para `SECRET_KEY` em `.env`. Escolhe uma palavra-passe única para `ADMIN_PASSWORD`. Não coloques valores reais no Git, em documentação ou em mensagens.

A aplicação não carrega `.env` automaticamente. O bloco seguinte carrega as variáveis para o processo PowerShell atual sem imprimir os valores e força o modo SQLite local. Executa-o sempre que abrires um novo terminal:

```powershell
foreach ($line in Get-Content .env) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $name = $Matches[1]
        $value = $Matches[2].Trim()
        if ($value.Length -ge 2 -and $value[0] -eq $value[-1] -and ($value[0] -eq '"' -or $value[0] -eq "'")) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}
$env:DATABASE_URL = ""
$env:DATABASE_PATH = "instance/moto_pos.sqlite3"
```

Inicializa o esquema e a conta inicial (na primeira instalação ou quando precisares de confirmar o esquema):

```powershell
python -m flask --app moto_pos.app init-db
```

O comando é idempotente para as tabelas. Se a conta já existir, não altera a palavra-passe; alterar credenciais de uma conta existente requer um processo próprio, que ainda não está implementado.

Inicia o servidor local:

```powershell
python -m flask --app moto_pos.app run --host 127.0.0.1 --port 5000
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000) no navegador. A aplicação encaminha para o login. Usa `ADMIN_USERNAME` e `ADMIN_PASSWORD` definidos no ambiente ao inicializar a base. Para parar o servidor, carrega em `Ctrl+C` no terminal.

Se a ativação do ambiente virtual for bloqueada pela política do PowerShell, executa os mesmos comandos através de `\.venv\Scripts\python.exe` sem ativar o ambiente.

## Testes e qualidade

Com o ambiente virtual ativo, executa:

```powershell
python -m pytest
python -m ruff check .
```

A suite existente cobre, entre outros fluxos, autenticação, CSRF, unicidade do VIN, registo de venda, comprovativo e prevenção de venda repetida. A configuração de CI em `.github/workflows/ci.yml` executa pytest e Ruff em Python 3.12 quando corre no GitHub Actions. Estes comandos verificam o código; não verificam uma ligação a uma base PostgreSQL real nem um deployment remoto.

## Estrutura do projeto

```text
app.py                         Entry point WSGI da Vercel
build.py                       Inicialização PostgreSQL durante o build Vercel
moto_pos/
  app.py                        Fábrica Flask, rotas e validação
  config.py                     Configuração e validação de segredos
  db.py                         Adaptadores SQLite/PostgreSQL e esquema
  templates/                    Páginas HTML Jinja
public/                         Ficheiros estáticos servidos pela aplicação
instance/                       Base SQLite local (ignorada pelo Git)
tests/                          Testes automatizados
.github/workflows/ci.yml        Verificações automáticas de CI
docs/                           Requisitos, decisões, segurança e deployment
```

## Segurança e dados

- As palavras-passe são armazenadas como hash; a aplicação não guarda o texto original.
- Sessões usam cookies `HttpOnly` e `SameSite=Lax`; `Secure` deve ser ativado com `COOKIE_SECURE=1` quando houver HTTPS.
- Os pedidos de alteração exigem token CSRF; as rotas funcionais exigem sessão autenticada.
- As consultas usam parâmetros SQL e os templates Jinja escapam conteúdo por omissão.
- A aplicação regista apenas o método de pagamento declarado. Não recolhe PAN, CVV ou credenciais de pagamento.
- Nome, email e telefone são dados pessoais. Limita o acesso à máquina/base de dados e define retenção e cópias de segurança antes de usar dados reais.
- `.env` contém segredos locais e está excluído do Git. Se uma credencial for partilhada ou exposta, troca-a.

A aplicação deve ficar limitada a `localhost` até existir uma configuração de produção revista, com HTTPS, servidor adequado, segredos geridos e política de backups/restauro. O servidor Flask integrado é apenas para desenvolvimento.

## Limitações e decisões pendentes

A versão atual não implementa:

- faturação fiscal, impostos, descontos, séries documentais ou integração contabilística;
- processamento de pagamentos, devoluções, anulações ou vendas com várias motas;
- múltiplos papéis/permissões, gestão de contas ou recuperação de palavra-passe;
- migrações versionadas, migração automática de SQLite para PostgreSQL ou backup/restauro automatizados;
- política de retenção/apagamento de dados pessoais ou auditoria imutável;
- verificação de desempenho, acessibilidade ou segurança independente.

O comprovativo apresentado é **interno** e não substitui fatura fiscal. Os requisitos fiscais e de proteção de dados têm de ser avaliados com os responsáveis apropriados antes de utilização comercial.

## Deployment

A raiz contém `app.py`, `vercel.json` e a configuração do entrypoint Flask para a Vercel. O modo remoto exige PostgreSQL persistente e as variáveis `DATABASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME` e `ADMIN_PASSWORD`; em produção, configura também `COOKIE_SECURE=1`.

O adaptador atual suporta **SQLite e PostgreSQL**. A base MySQL identificada pela porta 3306 não é compatível sem desenvolver e testar outro adaptador. O SQLite local não serve como armazenamento persistente para Vercel Functions.

O projeto ainda não tem uma ligação PostgreSQL real nem deployment Vercel verificados. Consulta o [guia de deployment](docs/deployment-vercel.md) antes de configurar o ambiente remoto. Não uses a mesma base de dados para Preview e Production.

## Documentação do projeto

- [Especificação Word: requisitos verificáveis e modelos](docs/Especificacao-Requisitos-e-Modelos.docx) — documento consolidado com requisitos, critérios de aceitação, casos de uso, backlog e fontes Mermaid dos diagramas.
- [Requisitos e rastreabilidade](docs/requirements-traceability.md) — mapa entre requisitos, implementação e evidência.
- [Modelos Mermaid editáveis](docs/modelos/) — contexto/containers, casos de uso, componentes, domínio, estados, sequência, atividade, segurança e deployment.
- [Decisões de arquitetura](docs/decisions.md) — decisões e trade-offs registados.
- [Segurança e privacidade](docs/security/security.md) — controlos, riscos e trabalho pendente.
- [Deployment na Vercel](docs/deployment-vercel.md) — requisitos e passos para o ambiente remoto.
- [Changelog](CHANGELOG.md) — alterações por versão.

## Resolução de problemas

**`Test-Path .env` ou `.venv\Scripts\python.exe` devolve `False`:** o terminal não está na raiz do projeto. Executa `Set-Location` para a pasta que contém `pyproject.toml` e repete a verificação.

**`SECRET_KEY` em falta ou demasiado curta:** confirma o valor no `.env`, volta a carregar as variáveis no terminal atual e verifica que o segredo tem pelo menos 32 caracteres.

**`ADMIN_PASSWORD` demasiado curta:** define uma palavra-passe inicial com pelo menos 12 caracteres antes de executar `init-db`.

**A aplicação recusa uma `DATABASE_URL` MySQL:** para desenvolvimento local, limpa `DATABASE_URL` e usa `DATABASE_PATH`; o backend local será SQLite. Para remoto, configura uma URL PostgreSQL suportada.

**A porta 5000 está ocupada:** inicia com `--port 5001` e abre `http://127.0.0.1:5001`.
