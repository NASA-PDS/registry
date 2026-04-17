locals {
  module_name = "get_awskeys_from_cognitojwt"
  lambda_name = "pds-registry-get-awskeys-from-cognitojwt"

  layer_name  = "pds-registry-lambda-layer"
  source_file = "${path.module}/src/${local.module_name}.py"
  handler     = "${local.module_name}.lambda_handler"

  # Construct JWKS URL from User Pool ID and region
  # Format: https://cognito-idp.{region}.amazonaws.com/{user-pool-id}/.well-known/jwks.json
  jwks_url = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}/.well-known/jwks.json"

  # Hash of layer files to trigger rebuild when dependencies change
  layer_files_hash = fileexists("${path.module}/src/layer/requirements.txt") ? filesha256("${path.module}/src/layer/requirements.txt") : "none"
}

# CloudWatch Log Group for Lambda function
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = 14

  tags = var.common_tags
}

resource "null_resource" "build_trigger" {
  triggers = {
    source_py_hash = filesha256(local.source_file)
    build_layer_exists = fileexists("${path.module}/build/${local.lambda_name}.zip") ? "yes" : "no"
  }

}

# Package the lambda source file as a zip

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = local.source_file
  output_path = "${path.module}/build/${local.lambda_name}.zip"
  depends_on  = [null_resource.build_trigger]
}

# Prepare Lambda Layer with Python dependencies
resource "null_resource" "prepare_layer" {
  triggers = {
    files_hash = local.layer_files_hash
  }

  provisioner "local-exec" {
    command = "rm -fr ${path.module}/build/layer/python && mkdir -p ${path.module}/build/layer/ && cp -r ${path.module}/src/layer ${path.module}/build/layer/python && pip install -r ${path.module}/build/layer/python/requirements.txt -t ${path.module}/build/layer/python"
  }

}

# Package the layer as a zip
data "archive_file" "lambda_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/layer"
  output_path = "${path.module}/build/layer.zip"
  depends_on  = [null_resource.prepare_layer]
}

# Create Lambda Layer
resource "aws_lambda_layer_version" "layer" {
  layer_name          = local.layer_name
  filename            = data.archive_file.lambda_layer_zip.output_path
  compatible_runtimes = [var.runtime]
  description         = "Common dependencies for PDS Registry Lambda (requests package)"
  depends_on          = [data.archive_file.lambda_layer_zip]

  source_code_hash = data.archive_file.lambda_layer_zip.output_base64sha256
}

resource "aws_lambda_function" "this" {
  function_name    = local.lambda_name
  runtime          = var.runtime
  handler          = local.handler
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = var.lambda_execution_role_arn
  timeout          = var.timeout
  memory_size      = var.memory_size

  # Attach the Lambda Layer
  layers = [aws_lambda_layer_version.layer.arn]

  environment {
    variables = {
      COGNITO_ALLOWED_GROUPS   = join(",", var.cognito_allowed_groups)
      COGNITO_USER_POOL_ID     = var.cognito_user_pool_id
      COGNITO_IDENTITY_POOL_ID = var.cognito_identity_pool_id
      COGNITO_JWKS_URL         = local.jwks_url
    }
  }

  # Explicitly configure CloudWatch Logs
  logging_config {
    log_format = "JSON"
    application_log_level = "DEBUG"
  }

  tags = var.common_tags

  depends_on = [
    data.archive_file.lambda_zip,
    aws_cloudwatch_log_group.lambda_logs,
    aws_lambda_layer_version.layer
  ]
}
