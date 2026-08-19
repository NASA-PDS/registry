terraform {
  backend "s3" {
    key = "registry/opensearch_managed_security.tfstate"
    # bucket, region, dynamodb_table, encrypt, profile provided via backend-config.tfvars
  }
}
