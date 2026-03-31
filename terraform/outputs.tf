output "api_endpoint" {
  description = "API Gateway HTTPS endpoint"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing Docker images"
  value       = aws_ecr_repository.app.repository_url
}

output "lambda_function_name" {
  description = "Lambda function name (for aws lambda update-function-code)"
  value       = aws_lambda_function.app.function_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID — give this to the frontend team (VITE_COGNITO_USER_POOL_ID)"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  description = "Cognito App Client ID — give this to the frontend team (VITE_COGNITO_CLIENT_ID)"
  value       = aws_cognito_user_pool_client.frontend.id
}

output "cognito_region" {
  description = "Cognito region (eu-west-1)"
  value       = var.aws_region
}
