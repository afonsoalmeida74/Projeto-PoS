# Requisitos e rastreabilidade

Esta matriz descreve a primeira versão implementada. Os IDs são estáveis para discussão e evolução; não representam aprovação formal do cliente.

| ID | Requisito da primeira versão | Implementação | Evidência automatizada | Estado |
|---|---|---|---|---|
| FR-01 | Exigir autenticação para operações do PoS | `moto_pos/app.py` (`login_required`) | `test_dashboard_requires_login`, `test_login_and_dashboard` | Implementado; execução pendente |
| FR-02 | Registar motas com VIN único, ano, condição e preço | rota `motorcycle_new`; esquema `motorcycles` | `test_motorcycle_creation_rejects_duplicate_vin` | Implementado; validação de criação normal ainda sem teste dedicado |
| FR-03 | Registar e consultar clientes | rotas `customer_new` e `customers` | — | Implementado; cobertura automatizada pendente |
| FR-04 | Vender uma mota disponível a um cliente e registar pagamento declarado | rota `sale_new`; tabelas `sales` e `motorcycles` | `test_sale_records_receipt_and_marks_motorcycle_sold` | Implementado; execução pendente |
| FR-05 | Impedir a venda repetida de uma unidade | transação `BEGIN IMMEDIATE`, estado e unicidade de `sales.motorcycle_id` | `test_cannot_sell_motorcycle_twice` | Implementado; execução pendente |
| FR-06 | Consultar vendas e apresentar comprovativo interno | rotas `sales` e `sale_receipt` | recibo coberto pelo teste de venda | Implementado; execução pendente |
| FR-07 | Proteger alterações contra CSRF | verificação comum de token antes dos pedidos de alteração | `test_login_rejects_invalid_csrf` | Implementado; execução pendente |
| NFR-01 | Evitar erros binários de representação monetária | `price_cents` inteiro; `Decimal` na validação | fluxo de venda valida total apresentado | Implementado |
| NFR-02 | Manter trilho básico de operações de escrita | tabela `audit_log` | teste verifica evento `sale.created` | Implementado; cobertura parcial |
| NFR-03 | Instalação repetível e operação documentada | `pyproject.toml`, `.env.example`, README | — | Implementado |
| NFR-04 | PostgreSQL persistente em ambiente serverless | `moto_pos/db.py`, `DATABASE_URL`, `.python-version`, `app.py` | Teste de guard Vercel; testes de integração PostgreSQL pendentes | Implementado; PostgreSQL real não configurado |

## Pendências de requisitos

Confirmar com a equipa: impostos, descontos, fatura fiscal e séries documentais, devoluções/anulações, múltiplas unidades por venda, papéis de utilizador, concorrência esperada, deployment, backup, retenção e integração contabilística. A solução atual não deve ser tratada como aceite para produção enquanto estes pontos não forem decididos.
