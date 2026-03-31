variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Deployment environment (production, staging)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name used for naming resources"
  type        = string
  default     = "actasynth"
}

variable "frontend_origin" {
  description = "Frontend URL allowed to call the Lambda Function URL (e.g. https://app.yoursite.com)"
  type        = string
}

# LLM API Keys (sensitive — pass via secrets.tfvars, never commit)
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
  default     = ""
}


# LangSmith (optional)
variable "langchain_api_key" {
  description = "LangSmith API key (optional)"
  type        = string
  sensitive   = true
  default     = ""
}

# Lambda sizing
variable "lambda_memory_mb" {
  description = "Lambda memory in MB (LangChain needs ~512MB minimum)"
  type        = number
  default     = 1024
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds (5 min covers slow LLM calls)"
  type        = number
  default     = 300
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}
