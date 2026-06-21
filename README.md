# nerofy-ingestion

Lambda de ingestão de dados financeiros via webhooks da Pluggy. Processa eventos SQS, busca dados na API Pluggy e persiste no S3 (bronze) e DynamoDB.

---

## Pré-requisitos

- Python 3.12
- Docker (para modo LocalStack)
- Terraform (para provisionar infra local)
- AWS SAM CLI (para invoke via SAM)

```bash
pip install -r requirements-dev.txt
```

---

## Modos de execução

| Modo | Docker | AWS real | Pluggy | Saída |
|---|---|---|---|---|
| **Mock** | Não | Não | Mockada | `local_output/` |
| **LocalStack** | Sim | Não | Mockada | LocalStack (S3 + DynamoDB) |
| **SAM (AWS)** | Sim | Sim | Real | AWS |

---

## Modo Mock

Roda sem Docker. Todas as dependências (S3, DynamoDB, Pluggy) são substituídas por fakes.

**1. Configurar `.env`:**
```
EXECUCAO=mock
```

**2. Invocar:**
```bash
python scripts/invoke_local.py item          # item atualizado (padrão)
python scripts/invoke_local.py transactions  # transações
python scripts/invoke_local.py connector     # conector
```

Saída salva em `local_output/`.

---

## Modo LocalStack

Usa boto3 real apontando para o LocalStack. S3 e DynamoDB funcionam de verdade. Pluggy permanece mockada.

**1. Subir o LocalStack:**
```bash
docker compose -f docker/compose.yaml up -d
```

Aguardar o container ficar saudável:
```bash
docker ps --filter "name=localstack"
```

**2. Provisionar infra local via Terraform (uma vez por sessão):**
```bash
terraform -chdir=infra/local init     # apenas na primeira vez
terraform -chdir=infra/local apply -auto-approve
```

Cria: bucket S3 `nerofy-bronze-dev`, tabelas DynamoDB `PluggyAuth` e `PluggyTransactionSync`, fila SQS `nerofy-events`.

**3. Invocar:**
```bash
python scripts/invoke_localstack.py item
python scripts/invoke_localstack.py transactions
python scripts/invoke_localstack.py connector
```

**4. Verificar dados gravados:**
```bash
# Arquivos no S3
aws --endpoint-url=http://localhost:4566 s3 ls s3://nerofy-bronze-dev --recursive

# Registros no DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name PluggyTransactionSync
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name PluggyAuth
```

**5. Derrubar o LocalStack:**
```bash
docker compose -f docker/compose.yaml down
```

---

## Modo SAM (AWS real)

Invoca a Lambda localmente via SAM CLI apontando para a AWS real (perfil `nerofy`).

```bash
python scripts/invoke_aws.py item
python scripts/invoke_aws.py transactions
python scripts/invoke_aws.py connector
```

---

## Build do pacote Lambda

Gera `lambda_local.zip` com o código e dependências para deploy manual ou no LocalStack:

```bash
.\scripts\build_local_lambda.ps1
```

---

## Testes

```bash
# Unitários
pytest src/tests/ --ignore=src/tests/integration

# Todos (requer AWS configurada)
pytest src/tests/
```

---

## Eventos disponíveis

| Arquivo | Tipo |
|---|---|
| `events/sqs_item_update.json` | Item atualizado |
| `events/sqs_transactions.json` | Transações |
| `events/sqs_connector.json` | Conector |

---

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `EXECUCAO` | Modo de execução: `aws`, `local`, `mock` | `aws` |
| `S3_BRONZE_BUCKET` | Nome do bucket S3 | — |
| `DYNAMO_AUTH_TABLE` | Tabela DynamoDB de autenticação | `PluggyAuth` |
| `DYNAMO_SYNC_TABLE` | Tabela DynamoDB de sincronização | `PluggyTransactionSync` |
| `PLUGGY_CLIENT_SECRET` | Secret da API Pluggy | — |
| `SSM_PLUGGY_SECRET_PATH` | Caminho SSM para buscar o secret | — |
| `AWS_REGION` | Região AWS | `sa-east-1` |
| `LOG_LEVEL` | Nível de log | `INFO` |

---

## Fluxo de CI/CD

```
feature/* → develop → release/X.Y → main → deploy AWS
hotfix/*  ──────────────────────→ main → deploy AWS
```

| Branch | Pipeline |
|---|---|
| `feature/**`, `fix/**`, etc. | Quality + Unit Tests → PR para develop |
| `develop` | Quality + Unit Tests → cria `release/X.Y` automaticamente |
| `release/**` | Quality + Unit Tests + Integration Tests → PR para main |
| `main` | Build + Terraform + Deploy Lambda na AWS |
