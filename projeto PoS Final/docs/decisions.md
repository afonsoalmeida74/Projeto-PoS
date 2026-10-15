# Registo de decisões

| ID | Decisão | Justificação e trade-off | Estado |
|---|---|---|---|
| ADR-001 | Aplicação web Flask | Interface acessível no navegador e ecossistema Python simples; requer servidor WSGI adequado para produção. | Implementado |
| ADR-002 | SQLite local e PostgreSQL remoto | SQLite simplifica o desenvolvimento local; Vercel exige armazenamento remoto persistente. | Implementado; PostgreSQL ainda sem migrações versionadas |
| ADR-003 | Preços em cêntimos inteiros | Evita erros de ponto flutuante em valores monetários. | Implementado |
| ADR-004 | Uma mota por venda, sem edição de preço | Mantém o fluxo transacional simples e o total derivado do preço de inventário; descontos e linhas múltiplas ficam para requisitos futuros. | Implementado |
| ADR-005 | Pagamento registado, sem processamento | Evita tratar dados sensíveis de cartão e integração financeira no protótipo. | Implementado |
| ADR-006 | Recibo interno, sem alegação fiscal | Requisitos fiscais não foram especificados nem validados. | Implementado com limitação documentada |
| ADR-007 | PostgreSQL por `DATABASE_URL` no alojamento | Mantém a SQLite local e evita depender do filesystem efémero das Functions. | Implementado; exige provisionar e configurar base externa |

## Requisitos ainda por confirmar

Volume de utilizadores simultâneos, uso numa ou várias lojas, perfis e permissões, impostos/descontos, devoluções e anulações, formato fiscal, integrações contabilísticas, retenção de dados, backups e ambiente de deployment. As escolhas atuais são pressupostos de uma primeira versão, não requisitos aprovados pelo negócio.
