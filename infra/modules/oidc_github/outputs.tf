output "oidc_provider_arn" {
  value       = local.oidc_provider_arn
  description = "ARN do Provedor OIDC do GitHub"
}

output "role_arn" {
  value       = aws_iam_role.github_actions.arn
  description = "ARN da Role IAM criada para o GitHub Actions (é o valor usado na secret AWS_ROLE_ARN)"
}

output "role_name" {
  value       = aws_iam_role.github_actions.name
  description = "Nome da Role IAM do GitHub Actions"
}
