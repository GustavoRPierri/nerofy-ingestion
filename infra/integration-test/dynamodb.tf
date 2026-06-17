resource "aws_dynamodb_table" "pluggy_auth_test" {
  name         = "PluggyAuth-test-${local.suffix}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "clientId"

  attribute {
    name = "clientId"
    type = "S"
  }
}

resource "aws_dynamodb_table" "transaction_sync_test" {
  name         = "PluggyTransactionSync-test-${local.suffix}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "accountId"

  attribute {
    name = "accountId"
    type = "S"
  }
}
