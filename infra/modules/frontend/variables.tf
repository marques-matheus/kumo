variable "bucket_name" {
  type        = string
  description = "Nome do bucket S3 para hospedar os arquivos estáticos do frontend (DEVE ser único globalmente)"
  default     = "simulados-aws-frontend-web"
}

variable "environment" {
  type        = string
  description = "Ambiente de implantação"
  default     = "prod"
}
