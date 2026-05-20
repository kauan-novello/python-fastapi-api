# Backend

Boilerplate de API em FastAPI com autenticação JWT, SQLAlchemy async e Alembic.

Este projeto serve como base genérica para iniciar novas APIs. Os módulos de
auth e users são exemplos prontos para adaptação ou remoção conforme a
necessidade do projeto.

## Configuração

Crie um arquivo `.env` com as variáveis necessárias para o seu ambiente.

Se o `poetry install` falhar em Linux por erro de keyring/secretstorage, rode
`poetry config keyring.enabled false` e tente novamente.

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

3. (Opcional) Se o `pyproject.toml` foi alterado e o `poetry.lock` ficou desatualizado, atualize o lock sem atualizar pacotes:

```bash
poetry lock --no-update
poetry install
```

4. Rodar linters, formatadores e testes (opcionais):

```bash
poetry run task format    # formata o código
poetry run task pre_lint  # verifica textos e lint leves
poetry run task test      # roda a suíte de testes
```

5. Rodar a aplicação em modo desenvolvimento (hot reload):

```bash
poetry run uvicorn backend.app:app --reload
```

Ou use o atalho configurado em `pyproject.toml`:

```bash
poetry run task run
```

## Inicialização (Docker)

Este repositório inclui um `Dockerfile` para construir a imagem da API. Exemplo de uso:

1. Construir a imagem Docker (a partir do diretório `backend`):

```bash
cd backend
docker build -t fastapi-boilerplate:latest .
```

2. Rodar um contêiner usando SQLite local (mapeando o diretório atual):

```bash
docker run --rm -p 8000:8000 \
	-v "$PWD":/app \
	-e DATABASE_URL=sqlite+aiosqlite:///./database.db \
	fastapi-boilerplate:latest
```

3. Rodar com um banco PostgreSQL externo (exemplo):

```bash
docker run --rm -p 8000:8000 \
	-e DATABASE_URL="postgresql+psycopg://user:pass@host:5432/dbname" \
	-e SECRET_KEY="change-me" \
	fastapi-boilerplate:latest
```

Notas:
- Ajuste as variáveis de ambiente conforme necessário (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Para produção, não use o `SECRET_KEY` padrão e prefira um armazenamento seguro para segredos.

## Execução

- Instalar dependências com Poetry.
- Rodar migrations com Alembic.
- Subir a API com o comando de desenvolvimento configurado no pyproject.

## Testes

Executar a suíte com pytest.

## Rotas de exemplo

- `GET /`
- `GET /health`
- `POST /auth/token`
- `POST /auth/refresh_token`
- `POST /users/`
- `GET /users/`
- `GET /users/{user_id}`
- `PUT /users/{user_id}`
- `DELETE /users/{user_id}`

As rotas de auth e users podem ser substituídas por recursos do seu domínio.
