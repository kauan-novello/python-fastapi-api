# Backend

Boilerplate de API em FastAPI com autenticação JWT, SQLAlchemy async e Alembic.

Este projeto serve como base genérica para iniciar novas APIs. Os módulos de
auth e users são exemplos prontos para adaptação ou remoção conforme a
necessidade do projeto.

## 📋 Configuração Rápida

1. **Clone e prepare o ambiente:**

```bash
cd backend
cp .env.example .env
poetry install
```

2. **Configure o banco de dados (desenvolvimento):**

SQLite é padrão (arquivo local). Para PostgreSQL, edite `DATABASE_URL` no `.env`.

3. **Rode as migrations:**

```bash
poetry run alembic upgrade head
```

4. **Inicie localmente:**

```bash
poetry run task run
```

Acesse `http://localhost:8000/docs` (Swagger) para testar os endpoints.

## Inicialização (Local)

Siga estes passos para rodar a API localmente com Poetry:

1. Abra o diretório do projeto e ative o ambiente do Poetry:

```bash
cd backend
poetry shell
```

2. Instale as dependências (após ativar o shell ou usando `poetry run`):

```bash
poetry install
```

3. Configure variáveis de ambiente (copie `.env.example`):

```bash
cp .env.example .env
# Edite .env com suas configurações
```

4. Execute migrations do banco:

```bash
poetry run alembic upgrade head
```

5. Rodar linters, formatadores e testes (opcionais):

```bash
poetry run task format    # formata o código
poetry run task lint      # verifica lint
poetry run task type_check # type-checking com mypy
poetry run task test      # roda a suíte de testes
```

6. Rodar a aplicação em modo desenvolvimento (hot reload):

```bash
poetry run task run
```

Ou use diretamente:

```bash
poetry run uvicorn backend.app:app --reload
```

## Inicialização (Docker Compose - Recomendado)

A forma mais rápida de rodar a API com banco de dados e cache:

```bash
cd backend
cp .env.docker .env.docker.local
# Edite .env.docker.local e mude SECRET_KEY para um valor seguro
docker compose --env-file .env.docker.local up -d
```

Acesse http://localhost:8000/docs para testar.

**Veja [DOCKER_COMPOSE.md](./DOCKER_COMPOSE.md) para mais detalhes.**

## Inicialização (Docker Manual)

Alternativa para construir e rodar a imagem Docker:

```bash
cd backend
docker build -t fastapi-boilerplate:latest .

docker run --rm -p 8000:8000 \
	-e DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/dbname" \
	-e SECRET_KEY="change-me" \
	fastapi-boilerplate:latest
```

## Execução

- Instalar dependências com Poetry.
- Rodar migrations com Alembic.
- Subir a API com o comando de desenvolvimento configurado no pyproject.

## Testes

Executar a suíte com pytest.

## 🔒 Segurança & Production

Este boilerplate inclui práticas seguras por padrão:

- ✅ JWT com Argon2 para hash de senhas
- ✅ CORS whitelist (não aceita `*`)
- ✅ Rate limiting por IP (login, registro, reset, etc.)
- ✅ Validação forte de senhas (8+ chars, maiúscula, digit, special char)
- ✅ Refresh token rotation (logout automático ao renovar)
- ✅ Migrations versionadas (Alembic)
- ✅ Roles (`user` / `admin`) com permissões por recurso
- ✅ Tokens revogados armazenados como hash (não em texto plano)
- ✅ Limpeza automática de tokens expirados no startup
- ✅ Health check com ping ao banco (`GET /health`)
- ✅ Logging configurável (`LOG_LEVEL`, `LOG_FORMAT=text|json`)
- ✅ Rate limiting em memória ou Redis (`RATE_LIMIT_BACKEND`)
- ✅ Type-checking (mypy)

### Rate limiting

Por padrão usa backend **memory** (por processo). Para múltiplos workers/réplicas,
configure Redis no `.env`:

```env
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
```

Com `memory`, o limite efetivo é multiplicado pelo número de processos Uvicorn/Gunicorn.

Endpoints limitados por IP (janela deslizante):

| Endpoint | Limite padrão |
|----------|----------------|
| `POST /auth/token` | 10 / hora |
| `POST /auth/register` | 10 / dia |
| `POST /auth/forgot-password` | 5 / hora |
| `POST /auth/reset-password` | 5 / hora |
| `POST /auth/verify-email` | 10 / hora |
| `POST /auth/resend-verification` | 5 / hora |

**Para deploy em produção, veja [DEPLOYMENT.md](DEPLOYMENT.md)** — guia completo com:
- Configuração de PostgreSQL
- Variáveis de ambiente seguras
- Docker setup
- Nginx/SSL
- Monitoramento
- Backups

## Rotas de Exemplo

### Auth
- `POST /auth/token` — login com e-mail/senha (campo OAuth2 `username` = e-mail;
  requer e-mail verificado; rate limit por IP)
- `POST /auth/refresh_token` — renovar token (com refresh token)
- `POST /auth/register` — criar conta
- `POST /auth/verify-email` — verificar email via token
- `POST /auth/resend-verification` — reenviar email de verificação
- `POST /auth/forgot-password` — solicitar reset de senha
- `POST /auth/reset-password` — resetar senha com token
- `POST /auth/logout` — fazer logout (revoga token)
- `GET /auth/me` — dados do usuário autenticado

### Users (autenticação obrigatória)

| Rota | Quem pode |
|------|-----------|
| `GET /users/?search=&offset=&limit=` | **admin** — lista paginada com `total` |
| `GET /users/{user_id}` | dono do id ou **admin** |
| `PUT /users/{user_id}` | dono do id ou **admin** (campos opcionais) |
| `DELETE /users/{user_id}` | dono do id ou **admin** |

Cadastro público: `POST /auth/register`. Novos usuários recebem `role=user`.
Para promover a admin, atualize `users.role` no banco (`admin`) até existir
endpoint de gestão.

### Health

`GET /health` retorna `status` (`ok` ou `degraded`) e `database` (`ok` ou `error`).

## Estrutura do Projeto

```
backend/
├── alembic.ini              # Configuração Alembic
├── Dockerfile               # Container produção
├── .dockerignore             # Arquivos acima do Docker
├── entrypoint.sh            # Startup com migrations
├── pyproject.toml           # Dependências Poetry
├── .env.example             # Variáveis modelo
├── README.md                # Este arquivo
├── DEPLOYMENT.md            # Guia de produção
├── migrations/              # Alembic migrations
├── backend/
│   ├── app.py               # FastAPI app + middleware
│   ├── configs/             # Settings, DB, Security
│   ├── controllers/         # Rotas (auth, users)
│   ├── services/            # Lógica de negócio
│   ├── repositories/        # Acesso a dados
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   └── utils/               # Utilities (rate limiter, etc)
└── tests/                   # Suíte de testes
```
