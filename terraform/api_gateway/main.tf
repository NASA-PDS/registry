# API Gateway REST API - Maintains backward compatibility with double-wrapped response
resource "aws_api_gateway_rest_api" "main" {
  name        = var.api_name
  description = var.api_description

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.common_tags
}

# /credentials resource
resource "aws_api_gateway_resource" "credentials" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "credentials"
}

# GET method on /credentials
resource "aws_api_gateway_method" "credentials_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.credentials.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for GET /credentials with request mapping template
resource "aws_api_gateway_integration" "credentials_lambda" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.credentials.id
  http_method = aws_api_gateway_method.credentials_get.http_method

  integration_http_method = "POST"  # Lambda requires POST for invocation
  type                    = "AWS"   # Non-proxy to support request mapping template
  uri                     = var.lambda_invoke_arn

  # Request mapping template to extract headers and body
  request_templates = {
    "application/json" = jsonencode({
      headers = {
        Authorization = "$input.params('Authorization')"
        IDToken       = "$input.params('IDToken')"
      }
      body = "$input.json('$')"
    })
  }

  passthrough_behavior = "WHEN_NO_TEMPLATES"
}

# Method response
resource "aws_api_gateway_method_response" "credentials_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.credentials.id
  http_method = aws_api_gateway_method.credentials_get.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# Integration response
resource "aws_api_gateway_integration_response" "credentials_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.credentials.id
  http_method = aws_api_gateway_method.credentials_get.http_method
  status_code = aws_api_gateway_method_response.credentials_200.status_code

  depends_on = [
    aws_api_gateway_integration.credentials_lambda
  ]
}

# Lambda permission to allow API Gateway to invoke the function
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # Allow invocation from any stage
  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    # Redeploy when the integration changes
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.credentials.id,
      aws_api_gateway_method.credentials_get.id,
      aws_api_gateway_integration.credentials_lambda.id,
      aws_api_gateway_integration_response.credentials_200.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_method.credentials_get,
    aws_api_gateway_integration.credentials_lambda
  ]
}

# Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name

  tags = var.common_tags
}
