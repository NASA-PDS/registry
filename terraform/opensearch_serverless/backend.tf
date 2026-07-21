terraform {
  backend "s3" {
    # Backend configuration values provided via backend-config.tfvars
    # Example backend-config.tfvars content:
    #   bucket         = "pds-infra"
    key            = "registry/opensearch_serverless.tfstate"
    #   region         = "us-east-1"
    #   dynamodb_table = "terraform-state-lock"
    #   encrypt        = true
    #   profile        = "your-aws-profile"
  }
}
