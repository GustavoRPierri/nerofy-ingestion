# Infraestrutura — nerofy-ingestion

Toda a infraestrutura é provisionada via Terraform na AWS (região `sa-east-1`).

## Estrutura

```
infra/
├── backend.tf          # Provider AWS e estado remoto no S3
├── main.tf             # Lambda function + Layer + trigger SQS
├── iam.tf              # Role e policies da Lambda
├── sqs.tf              # Fila de eventos
├── s3.tf               # Bucket bronze (dados brutos)
├── dynamodb.tf         # Tabelas de autenticação e sincronização
├── variables.tf        # Variáveis configuráveis
├── outputs.tf          # Valores exportados após o apply
└── integration-test/   # Infraestrutura temporária usada pelo CI
```

---

## Recursos criados em produção

### Lambda
- **Função:** `nerofy-ingestion` (Python 3.12, 256 MB, timeout 60s)
- **Handler:** `lambda_handler.lambda_handler`
- **Layer:** dependências do `requirements.txt` empacotadas separadamente

### SQS
- **Fila:** `nerofy-events`
- Visibility timeout de 300s (igual ao timeout da Lambda)
- Retenção de mensagens: 24h
- Configurada para receber mensagens do API Gateway (webhook da Pluggy)
- Gatilho da Lambda com batch de 10 mensagens e `ReportBatchItemFailures`

### S3
- **Bucket:** `nerofy-bronze-dev` (configurável via variável)
- Versionamento habilitado
- Criptografia AES256 server-side
- Acesso público bloqueado

### DynamoDB
- **`PluggyAuth`** — armazena credenciais de autenticação Pluggy (PK: `clientId`)
- **`PluggyTransactionSync`** — controla a sincronização de transações por conta (PK: `accountId`)
- Ambas no modo `PAY_PER_REQUEST`

### IAM
A role da Lambda tem permissão para:
- Escrever logs no CloudWatch (`AWSLambdaBasicExecutionRole`)
- `s3:PutObject` e `s3:GetObject` no bucket bronze
- `dynamodb:GetItem`, `PutItem`, `UpdateItem` nas duas tabelas
- `ssm:GetParameter` no path do secret da Pluggy
- `sqs:ReceiveMessage`, `DeleteMessage`, `GetQueueAttributes` na fila

### State remoto
O estado do Terraform fica no S3, com lock via DynamoDB:
- **Bucket:** `nerofy-terraform-state` (com versionamento)
- **Tabela de lock:** `terraform-state-lock` (PK: `LockID`)
- **Chave do estado:** `nerofy-finance/terraform.tfstate`

> Esses recursos precisam existir antes do primeiro `terraform init`. Crie-os manualmente uma única vez.

---

## Infraestrutura de testes (`integration-test/`)

Usada exclusivamente pelo CI durante a `release/**`. Sobe um ambiente isolado na AWS para rodar os testes de integração e destrói tudo ao final.

Cada execução de CI cria recursos com sufixo único baseado no `run_id` do GitHub Actions, evitando conflitos entre execuções paralelas:

| Recurso | Nome |
|---|---|
| Lambda | `nerofy-ingestion-test-{suffix}` |
| S3 | `nerofy-bronze-test-{run_id}` |
| DynamoDB Auth | `PluggyAuth-test-{suffix}` |
| DynamoDB Sync | `PluggyTransactionSync-test-{suffix}` |

O estado desse ambiente fica no mesmo bucket S3 com chave `nerofy-finance-test/{run_id}/terraform.tfstate`.

---

## Variáveis

| Variável | Padrão | Descrição |
|---|---|---|
| `aws_region` | `sa-east-1` | Região AWS |
| `lambda_function_name` | `nerofy-ingestion` | Nome da função Lambda |
| `s3_bronze_bucket` | `nerofy-bronze-dev` | Nome do bucket S3 |
| `ssm_pluggy_secret_path` | `/nerofy/pluggy/client_secret` | Path do secret no SSM Parameter Store |
| `log_level` | `INFO` | Nível de log da Lambda |
| `environment` | `dev` | Ambiente (`dev`, `prod`) |

---

## Deploy

O deploy é feito automaticamente pelo CI ao fazer merge em `main`. Para rodar manualmente:

```bash
cd infra
terraform init
terraform plan
terraform apply
```
