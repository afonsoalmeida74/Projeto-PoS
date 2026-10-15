# Segurança e privacidade

## Controlos implementados

- Palavras-passe armazenadas com `werkzeug.security` (hash adaptativo); nunca são guardadas em claro.
- Sessões assinadas pelo Flask, com `HttpOnly` e `SameSite=Lax`. `Secure` pode ser ativado com `COOKIE_SECURE=1` em HTTPS.
- Token CSRF verificado em todos os pedidos de alteração, incluindo início de sessão.
- As rotas funcionais exigem sessão autenticada. O redirecionamento pós-login aceita apenas caminhos locais.
- SQL parametrizado, chaves estrangeiras e restrições de unicidade/estado/preço em SQLite local e PostgreSQL remoto.
- A venda confirma a disponibilidade e regista venda, alteração de stock e auditoria na mesma transação (`BEGIN IMMEDIATE` em SQLite; transação SQL em PostgreSQL).
- Templates Jinja escapam conteúdo por omissão. Não há recolha de PAN, CVV ou outros dados de cartão.

## Riscos e medidas operacionais

- **Segredo e credenciais iniciais:** `SECRET_KEY` e `ADMIN_PASSWORD` devem ser valores fortes e exclusivos. Não guardar `.env` no controlo de versões. A conta inicial não tem fluxo de alteração/recuperação de palavra-passe: alterar credenciais requer processo operacional adicional.
- **Transporte:** usar apenas em localhost até existir configuração de produção com HTTPS, servidor WSGI, cabeçalhos de segurança e gestão de segredos.
- **Dados pessoais:** nomes, email e telefone são dados pessoais. Limitar acesso ao computador e à base de dados, definir retenção e cópias protegidas, e determinar fundamento/prazos legais com a organização.
- **Integridade e recuperação:** WAL melhora a concorrência SQLite local, mas não é backup. PostgreSQL remoto requer pooling e política própria de cópias/restauro.
- **Auditoria:** regista criação de motas/clientes e vendas, mas não é imutável nem cobre autenticações falhadas, leitura/exportação ou alterações administrativas.
- **Faturação:** o recibo apresentado é um comprovativo interno e não afirma cumprir requisitos fiscais portugueses.

## Fora do âmbito de segurança desta versão

Autorização por função, limitação de tentativas de login, MFA, rotação de sessões, política de retenção, exportação/apagamento de dados, migrações, backup/restore automatizados, monitorização e revisão independente de segurança.

## Revisão antes de produção

Requer avaliação de ameaças, requisitos fiscais e de proteção de dados, gestão de contas e funções, configuração de deployment, política de backup/recuperação, revisão de dependências e teste de segurança. Estes itens não foram verificados nesta versão.
