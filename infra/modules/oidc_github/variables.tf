variable "github_repo" {
  type        = string
  description = "Repositório do GitHub no formato 'dono/repositorio' autorizado a assumir a role"
  default     = "marques-matheus/simulados-aws"
}

variable "role_name" {
  type        = string
  description = "Nome da role IAM a ser assumida via OIDC pelo GitHub Actions"
  default     = "github-actions-simulados-role"
}

variable "create_oidc_provider" {
  type        = bool
  description = "Define se o Provedor OIDC do GitHub deve ser criado na conta AWS (defina como false se já existir um provedor para token.actions.githubusercontent.com na sua conta)"
  default     = true
}

variable "existing_oidc_provider_arn" {
  type        = string
  description = "ARN do Provedor OIDC existente (caso create_oidc_provider seja false)"
  default     = ""
}
