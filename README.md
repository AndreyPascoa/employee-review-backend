# Employee Review — backend

API de avaliação de desempenho desenvolvida com Python, FastAPI, SQLAlchemy e PostgreSQL. Permite que líderes avaliem seus subordinados diretos e indiretos e consultem a avaliação mais recente, com as respostas e a nota ponderada.

O [frontend em Next.js](https://github.com/AndreyPascoa/employee-review-frontend) consome esta API e oferece seleção de líder, listagem da equipe, formulário e consulta dos resultados.

## Tecnologias e requisitos

- Python 3.12 no ambiente Docker descrito abaixo, atendendo ao requisito Python 3.10+ do case.
- FastAPI e Uvicorn para a API HTTP e documentação OpenAPI.
- Pydantic para configuração e validação das entradas.
- SQLAlchemy e Psycopg para conexão, transações e consultas parametrizadas.
- PostgreSQL 17 para armazenamento local.
- Alembic para versionamento do esquema e carga dos dados iniciais.

As versões das dependências estão fixadas em `requirements.txt`. Para o procedimento principal, instale Git e Docker Desktop com contêineres Linux. Não é necessário instalar Python ou PostgreSQL no Windows.

**Os comandos deste guia são para o Prompt de Comando do Windows (CMD)**, executados no computador, salvo os blocos SQL indicados. No PowerShell, substitua `%cd%` pelo caminho absoluto do repositório no comando de montagem do contêiner.

## Retomar um ambiente já configurado

Se o banco, o usuário, o ambiente Python e as migrations já foram preparados conforme este guia:

```cmd
docker start employee-review-db employee-review-backend
docker exec -it -w /app employee-review-backend /opt/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mantenha esse terminal aberto. Se já houver uma instância da API em execução na porta 8000, use-a em vez de iniciar uma segunda. Para preparar uma instalação nova, siga as etapas abaixo.

## Instalação do zero

### 1. Obter o projeto

```cmd
git clone https://github.com/AndreyPascoa/employee-review-backend.git
cd employee-review-backend
```

Os próximos comandos que utilizam a pasta atual devem ser executados na raiz deste repositório, onde estão `requirements.txt` e `alembic.ini`.

### 2. Criar a rede e iniciar o PostgreSQL

Abra o Docker Desktop e aguarde o motor de contêineres iniciar. Crie a rede e o volume uma única vez:

```cmd
docker network create employee-review-network
docker volume create employee-review-postgres-data
```

Se a rede já existir, reutilize-a. O volume guarda o banco mesmo quando o contêiner é removido. Os nomes deste guia devem ser exclusivos no seu Docker; quem já tem os contêineres configurados deve usar a seção de retomada.

Substitua `SENHA_ADMIN_LOCAL` pela senha administrativa escolhida antes de executar:

```cmd
docker run -d --name employee-review-db --network employee-review-network --restart unless-stopped -p 127.0.0.1:5432:5432 -e "POSTGRES_USER=postgres" -e "POSTGRES_PASSWORD=SENHA_ADMIN_LOCAL" -e "POSTGRES_DB=employee_reviews" -v employee-review-postgres-data:/var/lib/postgresql/data postgres:17-bookworm
```

Confira se o banco está pronto. Repita após alguns segundos se ainda estiver inicializando:

```cmd
docker exec employee-review-db pg_isready -U postgres -d employee_reviews
```

O resultado esperado contém `accepting connections`. As variáveis `POSTGRES_*` inicializam apenas um volume vazio: mudar a senha no comando não altera a senha de um banco já existente.

### 3. Preparar o usuário e o schema da aplicação

Abra o console do PostgreSQL:

```cmd
docker exec -it employee-review-db psql -U postgres -d employee_reviews
```

Execute no prompt do **psql**, em um banco novo:

```sql
CREATE ROLE employee_app LOGIN;
```

Defina a senha da aplicação pelo comando do psql:

```text
\password employee_app
```

Digite a senha escolhida e repita quando solicitado. Os caracteres não aparecem enquanto você digita. Essa será a senha usada em `DB_PASSWORD`; ela pode ser diferente da senha administrativa do PostgreSQL.

Ainda no psql:

```sql
GRANT CONNECT ON DATABASE employee_reviews TO employee_app;
CREATE SCHEMA employee_reviews AUTHORIZATION employee_app;
ALTER ROLE employee_app IN DATABASE employee_reviews SET search_path TO employee_reviews, public;
```

Saia com:

```text
\q
```

**O schema precisa existir antes das migrations.** A tabela de controle do Alembic também é criada dentro de `employee_reviews`. A aplicação e as migrations utilizam `employee_app`, proprietário desse schema, sem usar a conta administrativa `postgres`.

### 4. Configurar as variáveis de ambiente

Na raiz do repositório, crie ou ajuste o arquivo `.env`:

```dotenv
DB_HOST=employee-review-db
DB_PORT=5432
DB_NAME=employee_reviews
DB_USER=employee_app
DB_PASSWORD="SENHA_DEFINIDA_PARA_EMPLOYEE_APP"
```

Substitua o exemplo de `DB_PASSWORD` pela senha definida com `\password employee_app`. Não use literalmente os marcadores de senha deste guia.

| Variável | Finalidade |
| --- | --- |
| `DB_HOST` | Endereço do PostgreSQL; dentro da rede Docker, use `employee-review-db` |
| `DB_PORT` | Porta do banco, `5432` por padrão |
| `DB_NAME` | Nome do banco: `employee_reviews` |
| `DB_USER` | Usuário da aplicação: `employee_app` |
| `DB_PASSWORD` | Senha desse usuário |

O arquivo é carregado por `app/config.py`, a partir do diretório de execução. Por isso os comandos da API e das migrations usam `/app`. Reinicie a aplicação após alterar a configuração. Não há chave de API externa necessária para este projeto.

### 5. Criar o contêiner Python e instalar dependências

Ainda na raiz do repositório, no CMD do Windows:

```cmd
docker run -dit --name employee-review-backend --network employee-review-network --restart unless-stopped -p 127.0.0.1:8000:8000 --mount "type=bind,source=%cd%,target=/app" -w /app python:3.12-slim-bookworm sleep infinity
docker exec employee-review-backend python -m venv /opt/venv
docker exec -w /app employee-review-backend /opt/venv/bin/python -m pip install -r requirements.txt
```

A pasta local é montada em `/app`: alterações no código ficam disponíveis dentro do contêiner. O ambiente virtual `/opt/venv` mantém as dependências separadas do Python base.

Nesta versão, o backend é preparado com comandos Docker, sem Dockerfile ou Compose próprios. O processo `sleep infinity` mantém o contêiner disponível, mas **não inicia a API automaticamente**. Se o contêiner for removido e criado novamente, repita a instalação das dependências; o ambiente virtual está no contêiner, enquanto o código está na pasta local.

### 6. Aplicar as migrations

```cmd
docker exec -w /app employee-review-backend /opt/venv/bin/python -m alembic upgrade head
docker exec -w /app employee-review-backend /opt/venv/bin/python -m alembic current
```

A revisão final esperada nesta versão é `938845197e21`. O Alembic registra as revisões aplicadas; executar `upgrade head` novamente não repete os dados iniciais.

| Migration | Responsabilidade |
| --- | --- |
| `0810fbba8499` | Cria funcionários e relações de liderança; insere 20 funcionários e 19 vínculos |
| `dc9b292442a6` | Cria as seis questões e seus pesos |
| `e25ba93b9dda` | Cria avaliações, respostas, restrições e índice de consulta |
| `938845197e21` | Protege avaliações e respostas contra atualização, exclusão e `TRUNCATE` |

As migrations já incluem a carga inicial baseada no dump do case. **Não importe o dump por cima desse esquema.** Para usar um banco previamente importado por outro processo, é necessário reconciliar sua estrutura e o histórico do Alembic antes de aplicar as migrations.

### 7. Iniciar a API

```cmd
docker exec -it -w /app employee-review-backend /opt/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Mantenha o terminal aberto e aguarde `Application startup complete`. O parâmetro `--reload` serve para desenvolvimento e reinicia a aplicação quando o código muda. Encerre a API com `Ctrl+C`.

- Swagger interativo: [http://localhost:8000/docs](http://localhost:8000/docs)
- Documentação ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Contrato OpenAPI: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- Verificação do processo: [http://localhost:8000/health](http://localhost:8000/health)

`/health` verifica somente se a API responde; não testa a conexão com o banco. Para conferir também o banco e as migrations, consulte `/api/leaders` e `/api/questions`.

### Alternativa: Python instalado no computador

Mantenha o PostgreSQL com a porta 5432 publicada. No `.env`, altere apenas o host para `DB_HOST=127.0.0.1`. Com Python 3.12 instalado e na raiz do projeto, use no CMD:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Essa alternativa substitui o contêiner Python. As etapas de preparação do banco, usuário e schema continuam necessárias.

## Conectar o frontend

Siga também o [README do frontend](https://github.com/AndreyPascoa/employee-review-frontend#readme).

- Next.js em contêiner na mesma rede: `API_BASE_URL=http://employee-review-backend:8000`.
- Next.js executado no computador: `API_BASE_URL=http://127.0.0.1:8000`.

O navegador chama `/api/...` no frontend; o servidor Next.js encaminha as solicitações para o FastAPI. Não há conexão direta do navegador com o PostgreSQL.

Na pasta do frontend, com a API em execução:

```cmd
docker compose up --build -d
```

O frontend usa a porta definida no seu `compose.yaml`: `5173` no exemplo original ou `5174` se ajustada para evitar conflito. Alterar a porta externa do frontend não muda o endereço interno do backend.

## Identificação do líder

O case dispensa login completo. A API recebe o identificador do usuário pelo cabeçalho `X-Leader-ID`; o frontend permite escolher um líder e guarda a seleção no `localStorage`.

| Líder de exemplo | ID | Subordinados diretos e indiretos |
| --- | --- | --- |
| Alice Hartman | 1 | 19 |
| Bob Sinclair | 2 | 12 |
| David Okafor | 4 | 4: Henry, James, Karen e Liam |

A lista completa está em `GET /api/leaders`. O cabeçalho identifica o usuário para a demonstração, mas não comprova sua identidade. A verificação de hierarquia é executada no servidor tanto para envio quanto para consulta.

## Endpoints

| Método | Caminho | Cabeçalho `X-Leader-ID` | Resultado |
| --- | --- | --- | --- |
| GET | `/health` | Não | Estado do processo HTTP |
| GET | `/api/leaders` | Não | Líderes disponíveis: `id`, `name` |
| GET | `/api/questions` | Não | Questões: `id`, `title`, `weight` |
| GET | `/api/employees` | Sim | Subordinados: `id`, `name`, `email`, `position_name` |
| POST | `/api/evaluations` | Sim | Cria avaliação e seis respostas na mesma transação |
| GET | `/api/evaluations/employee/{employee_id}/latest` | Sim | Última avaliação, respostas e nota ponderada |

A API não oferece operações de edição ou exclusão de avaliações. O histórico completo é opcional no enunciado e não está implementado.

### Exemplo de envio

No Swagger, abra `POST /api/evaluations`, clique em **Try it out**, informe `X-Leader-ID: 4` e utilize:

```json
{
  "employee_id": 8,
  "answers": [
    { "question_id": 1, "score": 3 },
    { "question_id": 2, "score": 4 },
    { "question_id": 3, "score": 3 },
    { "question_id": 4, "score": 2 },
    { "question_id": 5, "score": 4 },
    { "question_id": 6, "score": 3 }
  ]
}
```

Em um par ainda não avaliado na semana, a resposta é `201`, com `id`, `leader_id`, `employee_id`, `week_start` e `submitted_at`. Consulte depois `/api/evaluations/employee/8/latest` com o mesmo cabeçalho para obter `answers` e `weighted_score`. A nota desse exemplo é `3,15`; o valor decimal é serializado como string no JSON.

### Respostas de erro

| Código | Situação |
| --- | --- |
| 403 | Funcionário fora da hierarquia permitida, incluindo o próprio usuário |
| 404 | Identificador do usuário não encontrado ou funcionário autorizado ainda sem avaliação |
| 409 | Avaliação já enviada pelo mesmo líder para o mesmo funcionário na semana |
| 422 | Entrada inválida: cabeçalho ausente/inválido, notas fora de 1 a 4, questões duplicadas, ausentes ou diferentes das cadastradas |

## Regras e decisões de implementação

### Período semanal e independência dos líderes

A semana começa na segunda-feira às 00h e termina na segunda seguinte às 00h, no fuso `America/Sao_Paulo`. O banco calcula `week_start` no momento do envio. Essa delimitação foi adotada porque o enunciado não define explicitamente o início da semana.

A restrição única `(leader_id, employee_id, week_start)` permite uma avaliação por par a cada semana e impede duplicidade mesmo com solicitações concorrentes. A avaliação de outro líder não consome esse limite. Por exemplo, Bob e David podem avaliar Henry na mesma semana.

### Hierarquia e avaliação mais recente

Consultas recursivas percorrem os vínculos de liderança. O usuário só pode avaliar ou consultar seus subordinados diretos e indiretos; não pode consultar a si mesmo, seus pares ou superiores.

A expressão “respeitando sempre a maior hierarquia” não define claramente uma prioridade entre avaliações de autores diferentes. A interpretação adotada verifica a relação entre quem consulta e o funcionário avaliado, independentemente do autor da avaliação. Assim, David pode consultar a avaliação de Henry feita por Bob.

O registro mais recente é selecionado por `submitted_at` e, em caso de empate, `id`. Não há preferência por cargo do autor. Essa interpretação está explícita para ser confirmada caso o responsável pelo case espere outra regra.

### Respostas, pesos e cálculo

Cada envio exige exatamente as seis questões cadastradas, sem repetição, com notas inteiras de 1 a 4. Campos extras no corpo são rejeitados.

| Questão | Peso |
| --- | --- |
| Entrega de Resultados | 25 |
| Execução e Qualidade do Trabalho | 20 |
| Capacidade de Aprendizado e Desenvolvimento | 20 |
| Resolução de Problemas e Pensamento Crítico | 15 |
| Colaboração, Influência e Liderança | 10 |
| Visão Estratégica e Potencial de Crescimento | 10 |

A nota ponderada é `soma(nota × peso) / soma(pesos)`. A consulta utiliza os pesos cadastrados nas questões. Não há funcionalidade de edição desses pesos; alterar o catálogo diretamente no banco afetaria os cálculos das consultas anteriores.

### Transações e imutabilidade

Avaliação e respostas são gravadas na mesma transação: uma falha desfaz o envio. A restrição única protege o limite semanal. Triggers do PostgreSQL rejeitam `UPDATE`, `DELETE` e `TRUNCATE` em avaliações e respostas enviadas. A interface apresenta esses registros somente para leitura.

## Arquitetura e organização

```text
Navegador / frontend Next.js
        |
        | HTTP + X-Leader-ID (via proxy do Next.js)
        v
FastAPI: rotas, validação e dependências
        |
        v
Serviços de avaliação: hierarquia, questões e transação
        |
        v
SQLAlchemy / Psycopg: SQL parametrizado
        |
        v
PostgreSQL: dados, restrições, índices e triggers
```

- `app/main.py`: cria a aplicação e registra os roteadores.
- `app/config.py`: lê e valida as variáveis de conexão.
- `app/database.py`: configura o engine e fornece uma sessão por requisição.
- `app/dependencies.py`: lê `X-Leader-ID` e confere a existência do usuário.
- `app/routers/`: define os endpoints; as consultas simples de líderes, questões e equipe ficam nesses módulos.
- `app/schemas/evaluations.py`: contratos de entrada e saída, notas e validação das seis respostas.
- `app/services/evaluations.py`: valida hierarquia e questões, grava avaliações e consulta o último resultado.
- `migrations/versions/`: evolução do banco, dados iniciais e proteção dos registros.
- `migrations/env.py`: conecta o Alembic ao banco configurado no `.env`.

Tabelas: `employee` armazena funcionários; `leader_lead`, os vínculos; `question`, o catálogo; `evaluation`, os envios; `answer`, as notas. Todas ficam no schema `employee_reviews`, junto de `alembic_version`, que registra a versão aplicada.

As consultas usam parâmetros vinculados, sem concatenar valores recebidos do usuário no SQL. Há índice por funcionário/data de envio para a consulta da última avaliação e restrições para relacionamentos, notas e unicidade semanal.

## Verificação manual

Com banco, migrations e API disponíveis:

1. Abra `/api/leaders` e `/api/questions`; devem retornar sete líderes e seis questões.
2. Consulte `/api/employees` com `X-Leader-ID: 4`; confira Henry (8), James (10), Karen (11) e Liam (12).
3. Envie as seis notas do exemplo para um par ainda livre na semana; espere `201` e consulte a nota `3,15`.
4. Repita o envio para o mesmo par; espere `409`, sem sobrescrever as respostas.
5. Envie para Henry com Bob (`X-Leader-ID: 2`); esse líder tem um limite independente.
6. Com David (`4`), tente consultar a última avaliação de David (`4`), de Eva (`5`, par) e de Bob (`2`, superior); espere `403`.
7. Atualize a interface e consulte o registro novamente para conferir a persistência.

As verificações que gravam avaliações consomem o limite semanal daquele par. Não execute exemplos de envio em dados que pretenda reservar para outra demonstração da mesma semana.

Este repositório ainda não contém uma suíte automatizada de testes do backend. Os testes do frontend com respostas simuladas não substituem esse roteiro nem comprovam as regras do banco.

## Operação e problemas comuns

- **API não responde após `docker start`:** o contêiner Python usa `sleep infinity`; inicie o Uvicorn conforme a seção de retomada.
- **Porta já ocupada:** confira `docker ps` e as aplicações locais. Use a API já ativa ou ajuste a porta externa e o endereço de acesso. Entre contêineres, a API continua na porta 8000.
- **`schema employee_reviews does not exist`:** execute a preparação do schema antes de `alembic upgrade head`.
- **Falha de autenticação no banco:** confira se `DB_PASSWORD` corresponde à senha do usuário `employee_app`, não necessariamente à senha de `postgres`.
- **Nome do banco não resolve:** no contêiner, use `DB_HOST=employee-review-db` e mantenha ambos na rede `employee-review-network`. Fora do Docker, use `127.0.0.1`.
- **Tabela já existe ao migrar:** verifique se houve importação manual ou criação anterior fora do Alembic. Não use `stamp head` apenas para esconder o erro; ele não executa migrations.

Para conferir o estado dos contêineres e as mensagens do PostgreSQL:

```cmd
docker ps -a
docker logs --tail=50 employee-review-db
```

As mensagens do Uvicorn aparecem no terminal em que foi iniciado por `docker exec`. Para encerrar, pressione `Ctrl+C` nesse terminal e depois:

```cmd
docker stop employee-review-backend employee-review-db
```

Parar os contêineres preserva o banco. Não remova `employee-review-postgres-data` se quiser manter as avaliações.

## Ambiente de demonstração

Os funcionários e vínculos são dados do desafio. A troca de usuário por cabeçalho e a configuração local demonstrativa são propositais para facilitar a avaliação do case. O `.env` presente no repositório deve ser ajustado para o ambiente de quem executa; os exemplos não devem ser reutilizados como credenciais de produção.

O mecanismo `X-Leader-ID` não implementa autenticação. Uma implantação real exigiria identidade autenticada e configuração de segredos apropriada. O escopo desta entrega é a execução local descrita acima.
