# Testes Locais

Existem dois modos de execução local, ambos sem depender da AWS real.

---

## Modo Mock (`EXECUCAO=mock`)

Roda completamente sem Docker. Usa implementações fake de S3, DynamoDB e Pluggy API. Saída salva em `local_output/`.

**Pré-requisito:** `EXECUCAO=mock` no `.env`

```bash
python scripts/invoke_local.py item
python scripts/invoke_local.py transactions
python scripts/invoke_local.py connector
```

---

## Modo Local (`EXECUCAO=local`) — com LocalStack

Usa boto3 real apontando para o LocalStack. Pluggy API permanece mockada. Dados gravados de verdade no S3 e DynamoDB locais.

### 1. Configurar token

Edite `docker/.env` com seu token do [app.localstack.cloud](https://app.localstack.cloud):

```
LOCALSTACK_AUTH_TOKEN=ls-seu-token-aqui
```

### 2. Subir o LocalStack

```bash
docker compose -f docker/compose.yaml --env-file docker/.env up -d
```

Aguarde o container aparecer como `(healthy)`:

```bash
docker ps --filter "name=localstack"
```

### 3. Criar recursos AWS via Terraform (recomendado)

Rode uma única vez por sessão (os dados são perdidos ao reiniciar o container).
Os arquivos Terraform já estão em `infra/local/` configurados para o LocalStack:

```bash
terraform -chdir=infra/local init   # apenas na primeira vez
terraform -chdir=infra/local apply -auto-approve
```

Isso cria: bucket S3 `nerofy-bronze-dev`, tabelas DynamoDB `PluggyAuth` e `PluggyTransactionSync`, e fila SQS `nerofy-events`.

> **Alternativa sem Terraform** (via AWS CLI):
> ```bash
> export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=sa-east-1
> aws --endpoint-url=http://localhost:4566 s3 mb s3://nerofy-bronze-dev
> aws --endpoint-url=http://localhost:4566 dynamodb create-table --table-name PluggyAuth \
>   --attribute-definitions AttributeName=clientId,AttributeType=S \
>   --key-schema AttributeName=clientId,KeyType=HASH --billing-mode PAY_PER_REQUEST
> aws --endpoint-url=http://localhost:4566 dynamodb create-table --table-name PluggyTransactionSync \
>   --attribute-definitions AttributeName=accountId,AttributeType=S \
>   --key-schema AttributeName=accountId,KeyType=HASH --billing-mode PAY_PER_REQUEST
> ```

### 4. Invocar os eventos

```bash
python scripts/invoke_localstack.py item
python scripts/invoke_localstack.py transactions
python scripts/invoke_localstack.py connector
```

### 5. Verificar os dados gravados

```bash
# Arquivos no S3
aws --endpoint-url=http://localhost:4566 s3 ls s3://nerofy-bronze-local --recursive

# Registros no DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name PluggyTransactionSync
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name PluggyAuth

# Ler um arquivo S3 específico
aws --endpoint-url=http://localhost:4566 s3 cp s3://nerofy-bronze-local/<caminho-do-arquivo> -
```

### 6. Derrubar o LocalStack

```bash
docker compose -f docker/compose.yaml down
```

---

## Comparativo

| | Mock | Local (LocalStack) |
|---|---|---|
| Docker necessário | Não | Sim |
| S3 / DynamoDB reais | Não | Sim (LocalStack) |
| Pluggy API | Mockada | Mockada |
| Saída | `local_output/` | LocalStack (S3 + DynamoDB) |
| Uso | Desenvolvimento rápido | Validação da infra AWS |
