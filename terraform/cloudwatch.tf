resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.app_name}-${var.environment}"
  retention_in_days = var.log_retention_days
}

# Metric filter: count successful workflow completions
resource "aws_cloudwatch_log_metric_filter" "workflow_completed" {
  name           = "WorkflowCompletions"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "{ $.event = \"workflow_execution_completed\" }"

  metric_transformation {
    name          = "WorkflowExecutions"
    namespace     = "Actasynth"
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

# Metric filter: count workflow failures
resource "aws_cloudwatch_log_metric_filter" "workflow_failed" {
  name           = "WorkflowFailures"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "{ $.event = \"workflow_execution_failed\" }"

  metric_transformation {
    name          = "WorkflowErrors"
    namespace     = "Actasynth"
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

# Metric filter: extract LLM cost per workflow
resource "aws_cloudwatch_log_metric_filter" "workflow_cost" {
  name           = "WorkflowCost"
  log_group_name = aws_cloudwatch_log_group.lambda.name
  pattern        = "{ $.event = \"workflow_execution_completed\" && $.total_cost_usd = * }"

  metric_transformation {
    name          = "WorkflowCostUSD"
    namespace     = "Actasynth"
    value         = "$.total_cost_usd"
    default_value = "0"
    unit          = "None"
  }
}

# Alarm: alert when error rate is high
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "${var.app_name}-${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WorkflowErrors"
  namespace           = "Actasynth"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "More than 5 workflow failures in 5 minutes"
  treat_missing_data  = "notBreaching"
}
