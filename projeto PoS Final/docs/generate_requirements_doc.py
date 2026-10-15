"""Generate the editable requirements and system models document.

Run from the repository root with python-docx installed:
    python docs/generate_requirements_doc.py

The Mermaid sources written to docs/modelos are the editable diagram masters.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MODELS = DOCS / "modelos"
OUT = DOCS / "Especificacao-Requisitos-e-Modelos.docx"


REQS = {
    "Necessidades funcionais": [
        ("REQ-F-001", "Autenticar operador", "Must", "Necessidade inferida: impedir acesso operacional anónimo.", "Credenciais válidas iniciam sessão e encaminham para destino local; inválidas não autenticam; sem sessão, rotas protegidas redirecionam para login.", "Testes de integração: login válido/inválido, GET protegido anónimo e destino externo malicioso.", "Implementado; cobertura parcial nos testes existentes.", "moto_pos/app.py: login, login_required; tests/test_pos.py"),
        ("REQ-F-002", "Terminar sessão", "Must", "Necessidade inferida: operador pode encerrar sessão.", "POST autenticado com CSRF válido limpa a sessão; pedido sem CSRF é rejeitado; GET não executa logout.", "Teste HTTP de sessão, método e CSRF.", "Implementado; falta teste dedicado de logout.", "moto_pos/app.py: logout; templates/base.html"),
        ("REQ-F-003", "Registar e consultar inventário", "Must", "Brief: PoS para motas novas/usadas; campos e limites observados no código.", "Aceitar marca/modelo obrigatórios até 80 caracteres, VIN normalizado em maiúsculas com 5–32 caracteres e único, ano entre 1885 e ano atual + 1, condição nova/usada, preço até 2 casas decimais e não negativo. VIN repetido é recusado com conflito; inventário lista registos.", "Testes de integração para limites, duplicação, valores inválidos e listagem; validar restrições da BD.", "Implementado; teste de duplicação existe; restantes limites sem cobertura dedicada.", "moto_pos/app.py: motorcycle_new, motorcycles; moto_pos/db.py; tests/test_pos.py"),
        ("REQ-F-004", "Registar e consultar clientes", "Must", "Brief: registar clientes para associar às vendas; regras de campos observadas.", "Nome obrigatório até 120 caracteres; email e telefone opcionais limitados a 254/40 caracteres; email é sujeito a validação básica; cliente aparece na lista ordenada por nome.", "Testes de campos omitidos, limites, email e listagem.", "Implementado; cobertura automatizada dedicada pendente.", "moto_pos/app.py: customer_new, customers; moto_pos/db.py"),
        ("REQ-F-005", "Registar venda de uma mota", "Must", "Brief: PoS; pressuposto da versão: uma unidade por venda e pagamento registado manualmente.", "Para mota disponível, cliente existente e método permitido, criar uma venda cujo total é o preço de inventário, marcar a mota vendida e gravar auditoria numa transação; erro não deixa alterações parciais.", "Teste de integração e falhas injetadas antes do commit; confirmar estado, venda, total e auditoria.", "Implementado para SQLite/PostgreSQL; teste feliz e venda repetida existentes; concorrência PostgreSQL não verificada.", "moto_pos/app.py: sale_new; moto_pos/db.py; tests/test_pos.py"),
        ("REQ-F-006", "Consultar resumo operacional", "Should", "Necessidade inferida da página Resumo existente.", "Após autenticação, apresentar contagem de motas disponíveis, contagem de vendas e soma dos totais registados; soma vazia é zero.", "Teste de integração com base vazia e dados semeados.", "Implementado; teste dedicado pendente.", "moto_pos/app.py: dashboard; templates/dashboard.html"),
        ("REQ-F-007", "Consultar vendas e comprovativo interno", "Must", "Brief: consultar vendas; decisão ADR-006: recibo apenas interno.", "Operador autenticado consulta vendas por ordem temporal decrescente e abre o comprovativo associado; ID inexistente devolve 404; conteúdo não se declara fatura fiscal.", "Testes de ordenação, autorização, 404 e conteúdo do comprovativo.", "Implementado; recibo coberto pelo teste da venda; restantes casos pendentes.", "moto_pos/app.py: sales, sale_receipt; templates/receipt.html; tests/test_pos.py"),
        ("REQ-F-008", "Auditar operações de escrita", "Should", "Decisão técnica de rastreabilidade; eventos observados no código.", "Criar mota, cliente ou venda grava evento com utilizador, ação, entidade, ID e instante na mesma unidade de trabalho aplicável; erro na venda não deixa evento órfão.", "Consultar audit_log após sucesso e falha; cobrir cada ação de escrita.", "Parcial: criação de mota/cliente e venda registadas; cobertura e âmbito de auditoria limitados.", "moto_pos/app.py: audit; moto_pos/db.py: audit_log; tests/test_pos.py"),
    ],
    "Qualidade e operação": [
        ("REQ-NF-001", "Exatidão monetária", "Must", "Risco de negócio: erros de arredondamento; decisão ADR-003.", "Valores válidos são convertidos para cêntimos inteiros; rejeitar valores negativos, acima do máximo configurado e com mais de 2 casas decimais. Não usar float para cálculo do total.", "Testes de fronteira e inspeção do tipo persistido; total de venda igual ao preço em cêntimos.", "Implementado por Decimal e price_cents; fronteiras com cobertura pendente.", "moto_pos/app.py: money_to_cents; moto_pos/db.py"),
        ("REQ-NF-002", "Integridade transacional", "Must", "Regra comercial para impedir venda duplicada ou parcial.", "Em qualquer falha no fluxo de venda, nenhuma alteração parcial persiste; uma mota tem no máximo uma venda; duas tentativas concorrentes não podem vender a mesma mota duas vezes.", "Testes de rollback e concorrência contra cada SGBD suportado.", "Restrições e transação implementadas; cenário concorrente e PostgreSQL real não verificados.", "moto_pos/app.py: sale_new; moto_pos/db.py; tests/test_pos.py"),
        ("REQ-NF-003", "Desempenho percebido", "Should — proposta", "Meta de engenharia provisória; não aprovada pelo cliente nem medida.", "Meta proposta: p95 inferior a 2 s para páginas HTML e submissões sem rede externa, com 10 000 motas, 10 000 clientes, 100 000 vendas e 20 utilizadores concorrentes num ambiente de referência de 2 vCPU/4 GB. Confirmar ou substituir após conhecer a carga real.", "Teste de carga reproduzível; guardar ambiente, dados, perfil e relatório p50/p95/p99. Sem teste, não declarar cumprido.", "Não medido; requisito proposto.", "Proposta; backlog de validação de carga"),
        ("REQ-NF-004", "Usabilidade e acessibilidade", "Should — proposta", "Meta provisória; fluxos e utilizadores reais ainda não foram observados.", "Meta proposta: completar registo de uma mota e venda com teclado, rótulos programáticos e foco visível; em teste moderado, pelo menos 4/5 operadores concluem cada fluxo sem ajuda. Alvo WCAG 2.2 AA requer auditoria antes de alegar conformidade.", "Inspeção automatizada e manual de acessibilidade; teste de tarefas com utilizadores representativos e registo de resultados.", "Não verificado; interface HTML sem evidência de auditoria WCAG ou teste de utilizadores.", "Proposta; backlog de validação UX"),
        ("REQ-NF-005", "Manutenibilidade e reprodução", "Must", "Objetivo de engenharia do projeto; CI declarada no repositório.", "Instalação a partir de pyproject.toml; PR/push executa pytest e Ruff em Python 3.12; documentação distingue estado implementado e pendente.", "Executar workflow CI limpo e reproduzir instalação numa máquina sem estado prévio.", "Configuração CI e documentação presentes; execução remota da CI não comprovada nesta especificação.", ".github/workflows/ci.yml; pyproject.toml; README.md"),
        ("REQ-NF-006", "Disponibilidade e recuperação", "Should — por decidir", "Necessidade operacional presumida; RPO/RTO dependem do stand e alojamento.", "Definir com o cliente RPO, RTO, retenção e frequência de backup antes de produção. Critério de aceitação: restauro demonstrado num ambiente isolado dentro dos objetivos aprovados.", "Ensaio documentado de backup/restauro com medição; rever política aprovada.", "Não implementado: backup/restauro automatizados e metas RPO/RTO não definidos.", "docs/security/security.md; decisão pendente"),
    ],
    "Segurança": [
        ("REQ-SEC-001", "Segredos e credenciais", "Must", "Prática de segurança; configuração atual exige segredo >=32 e palavra-passe inicial >=12.", "SECRET_KEY com pelo menos 32 caracteres; ADMIN_PASSWORD com pelo menos 12; armazenamento de password por hash Werkzeug; .env nunca é versionado.", "Testes de validação de configuração; inspeção de base para confirmar que texto claro não é armazenado; verificação de gitignore/artefactos.", "Implementado parcialmente: hash, limites e .gitignore; rotação/recuperação não existem.", "moto_pos/config.py; moto_pos/db.py; .gitignore; build.py"),
        ("REQ-SEC-002", "Autorização de rotas", "Must", "Necessidade inferida: dados e operações PoS não podem ser anónimos.", "Todas as rotas operacionais redirecionam sessões não autenticadas; só login e assets públicos ficam acessíveis sem sessão. Não há diferenciação de papéis nesta versão.", "Matriz de rotas anónimas/autenticadas; testes de autorização por endpoint.", "Implementado com autenticação única; autorização por função não existe.", "moto_pos/app.py: login_required; tests/test_pos.py"),
        ("REQ-SEC-003", "Proteção contra CSRF", "Must", "Ameaça de submissão de ações a partir de origem externa.", "Todos os métodos de alteração (POST/PUT/PATCH/DELETE) requerem token de sessão correspondente; comparação em tempo constante; pedido inválido retorna 400.", "Teste por método e endpoint, incluindo login/logout.", "Implementado; teste dedicado cobre token inválido no login, cobertura global pendente.", "moto_pos/app.py: before_request; templates com csrf_token; tests/test_pos.py"),
        ("REQ-SEC-004", "Injeção e validação de dados", "Must", "Ameaça de injeção; dados vindos do browser não são confiáveis.", "Consultas persistentes usam parâmetros; entradas são validadas no servidor; conteúdo apresentado mantém escape Jinja ativo.", "Revisão estática/manual das consultas e testes de payloads maliciosos e limites.", "Implementado em consultas observadas; revisão de segurança independente não realizada.", "moto_pos/app.py; moto_pos/db.py; templates/*.html"),
        ("REQ-SEC-005", "Proteção de cookies e transporte", "Must", "Boas práticas para sessão; deployment de produção ainda não verificado.", "Cookies de sessão HttpOnly e SameSite=Lax; Secure ativo em HTTPS com COOKIE_SECURE=1; produção só através de HTTPS.", "Inspeção dos atributos Set-Cookie em cada ambiente e teste de HTTPS/headers no deployment.", "HttpOnly/SameSite configurados; Secure depende de configuração; deployment TLS não verificado.", "moto_pos/app.py: app.config; docs/security/security.md"),
        ("REQ-SEC-006", "Não recolher dados de cartão", "Must", "ADR-005: pagamento processado fora da aplicação.", "Sistema guarda apenas método declarado (dinheiro/cartão/transferência); não pede nem persiste PAN, CVV ou credenciais de pagamento.", "Inspecionar schema, formulários, tráfego e logs; confirmar que fluxo de pagamento é externo.", "Implementado no fluxo atual; não existe integração de pagamento.", "moto_pos/db.py: payment_method; templates/sale_form.html"),
    ],
    "Privacidade, restrições e regras de negócio": [
        ("REQ-PRIV-001", "Minimização de dados do cliente", "Must", "Princípio de privacidade; modelo atual recolhe nome, email e telefone.", "Nome obrigatório; email/telefone opcionais; não recolher campos pessoais adicionais sem finalidade aprovada.", "Revisão de formulários, schema, logs e exportações.", "Implementado no esquema/formulários; base jurídica e prazos ainda carecem de decisão organizacional.", "moto_pos/app.py: customer_new; moto_pos/db.py; templates/customer_form.html"),
        ("REQ-PRIV-002", "Retenção e direitos dos titulares", "Must — bloqueio de produção", "Obrigação organizacional/legal a determinar com o responsável pelo tratamento.", "Antes de produção, aprovar finalidade, base jurídica, retenção, acesso, correção, exportação e apagamento; implementar e demonstrar os processos aprovados.", "Revisão documental e testes operacionais de cada processo após implementação.", "Não implementado; prazo e processos não definidos.", "Pendente de decisão; docs/security/security.md"),
        ("REQ-CON-001", "Motores de base de dados suportados", "Must", "Decisão ADR-002/007 e implementação do adaptador.", "Modo local usa SQLite; modo remoto aceita somente URL postgres:// ou postgresql://. MySQL, incluindo porta 3306, não é suportado sem alteração explícita.", "Testar seleção SQLite/PostgreSQL e rejeição de URL de outro esquema; integração real PostgreSQL separada.", "Implementado para SQLite e adaptador PostgreSQL; PostgreSQL externo não verificado; MySQL não suportado.", "moto_pos/db.py; moto_pos/app.py; build.py"),
        ("REQ-CON-002", "Âmbito fiscal e documental", "Must — restrição", "ADR-006; requisitos fiscais portugueses não foram especificados nem validados.", "Comprovativo identifica-se como interno e não como fatura; nenhuma alegação de conformidade fiscal é permitida.", "Revisão do comprovativo e aprovação por especialista fiscal antes de qualquer evolução fiscal.", "Restrição documentada; faturação fiscal não implementada.", "templates/receipt.html; docs/decisions.md; docs/security/security.md"),
        ("REQ-CON-003", "Ambiente de execução", "Must", "Configuração de projeto e intenção de deployment.", "Python >=3.11 declarado; CI usa Python 3.12; deployment serverless requer PostgreSQL persistente e variáveis seguras. SQLite serve apenas ao desenvolvimento/local.", "Build limpo em Python 3.12; verificar variáveis e política de persistência no ambiente alvo.", "Configuração existe; produção Vercel não verificada.", "pyproject.toml; .python-version; build.py; docs/deployment-vercel.md"),
        ("RN-001", "VIN único e normalizado", "Must", "Regra derivada do identificador de unidade no inventário.", "Aplicação remove espaços exteriores, converte para maiúsculas e aceita 5–32 caracteres; colisão é recusada.", "Testes de VIN repetido com variação de caixa/espaços e limites.", "Implementado; normalização/limites sem testes dedicados.", "moto_pos/app.py; moto_pos/db.py"),
        ("RN-002", "Ano, condição e preço válidos", "Must", "Regra inferida do formulário e restrições SQL.", "Ano entre 1885 e ano UTC atual + 1; condição em {nova, usada}; preço entre 0 e 999999999,99 com no máximo 2 casas.", "Testes de fronteira temporal, enumeração e preço.", "Validação de aplicação implementada; restrição SQL de ano permite até 2100 e deve continuar protegida pela validação HTTP.", "moto_pos/app.py: motorcycle_new, money_to_cents; moto_pos/db.py"),
        ("RN-003", "Só vender mota disponível", "Must", "Integridade de stock.", "Uma venda só é aceite para status=disponivel e cliente existente; após commit, status=vendida.", "Teste de estados disponível/vendida e cliente inexistente.", "Implementado; caminhos inválidos parcialmente cobertos.", "moto_pos/app.py: sale_new; tests/test_pos.py"),
        ("RN-004", "Uma venda por unidade", "Must", "Regra de negócio para impedir dupla venda.", "Cada motorcycle_id aparece no máximo uma vez em sales; venda repetida é rejeitada e não cria recibo/venda adicional.", "Teste de venda repetida e concorrência por SGBD.", "Índice UNIQUE e validação implementados; concorrência PostgreSQL não verificada.", "moto_pos/db.py; tests/test_pos.py"),
        ("RN-005", "Total e pagamento declarados", "Must", "Decisões ADR-004/005.", "Total da venda é o preço atual da mota, sem edição, desconto ou imposto; método pertence a dinheiro/cartao/transferencia; não processa pagamento.", "Testes de total e rejeição de método inválido.", "Implementado; descontos/impostos/pagamento eletrónico fora do âmbito.", "moto_pos/app.py: sale_new; moto_pos/db.py"),
        ("RN-006", "Venda, stock e auditoria atómicos", "Must", "Regra de consistência transacional.", "Venda criada, mota marcada vendida e evento sale.created confirmado juntos; em rollback, nenhum dos três efeitos persiste.", "Testes de transação e injeção de falhas nos dois backends.", "Implementado; integração e testes de falha PostgreSQL pendentes.", "moto_pos/app.py: sale_new, audit; moto_pos/db.py"),
    ],
}


DIAGRAMS = {
    "01-contexto-containers.mmd": ("C4 — contexto e containers", "Delimita o operador, o browser, a aplicação Flask, os dados e as fronteiras de deployment. Diferencia o modo local já executável do alvo PostgreSQL ainda condicionado.", r'''flowchart LR
  operador[Operador do stand]
  browser[Navegador]
  subgraph app["Moto PoS — aplicação web"]
    web["Flask: rotas e casos de uso"]
    templates["Templates Jinja e CSS"]
    security["Sessão, CSRF e validação"]
  end
  sqlite[("SQLite — local")]
  pg[("PostgreSQL — remoto, por configurar")]
  operador --> browser
  browser <-->|"HTTP local / HTTPS no alvo"| web
  web --> templates
  web --> security
  web -->|"modo local"| sqlite
  web -->|"modo remoto suportado"| pg
  web -. "não integra" .-> payment["Gateway de pagamento"]
'''),
    "02-casos-de-uso.mmd": ("Casos de uso", "Mostra o único ator funcional atual. Autorização por papéis, pagamento e faturação fiscal não aparecem como casos suportados.", r'''flowchart LR
  op["Operador autenticado"]
  subgraph pos["Moto PoS"]
    auth([Iniciar / terminar sessão])
    inventory([Registar e consultar motas])
    customer([Registar e consultar clientes])
    sell([Registar venda de uma mota])
    dashboard([Consultar resumo])
    history([Consultar vendas])
    receipt([Abrir comprovativo interno])
  end
  op --> auth
  op --> inventory
  op --> customer
  op --> sell
  op --> dashboard
  op --> history
  op --> receipt
'''),
    "03-componentes.mmd": ("Componentes e camadas", "Relaciona interface, rotas, validação, persistência e adaptador de base de dados conforme a organização atual do código.", r'''flowchart TB
  browser["Browser / formulários"] --> templates["Templates Jinja + public/style.css"]
  templates --> routes["moto_pos/app.py — rotas Flask"]
  routes --> security["Sessão, login_required e CSRF"]
  routes --> validation["Validação de campos e dinheiro"]
  routes --> dbapi["moto_pos/db.py — DatabaseConnection"]
  dbapi --> sqlite["sqlite3 — ficheiro local"]
  dbapi --> psycopg["psycopg — PostgreSQL"]
  dbapi --> schema["Esquema e bootstrap idempotente"]
'''),
    "04-dominio-relacional.mmd": ("Modelo conceptual e relacional", "Representa as entidades, cardinalidades e restrições que estão no esquema SQL. O audit_log é histórico básico, não trilho imutável.", r'''erDiagram
  USERS ||--o{ SALES : records
  CUSTOMERS ||--o{ SALES : purchases
  MOTORCYCLES ||--o| SALES : sold_as
  USERS ||--o{ AUDIT_LOG : performs
  USERS {
    int id PK
    string username UK
    string password_hash
    datetime created_at
  }
  MOTORCYCLES {
    int id PK
    string make
    string model
    int year
    string vin UK
    string condition
    int price_cents
    string status
    datetime created_at
  }
  CUSTOMERS {
    int id PK
    string name
    string email
    string phone
    datetime created_at
  }
  SALES {
    int id PK
    int motorcycle_id FK_UK
    int customer_id FK
    int user_id FK
    int total_cents
    string payment_method
    datetime created_at
  }
  AUDIT_LOG {
    int id PK
    int user_id FK
    string action
    string entity_type
    int entity_id
    datetime created_at
  }
'''),
    "05-estado-mota.mmd": ("Máquina de estados da mota", "Explicita a transição de stock permitida e o efeito de falha antes do commit. Não existe fluxo de anulação/devolução implementado.", r'''stateDiagram-v2
  [*] --> Disponivel : registo válido
  Disponivel --> Vendida : venda confirmada / commit
  Disponivel --> Disponivel : venda falha / rollback
  Vendida --> [*]
  note right of Vendida : Sem reversão na versão atual
'''),
    "06-sequencia-venda.mmd": ("Sequência do caso de uso venda", "Mostra validação, transação e resposta; os dados de pagamento não passam por gateway.", r'''sequenceDiagram
  actor Operador
  participant Browser
  participant Flask as Flask / sale_new
  participant DB as SQLite ou PostgreSQL
  Operador->>Browser: Escolhe mota, cliente e método
  Browser->>Flask: POST + sessão + token CSRF
  Flask->>Flask: Autentica e valida entrada
  Flask->>DB: BEGIN; carregar mota disponível e cliente
  alt dados válidos e mota disponível
    Flask->>DB: marcar vendida; inserir venda e auditoria
    Flask->>DB: COMMIT
    Flask-->>Browser: redirecionar para comprovativo
  else dados inválidos / conflito
    Flask->>DB: ROLLBACK se necessário
    Flask-->>Browser: mensagem de erro; sem venda
  end
'''),
    "07-atividade-venda.mmd": ("Atividade de venda", "Descreve decisões, pré-condições e caminho de erro para o fluxo central do PoS.", r'''flowchart TD
  start((Início)) --> auth{Sessão autenticada?}
  auth -- não --> login[Redirecionar para login]
  auth -- sim --> select[Selecionar mota, cliente e pagamento]
  select --> csrf{Token CSRF válido?}
  csrf -- não --> reject[Rejeitar pedido]
  csrf -- sim --> valid{Dados válidos e mota disponível?}
  valid -- não --> error[Mostrar erro; manter stock]
  valid -- sim --> tx[Transação: atualizar stock + venda + auditoria]
  tx --> commit{Commit bem-sucedido?}
  commit -- não --> rollback[Rollback integral]
  rollback --> error
  commit -- sim --> receipt[Mostrar comprovativo interno]
'''),
    "08-seguranca-fluxo-dados.mmd": ("Fronteira de segurança e fluxo de dados", "Identifica dados pessoais, credenciais, token de sessão e dados de venda; o cartão é pago fora do limite da aplicação.", r'''flowchart LR
  subgraph untrusted["Zona não confiável — browser do operador"]
    input["Formulários: cliente, mota, venda"]
  end
  subgraph trust["Fronteira da aplicação Moto PoS"]
    csrf["CSRF + sessão Flask"]
    validate["Autorização + validação"]
    app["Rotas e regras de negócio"]
  end
  subgraph data["Persistência controlada pelo operador"]
    store["SQLite local ou PostgreSQL externo"]
    pii["Nome, email/telefone opcionais"]
    secrets["Hash de palavra-passe; segredo fora do código"]
    events["Vendas e auditoria limitada"]
  end
  input -->|"HTTP local / HTTPS em produção"| csrf --> validate --> app
  app --> store
  store --> pii
  store --> secrets
  store --> events
  input -. "PAN/CVV não recolhidos" .-> out["Pagamento externo ao sistema"]
'''),
    "09-deployment.mmd": ("Deployment — atual e alvo condicionado", "Separa o modo local suportado do desenho Vercel pretendido. A ligação real à Vercel/PostgreSQL não está verificada.", r'''flowchart TB
  subgraph local["Atual — desenvolvimento local"]
    user1["Operador"] --> browser1["Browser"] --> flask1["Flask dev server"] --> sqlite1[("SQLite em instance/")]
    static1["public/style.css"] --> browser1
  end
  subgraph target["Alvo — não verificado"]
    user2["Operador"] -->|HTTPS| edge["Vercel Function: app.py"]
    edge --> pg[("PostgreSQL externo persistente")]
    static2["public/ servido pela Vercel"] --> browser2["Browser"]
  end
  warning["Requer DATABASE_URL, segredos, base provisionada, build e teste de integração"]
  warning -.-> target
'''),
}


STORIES = [
    ("US-01", "Como operador, quero iniciar e terminar sessão para restringir o acesso às operações.", "P0", "Login válido; inválido; rota protegida anónima; CSRF no login/logout."),
    ("US-02", "Como operador, quero registar e consultar motas para controlar o inventário.", "P0", "Nova/usada, VIN repetido, ano/preço fora dos limites, listagem autenticada."),
    ("US-03", "Como operador, quero registar e consultar clientes para os associar a vendas.", "P0", "Nome em falta, email opcional inválido, telefone opcional, listagem ordenada."),
    ("US-04", "Como operador, quero vender uma mota disponível a um cliente para registar a transação operacional.", "P0", "Sucesso; mota já vendida; cliente inexistente; método inválido; CSRF ausente; rollback."),
    ("US-05", "Como operador, quero consultar o resumo e histórico para acompanhar o estado comercial.", "P1", "Base vazia, múltiplas vendas, ordenação e acesso anónimo."),
    ("US-06", "Como operador, quero abrir um comprovativo interno para consultar os dados da venda.", "P1", "ID existente, inexistente (404), venda associada a mota/cliente; sem alegação fiscal."),
    ("US-07", "Como responsável pelo stand, quero recuperar uma base de dados para reduzir perda operacional.", "P1 — futuro", "Definir RPO/RTO/retenção; executar backup e restauro isolado e validar contagens."),
    ("US-08", "Como responsável, quero separar funções e gerir contas para limitar operações por utilizador.", "P2 — futuro", "Perfis aprovados, autorização por endpoint, provisionamento/desativação e auditoria."),
]


USE_CASES = [
    ("UC-01 — Autenticar operador", "Operador; serviço Flask; utilizador inicial provisionado.", "Conta existente; aplicação e base disponíveis.", "1. Browser pede login. 2. Operador submete credenciais e token CSRF. 3. Sistema compara hash. 4. Em sucesso limpa sessão anterior, cria sessão e redireciona para caminho local permitido.", "Credencial incorreta: login recusado. CSRF inválido: 400. Destino externo/URL com // ou barra invertida: ignorado e encaminhado ao resumo.", "Sessão autenticada ou utilizador continua sem sessão.", "Implementado; verificar cobertura de redirects e credenciais."),
    ("UC-02 — Registar mota", "Operador autenticado.", "Sessão válida; CSRF disponível.", "1. Abrir formulário. 2. Preencher marca/modelo/ano/VIN/condição/preço. 3. Servidor valida e normaliza VIN. 4. Persistir mota e evento de auditoria. 5. Mostrar inventário.", "Campo obrigatório ausente/limite violado: 400. VIN repetido: 409. Acesso sem sessão: redirect login.", "Mota disponível listada ou nenhum registo criado.", "Implementado; testes de limites em falta."),
    ("UC-03 — Registar cliente", "Operador autenticado.", "Sessão válida; CSRF disponível.", "1. Abrir formulário. 2. Informar nome e opcionalmente email/telefone. 3. Servidor valida limites e email básico. 4. Guardar cliente/auditoria. 5. Mostrar lista.", "Nome vazio/email malformado: 400; campos opcionais vazios persistem como null.", "Cliente criado ou nenhuma alteração.", "Implementado; teste dedicado pendente."),
    ("UC-04 — Registar venda", "Operador autenticado; cliente; mota disponível.", "Pelo menos uma mota disponível e um cliente registado.", "1. Selecionar mota/cliente/método. 2. Enviar POST com CSRF. 3. Abrir transação. 4. Confirmar disponibilidade e cliente. 5. Marcar mota vendida, inserir venda ao preço de inventário e auditoria. 6. Commit e redirecionar ao comprovativo.", "Mota vendida/cliente ausente/método inválido: não vender. Falha SQL: rollback. Duas vendas simultâneas: no máximo uma deve confirmar; integração concorrente por backend ainda por verificar.", "Venda e stock consistentes; recibo interno disponível apenas após commit.", "Implementado; concorrência PostgreSQL e rollback injetado pendentes."),
    ("UC-05 — Consultar venda", "Operador autenticado.", "Venda criada.", "1. Consultar histórico ordenado por data. 2. Abrir venda. 3. Ver mota, cliente, operador, total, método declarado e data.", "ID inexistente: 404. Acesso anónimo: redirect. Documento continua classificado como comprovativo interno.", "Dados consultados sem escrita.", "Implementado; testes de borda pendentes."),
]


BACKLOG = [
    ("P0", "Validar requisitos comerciais e critérios fiscais", "Confirmar impostos, descontos, séries, recibo/fatura, devoluções, múltiplas motas e papéis. Sem decisão, manter recibo interno e âmbito atual.", "Responsável do stand + especialista fiscal; desbloqueia produção."),
    ("P0", "Estabelecer credenciais e ciclo de vida de contas", "Provisionamento, alteração/recuperação de palavra-passe, desativação e pelo menos um administrador de contingência.", "Responsável operacional; necessário para operação segura."),
    ("P0", "Definir privacidade, retenção e resposta a titulares", "Finalidade, base jurídica, prazos, acesso, retificação, exportação/apagamento e responsáveis.", "Responsável pelo tratamento/privacidade; antes de dados reais."),
    ("P0", "Política e ensaio de backup/restauro", "Aprovar RPO/RTO, frequência, retenção, cifragem e teste de recuperação.", "Operações; antes de produção persistente."),
    ("P1", "Completar testes funcionais negativos e limites", "Cobrir validação de mota/cliente, logout, autorização de endpoints, recibo 404, rollback e auditoria.", "Desenvolvimento; execução local e CI."),
    ("P1", "Testes PostgreSQL reais e concorrência", "Executar migração/bootstrap e venda concorrente contra PostgreSQL gerido; comprovar uma só venda.", "Infra/Desenvolvimento; exige base de teste."),
    ("P1", "Definir carga e medir desempenho", "Validar/ajustar meta provisória de 2 s p95, carga e ambiente de referência; publicar relatório repetível.", "Cliente + engenharia; antes de escalar."),
    ("P1", "Auditoria de acessibilidade e usabilidade", "Rever teclado, foco, semântica e leitores de ecrã; teste de tarefas com operadores reais; resolver bloqueios.", "Produto/QA; antes de aceite de UX."),
    ("P1", "Rever deployment e configuração segura", "Base PostgreSQL, HTTPS, cookies Secure, secrets, pooling, build, logs sem PII e teste de smoke em staging.", "Operações; deployment ainda não verificado."),
    ("P2", "Papéis e autorização por função", "Modelar administrador/vendedor e verificar permissões por endpoint, se necessidade for confirmada.", "Negócio + segurança."),
    ("P2", "Devoluções/anulações e alterações auditáveis", "Definir estados, impacto em stock/financeiro e mecanismo de correção append-only.", "Negócio/contabilidade; depende de regras fiscais."),
    ("P2", "Migrações versionadas e migração SQLite/PostgreSQL", "Introduzir ferramenta/migrações com rollback e procedimento de transferência validado.", "Engenharia; antes de evolução do schema."),
]


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, *, bold: bool = False, color: str | None = None, size: float = 9) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)


def page_field(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for item in (begin, instr, separate, text, end):
        run._r.append(item)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.add_run(text)


def add_requirement(doc: Document, req: tuple[str, ...]) -> None:
    rid, title, priority, origin, acceptance, verification, status, evidence = req
    p = doc.add_heading(f"{rid} — {title}", level=3)
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=0, cols=2)
    t.style = "Light Shading Accent 1"
    entries = [
        ("Prioridade", priority),
        ("Origem / pressuposto", origin),
        ("Critérios de aceitação", acceptance),
        ("Verificação", verification),
        ("Estado / evidência", f"{status} Evidência: {evidence}"),
    ]
    for label, value in entries:
        cells = t.add_row().cells
        cells[0].width = Inches(1.45)
        cells[1].width = Inches(5.65)
        set_cell_text(cells[0], label, bold=True, color="174C3C", size=8.5)
        set_cell_text(cells[1], value, size=8.5)
        shade(cells[0], "E8F1ED")
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_simple_table(doc: Document, headers: list[str], rows: list[tuple[str, ...]], widths: list[float] | None = None) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Shading Accent 1"
    repeat_table_header(table.rows[0])
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True, color="FFFFFF", size=8)
        shade(table.rows[0].cells[i], "174C3C")
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, size=8)
            if widths:
                cells[i].width = Inches(widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_mermaid(doc: Document, filename: str, title: str, purpose: str, source: str) -> None:
    doc.add_heading(title, level=2)
    doc.add_paragraph(purpose)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    link = p.add_run(f"Fonte Mermaid editável incluída integralmente neste documento ({filename}).")
    link.italic = True
    link.font.color.rgb = RGBColor(23, 76, 60)
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    shade(cell, "F4F6F5")
    cell.text = ""
    for i, line in enumerate(source.strip().splitlines()):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(7)
        run.font.color.rgb = RGBColor.from_string("24423A")
    doc.add_page_break()


def build() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    for filename, (_, _, source) in DIAGRAMS.items():
        (MODELS / filename).write_text(source.strip() + "\n", encoding="utf-8")

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.3)

    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(9.5)
    styles["Normal"].paragraph_format.space_after = Pt(5)
    for name, size, color in (("Title", 28, "174C3C"), ("Heading 1", 18, "174C3C"), ("Heading 2", 13, "20785C"), ("Heading 3", 10.5, "174C3C")):
        style = styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.keep_with_next = True

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = header.add_run("MOTO PoS  |  ENGENHARIA DE REQUISITOS E MODELAÇÃO")
    r.font.name = "Aptos"
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor.from_string("61756D")
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run("Especificação de trabalho — não aprovada pelo cliente  ·  Página ")
    fr.font.size = Pt(8)
    page_field(footer)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(70)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("MOTO PoS")
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor.from_string("20785C")
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Engenharia de requisitos\nverificáveis e modelação do sistema")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = subtitle.add_run("Especificação de trabalho para o ponto de venda de motas novas e usadas")
    sr.font.size = Pt(12)
    sr.font.color.rgb = RGBColor.from_string("596B64")
    doc.add_paragraph()
    cover = doc.add_table(rows=0, cols=2)
    cover.style = "Light Shading Accent 1"
    for label, val in [
        ("Versão", "0.1 — baseline para validação"),
        ("Data de geração", date.today().isoformat()),
        ("Estado", "Proposta técnica baseada no repositório; sem aprovação formal do cliente"),
        ("Âmbito observado", "Flask; SQLite local; adaptador PostgreSQL; uma venda por mota"),
        ("Fonte da verdade", "Código e documentos em docs/; ver matriz de rastreabilidade"),
    ]:
        c = cover.add_row().cells
        set_cell_text(c[0], label, bold=True, color="174C3C", size=9)
        set_cell_text(c[1], val, size=9)
        shade(c[0], "E8F1ED")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(22)
    rr = p.add_run("Documento vivo. Pressupostos, metas propostas e funcionalidades não implementadas estão identificados como tal.")
    rr.italic = True
    rr.font.size = Pt(9)
    doc.add_page_break()

    doc.add_heading("Controlo e leitura do documento", level=1)
    doc.add_paragraph("Esta especificação descreve a versão do código inspecionada em 15 de outubro de 2026. É uma baseline de engenharia, não uma validação do cliente nem evidência de conformidade legal, segurança independente, desempenho medido ou deployment produtivo.")
    add_simple_table(doc, ["Estado", "Significado"], [
        ("Implementado", "Existe no código identificado; não implica que esteja validado em produção."),
        ("Parcial", "Há implementação, mas faltam coberturas, limites ou controlos."),
        ("Proposto / por decidir", "Meta de engenharia ou necessidade presumida; requer aprovação do cliente."),
        ("Não implementado", "Não existe no código observado; está no backlog ou bloqueia produção."),
    ], [1.45, 5.65])
    doc.add_heading("Índice", level=2)
    for line in ["1. Problema, fronteiras e vocabulário", "2. Necessidades, requisitos, regras e decisões", "3. Catálogo de requisitos verificáveis", "4. User stories, casos de uso e backlog", "5. Modelação do sistema", "6. Rastreabilidade", "7. Pressupostos, riscos e decisões pendentes", "Anexo A. Fontes editáveis dos diagramas"]:
        add_bullet(doc, line)

    doc.add_heading("1. Problema, fronteiras e vocabulário", level=1)
    doc.add_paragraph("O sistema apoia um operador de stand no registo do inventário e dos clientes, na venda operacional de uma mota e na consulta do histórico. A implementação observada é uma aplicação web Flask com um único tipo de conta funcional, templates Jinja, CSS estático e persistência SQLite local ou PostgreSQL através de psycopg.")
    doc.add_paragraph("Fora da fronteira atual: processamento de pagamentos, armazenamento de dados de cartão, faturação fiscal, devoluções/anulações, múltiplos artigos por venda, perfis de autorização, sincronização com fornecedores, backup/restauro automatizados e migrações versionadas. O MySQL não é suportado pelo adaptador atual.")
    add_simple_table(doc, ["Termo", "Definição usada nesta especificação"], [
        ("Necessidade do cliente", "Problema ou resultado desejado em linguagem do negócio; deve ser confirmado com o stand."),
        ("Requisito", "Propriedade ou comportamento verificável que o sistema deve satisfazer; recebe ID estável."),
        ("Regra de negócio", "Política do negócio que limita ou determina decisões e transações, independente da tecnologia."),
        ("Decisão técnica", "Escolha de arquitetura/implementação, com justificativa e trade-offs; registada como ADR."),
        ("Critério de aceitação", "Condição observável para aceitar um requisito; critérios propostos não são aprovação."),
        ("Verificação", "Método/evidência para demonstrar conformidade (teste, inspeção, análise, demonstração ou medição)."),
    ], [1.75, 5.35])
    doc.add_heading("2. Necessidades, requisitos, regras e decisões", level=1)
    doc.add_paragraph("Necessidades de negócio inferidas do pedido: manter stock de motas novas/usadas; associar clientes; registar vendas; consultar informação operacional. Estas necessidades ainda carecem de entrevistas e validação do cliente. Os requisitos REQ-* detalham resultados verificáveis. As RN-* formalizam regras como venda única por mota e total pelo preço de inventário. As ADR-* escolhem soluções técnicas (Flask, SQLite local/PostgreSQL remoto, preço em cêntimos, sem integração de pagamento). Uma decisão técnica não prova que a necessidade do negócio foi validada.")
    add_simple_table(doc, ["Fonte/decisão", "Conteúdo observado", "Consequência"], [
        ("Brief do projeto", "PoS para stand de motas usadas e novas.", "Necessidade de inventário e venda; campos fiscais/comerciais continuam por decidir."),
        ("ADR-001", "Aplicação web Flask.", "Navegador acede ao servidor; produção precisa de runtime WSGI adequado."),
        ("ADR-002 / ADR-007", "SQLite local; PostgreSQL em remoto.", "MySQL não funciona sem novo adaptador e testes."),
        ("ADR-003 / ADR-004", "Cêntimos inteiros; uma mota por venda, sem editar preço.", "Total deriva do preço armazenado; descontos/impostos não fazem parte do fluxo atual."),
        ("ADR-005 / ADR-006", "Pagamento declarado; recibo interno.", "Não recolhe dados de cartão e não substitui documento fiscal."),
    ], [1.45, 2.55, 3.1])

    doc.add_heading("3. Catálogo de requisitos verificáveis", level=1)
    doc.add_paragraph("Prioridades MoSCoW são recomendações de planeamento para validação. Critérios quantificados marcados como proposta não foram aprovados nem medidos. A evidência aponta para implementação e cobertura existentes; cobertura planeada não deve ser confundida com teste executado.")
    for group, reqs in REQS.items():
        doc.add_heading(group, level=2)
        for req in reqs:
            add_requirement(doc, req)

    doc.add_heading("4. User stories, casos de uso e backlog", level=1)
    doc.add_heading("4.1 User stories", level=2)
    add_simple_table(doc, ["ID", "História", "Prioridade", "Exemplos de aceitação"], STORIES, [0.62, 2.8, 0.9, 2.78])
    doc.add_heading("4.2 Casos de uso", level=2)
    for title, actor, pre, main, alt, post, evidence in USE_CASES:
        doc.add_heading(title, level=3)
        add_simple_table(doc, ["Campo", "Descrição"], [
            ("Ator / participantes", actor), ("Pré-condições", pre), ("Fluxo principal", main),
            ("Alternativas e erros", alt), ("Pós-condições", post), ("Estado/evidência", evidence),
        ], [1.45, 5.65])
    doc.add_heading("4.3 Backlog priorizado", level=2)
    doc.add_paragraph("Ordem provisória. P0 contém decisões e controlos que condicionam uso real; não significa que estejam implementados. P1 e P2 são melhorias propostas, sujeitas a validação do stand.")
    add_simple_table(doc, ["Prioridade", "Item", "Resultado / critério de saída", "Dependência"], BACKLOG, [0.75, 1.9, 3.15, 1.3])

    doc.add_heading("5. Modelação do sistema", level=1)
    doc.add_paragraph("Os modelos abaixo descrevem o código observado e, onde indicado, uma arquitetura-alvo ainda não verificada. Os ficheiros Mermaid são masters de texto editáveis e versionáveis; podem ser abertos num editor Mermaid ou convertidos em SVG/PNG por um renderer compatível. Cada modelo explica uma perspetiva diferente e não substitui os testes nem o código.")
    model_desc = [
        ("C4 — contexto e containers", "Visão de fronteiras, ator, browser, aplicação, persistência e serviços explicitamente ausentes."),
        ("Casos de uso", "Âmbito funcional e ator atualmente suportado; ajuda a validar atores e fronteiras com o negócio."),
        ("Componentes e camadas", "Responsabilidades entre apresentação, aplicação, segurança, validação e persistência."),
        ("Modelo conceptual e relacional", "Entidades e cardinalidades no esquema; orienta integridade, consultas e evolução da base."),
        ("Máquina de estados da mota", "Transições permitidas de stock e resultado de falha/rollback."),
        ("Sequência e atividade de venda", "Interações e decisões do fluxo transacional central, incluindo erros e token CSRF."),
        ("Fronteira de segurança e fluxo de dados", "Trust boundaries, dados pessoais/segredos e exclusão dos dados de cartão."),
        ("Deployment atual e alvo", "Contrasta execução local SQLite com alvo remoto Vercel/PostgreSQL condicionado."),
    ]
    add_simple_table(doc, ["Modelo", "Finalidade"], model_desc, [2.35, 4.75])
    doc.add_paragraph("Este documento contém os modelos e as fontes Mermaid completas no Anexo A; não é necessário abrir outros ficheiros para consultar ou editar o conteúdo dos diagramas. Existem cópias .mmd individuais no repositório apenas como conveniência para edição/renderização. O diagrama de deployment marca explicitamente como não verificados o fornecedor PostgreSQL, as variáveis de produção e o deployment Vercel.")

    doc.add_heading("6. Rastreabilidade", level=1)
    trace = [
        ("Necessidade: inventário", "REQ-F-003; RN-001; RN-002", "UC-02; casos de uso", "moto_pos/app.py motorcycle_new; moto_pos/db.py", "Teste existente de VIN duplicado; limites por completar"),
        ("Necessidade: gerir clientes", "REQ-F-004; REQ-PRIV-001", "UC-03; domínio", "moto_pos/app.py customer_new/customers", "Testes dedicados pendentes"),
        ("Necessidade: vender uma mota", "REQ-F-005; REQ-NF-001/002; RN-003..006", "UC-04; sequência; atividade; estado", "moto_pos/app.py sale_new; moto_pos/db.py", "Testes de venda e repetição existentes; integração concorrente por backend pendente"),
        ("Necessidade: controlo de acesso", "REQ-F-001/002; REQ-SEC-001..005", "UC-01; fluxo de segurança", "moto_pos/app.py; templates/base.html", "Testes de login/CSRF existentes; matriz completa de rotas pendente"),
        ("Necessidade: consultar operação", "REQ-F-006/007", "UC-05; casos de uso", "moto_pos/app.py dashboard/sales/sale_receipt", "Cobertura parcial via teste da venda"),
        ("Necessidade: operação sustentável", "REQ-NF-003..006; REQ-PRIV-002", "Deployment; backlog", ".github/workflows/ci.yml; docs/security/security.md", "Carga, UX, restore, privacidade e PostgreSQL real não verificados"),
    ]
    add_simple_table(doc, ["Necessidade", "Requisitos", "Modelo/caso de uso", "Código principal", "Evidência/estado"], trace, [1.2, 1.25, 1.25, 1.65, 1.75])
    doc.add_heading("Critério de atualização", level=2)
    doc.add_paragraph("Ao alterar um requisito, preservar o ID e atualizar critérios, testes, código, casos de uso/modelos e estado. Só marcar ‘verificado’ após guardar a evidência executada (versão, ambiente, comando, resultado e data). Alterações incompatíveis devem criar novo ID ou registar a substituição, nunca reutilizar um identificador com outro significado.")

    doc.add_heading("7. Pressupostos, riscos e decisões pendentes", level=1)
    for text in [
        "Atores reais, lojas, número de utilizadores, concorrência e operação offline não foram confirmados.",
        "Impostos, descontos, financiamento, devoluções, anulações, séries documentais e fatura fiscal requerem decisões de negócio/fiscais antes de produção.",
        "Papéis, recuperação de conta, MFA, limitação de tentativas e gestão de sessões não existem na versão observada.",
        "O PostgreSQL remoto está suportado por código, mas não foi verificado contra uma instância externa; o erro do fornecedor MySQL não pode ser resolvido pela configuração PostgreSQL atual.",
        "Desempenho, disponibilidade, acessibilidade, backups/restauro, proteção de dados e deployment produtivo não têm medições/evidência neste documento.",
        "As metas de p95 e teste com utilizadores são propostas de engenharia para discutir; substituí-las com objetivos aprovados e ambiente definido antes de tratá-las como compromissos.",
    ]:
        add_bullet(doc, text)
    doc.add_heading("Anexo A. Fontes editáveis dos diagramas", level=1)
    doc.add_paragraph("Este anexo torna o DOCX autossuficiente: cada bloco contém a fonte Mermaid editável completa de um dos nove modelos. Pode editar a fonte diretamente neste documento ou copiá-la para um renderer Mermaid para obter uma vista gráfica. Os ficheiros .mmd individuais são cópias auxiliares opcionais.")
    for filename, (title, purpose, source) in DIAGRAMS.items():
        add_mermaid(doc, filename, title, purpose, source)

    doc.core_properties.title = "Engenharia de requisitos verificáveis e modelação — Moto PoS"
    doc.core_properties.subject = "Requisitos, casos de uso, backlog, modelos C4, domínio, segurança e deployment"
    doc.core_properties.author = "Projeto Moto PoS"
    doc.core_properties.keywords = "requisitos; rastreabilidade; Mermaid; PoS; Flask"
    doc.save(OUT)
    print(f"Documento criado: {OUT.relative_to(ROOT)}")
    print(f"Fontes Mermaid editáveis: {len(DIAGRAMS)} em {MODELS.relative_to(ROOT)}")
    print(f"Requisitos catalogados: {sum(map(len, REQS.values()))}")


if __name__ == "__main__":
    build()
