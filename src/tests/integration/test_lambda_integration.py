"""
Testes de integração contra a Lambda efêmera criada pelo Terraform.

Validam a infraestrutura AWS (Lambda, DynamoDB, S3) sem depender de
credenciais reais da Pluggy — o EXECUCAO=local na Lambda evita fetch do SSM,
e a falha eventual na API Pluggy é tratada pela Lambda (retorna 200 ou 500).
"""

import json


class TestLambdaInfrastructure:
    """Verifica que a Lambda e recursos de suporte foram criados corretamente."""

    def test_lambda_exists_and_is_active(self, lambda_client, test_lambda_name):
        response = lambda_client.get_function(FunctionName=test_lambda_name)
        state = response["Configuration"]["State"]
        assert state == "Active", f"Lambda deveria estar Active, está: {state}"

    def test_dynamo_auth_table_active(self, dynamo_client, test_dynamo_auth_table):
        response = dynamo_client.describe_table(TableName=test_dynamo_auth_table)
        status = response["Table"]["TableStatus"]
        assert status == "ACTIVE", f"Tabela DynamoDB deveria estar ACTIVE, está: {status}"

    def test_dynamo_sync_table_active(self, dynamo_client, test_dynamo_sync_table):
        response = dynamo_client.describe_table(TableName=test_dynamo_sync_table)
        status = response["Table"]["TableStatus"]
        assert status == "ACTIVE", f"Tabela DynamoDB deveria estar ACTIVE, está: {status}"

    def test_s3_bucket_accessible(self, s3_client, test_s3_bucket):
        # head_bucket retorna 200 se o bucket existe e é acessível
        response = s3_client.head_bucket(Bucket=test_s3_bucket)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


class TestLambdaInvocation:
    """Valida o comportamento da Lambda ao receber eventos via invocação direta."""

    def test_invalid_event_returns_400(self, lambda_client, test_lambda_name, sqs_event_invalid):
        """Evento sem estrutura SQS → Lambda deve retornar statusCode 400."""
        response = lambda_client.invoke(
            FunctionName=test_lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(sqs_event_invalid).encode(),
        )
        assert response["StatusCode"] == 200, "Invocação Lambda falhou (erro de infraestrutura)"

        result = json.loads(response["Payload"].read())
        assert (
            result["statusCode"] == 400
        ), f"Evento inválido deveria retornar 400, retornou: {result}"

    def test_valid_sqs_event_returns_structured_response(
        self, lambda_client, test_lambda_name, sqs_event_valid
    ):
        """Evento SQS válido → Lambda deve retornar resposta JSON estruturada."""
        response = lambda_client.invoke(
            FunctionName=test_lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(sqs_event_valid).encode(),
        )
        assert response["StatusCode"] == 200, "Invocação Lambda falhou (erro de infraestrutura)"

        result = json.loads(response["Payload"].read())
        assert "statusCode" in result, "Resposta da Lambda deve conter 'statusCode'"
        assert "body" in result, "Resposta da Lambda deve conter 'body'"
        # 200 = sucesso completo, 500 = falha ao chamar Pluggy API (sem credenciais reais)
        assert result["statusCode"] in (200, 500), f"statusCode inesperado: {result['statusCode']}"

    def test_lambda_not_crashed_by_concurrent_events(
        self, lambda_client, test_lambda_name, sqs_event_invalid
    ):
        """Múltiplas invocações sequenciais não devem causar crash ou estado corrompido."""
        for i in range(3):
            response = lambda_client.invoke(
                FunctionName=test_lambda_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(sqs_event_invalid).encode(),
            )
            assert response["StatusCode"] == 200, f"Invocação {i+1} falhou na infraestrutura"
            result = json.loads(response["Payload"].read())
            assert "statusCode" in result, f"Resposta {i+1} mal-formada: {result}"
