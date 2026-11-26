output "repository_url" {
  description = "ECR repository URI, used for docker tag and docker push"
  value       = aws_ecr_repository.app.repository_url
}