# ECR: the private registry for the app image. Kept across sessions (not in infra/app)

resource "aws_ecr_repository" "app" {
  name                 = "runbook-assistant"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "runbook-assistant"
  }
}

# Lifecycle Policy for the repository
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the 10 most recent images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }

      action = {
        type = "expire"
      }
    }]
  })
}