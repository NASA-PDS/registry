locals {
  module_name = "get_awskeys_from_cognitojwt"
  lambda_name = "pds-registry-get-awskeys-from-cognitojwt"

  layer_name  = "pds-registry-lambda-layer"
  source_file = "${path.module}/src/${local.module_name}.py"
  handler     = "${local.module_name}.lambda_handler"

  # Construct JWKS URL from User Pool ID and region
  # Format: https://cognito-idp.{region}.amazonaws.com/{user-pool-id}/.well-known/jwks.json
  jwks_url = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}/.well-known/jwks.json"

  # The layer is identified by its inputs (requirements + runtime), NOT by the bytes of the built zip.
  # The zip is not reproducible across machines (pip version, platform, absolute paths in scripts),
  # and build/ is git-ignored so it does not exist in a fresh checkout (e.g. the terragrunt cache).
  layer_inputs_hash = sha256(join("|", [
    filesha256("${path.module}/src/layer/requirements.txt"),
    var.runtime,
  ]))
  layer_zip_path = "${path.module}/build/layer.zip"
  python_version = trimprefix(var.runtime, "python")
}

# CloudWatch Log Group for Lambda function
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = 14

  tags = var.common_tags
}

# Package the lambda source file as a zip.
# Read at plan time from the sources only, so the hash is stable wherever the module is checked out.
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = local.source_file
  output_path = "${path.module}/build/${local.lambda_name}.zip"
}

# Build the Lambda Layer zip with the Python dependencies.
# Only re-runs when the requirements or runtime change (not based on the presence of files in build/).
resource "null_resource" "build_layer" {
  triggers = {
    layer_inputs_hash = local.layer_inputs_hash
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      build_dir="${path.module}/build/layer"
      rm -rf "$build_dir" "${local.layer_zip_path}"
      mkdir -p "$build_dir/python"
      # Target the Lambda runtime (linux x86_64), not the machine running terraform.
      python3 -m pip install \
        --requirement "${path.module}/src/layer/requirements.txt" \
        --target "$build_dir/python" \
        --platform manylinux2014_x86_64 --implementation cp \
        --python-version "${local.python_version}" --only-binary=:all: \
        --no-compile --disable-pip-version-check 2>&1 | tee /tmp/layer-build.log
      rm -rf "$build_dir/python/bin"
      (cd "$build_dir" && zip -qr "../layer.zip" python)
    EOT
  }
}

# Create Lambda Layer
resource "aws_lambda_layer_version" "layer" {
  layer_name          = local.layer_name
  filename            = local.layer_zip_path
  compatible_runtimes = [var.runtime]
  description         = "Common dependencies for PDS Registry Lambda (requests package)"

  # Derived from inputs: the provider keeps this value in state, so the layer is only
  # republished when the requirements or runtime change.
  source_code_hash = local.layer_inputs_hash

  depends_on = [null_resource.build_layer]
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

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}
