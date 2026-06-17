resource "aws_dynamodb_table" "pluggy_auth" {
  name         = "PluggyAuth"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "clientId"

  attribute {
    name = "clientId"
    type = "S"
  }
}

resource "aws_dynamodb_table" "transaction_sync" {
  name         = "PluggyTransactionSync"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "accountId"

  attribute {
    name = "accountId"
    type = "S"
  }
}
