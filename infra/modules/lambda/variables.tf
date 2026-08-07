variable "dynamodb_table_arn" {
  type        = string
  description = "ARN da tabela Simulados_AWS (Query + BatchGetItem)"
}

variable "historico_table_arn" {
  type        = string
  description = "ARN da tabela Historico_Simulados (PutItem + Query + GetItem)"
}

variable "simulados_detalhes_table_arn" {
  type        = string
  description = "ARN da tabela Simulados_Detalhes (PutItem + GetItem)"
}

variable "turmas_table_arn" {
  type        = string
  description = "ARN da tabela Turmas (PutItem + Query + GetItem + UpdateItem + DeleteItem)"
}
