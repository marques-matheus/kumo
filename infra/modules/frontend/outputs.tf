output "bucket_name" {
  value       = aws_s3_bucket.frontend.id
  description = "Nome do bucket S3 do frontend"
}

output "bucket_arn" {
  value       = aws_s3_bucket.frontend.arn
  description = "ARN do bucket S3"
}

output "cloudfront_id" {
  value       = aws_cloudfront_distribution.cdn.id
  description = "ID da distribuição CloudFront (usado na invalidação de cache pelo GitHub Actions)"
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.cdn.domain_name
  description = "Domínio público do CloudFront (URL do site estático)"
}

output "cloudfront_arn" {
  value       = aws_cloudfront_distribution.cdn.arn
  description = "ARN do CloudFront"
}
