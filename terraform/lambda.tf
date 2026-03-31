resource "aws_lambda_function" "app" {
  function_name = "${var.app_name}-${var.environment}"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.app.repository_url}:latest"

  memory_size = var.lambda_memory_mb
  timeout     = var.lambda_timeout_seconds

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      LOG_LEVEL            = "info"
      ALLOWED_ORIGINS      = jsonencode([var.frontend_origin])

      # LLM API Keys
      OPENAI_API_KEY    = var.openai_api_key
      ANTHROPIC_API_KEY = var.anthropic_api_key
      GOOGLE_API_KEY    = var.google_api_key

      # Cognito (User Pool created in eu-west-1 by cognito.tf)
      COGNITO_REGION        = var.aws_region
      COGNITO_USER_POOL_ID  = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID     = aws_cognito_user_pool_client.frontend.id

      # LangSmith (optional)
      LANGCHAIN_TRACING_V2 = var.langchain_api_key != "" ? "true" : "false"
      LANGCHAIN_API_KEY    = var.langchain_api_key
      LANGCHAIN_PROJECT    = var.app_name
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

