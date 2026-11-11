# CLAUDE.md

## Project
`runbook-assistant` (working name): a Python/FastAPI service that answers questions about technical documentation (RAG on Amazon Bedrock) and cites its sources. The service itself is secondary. The goal is a portfolio project that shows how it is built, deployed and operated like a platform team would: Docker, AWS (ECS Fargate + ALB), Terraform, GitHub Actions, observability, and later Kubernetes (k3s, Helm, ArgoCD, Prometheus/Grafana).

Planning and decisions happen outside this repo, in a separate claude.ai project. The developer tells you which block of the plan he is working on and what its goal is. If something he asks conflicts with what you already know about the project, ask which is current instead of assuming. Do not change the scope on your own: propose improvements as optional and state their cost in time.

## Architecture and decisions (already made)
**App:** FastAPI with `POST /ingest` (split documents into chunks, embed with Bedrock, build a FAISS index), `POST /ask` (retrieve chunks, call a Claude model on Bedrock, answer with cited sources), `GET /health`, `GET /metrics`. The FAISS index is stored in S3 and loaded at startup. Documents: Kubernetes documentation (license to verify) plus the developer's own study notes; nothing private. Tests mock Bedrock. Minimal scope: if the AI part gets complicated, reduce it to a simple model call; the infrastructure is what matters.

**Stage A:** Docker image in ECR; ECS Fargate behind an ALB. Terraform for everything (ECR, ECS, ALB, IAM, S3, CloudWatch, VPC with public/private subnets and security groups), organized in reusable modules with two environments (`dev` and `prod`, normally only `dev` is deployed), remote state in S3 with locking. GitHub Actions: on PR run ruff, pytest, Trivy (image and dependencies) and `terraform plan`; on merge build, push and deploy. AWS access from the pipeline via OIDC. App secrets in SSM Parameter Store. Structured logs to CloudWatch.

**Stage B:** metrics endpoint, dashboard, a CloudWatch alarm that really fires, AWS Budgets alert.

**Stage C (mandatory):** the same service on Kubernetes (k3s on a small EC2, or local k3d/kind), with Helm, ArgoCD, Prometheus and Grafana (plus Alertmanager). Ansible configures the EC2 that runs k3s.

**Optional, only if the developer asks:** GitLab CI mirror of the pipeline, SLOs/runbook/postmortem example, pgvector inside the cluster instead of FAISS, versioned re-indexing, LangChain.

**Out of scope:** Azure, GCP, EKS, RDS.

**Undecided on purpose (decide after stage A):** demo for third parties (live URL, simple page) and protecting the public endpoint with an API key and rate limit.

**AWS account facts (verified Nov 11, 2026):** free plan of the new AWS account type (with "Projects"), ~120 USD in credits, expires around Mar 25, 2027. No charges on the free plan; if credits run out, the account closes, so tear down costly resources every session. All services the project needs are included in the free plan (Bedrock, ECS, ECR, Elastic Load Balancing, VPC, S3, Systems Manager, CloudWatch, IAM, EC2). IAM Identity Center (SSO) is NOT available on this account type: local access uses an IAM user with MFA and an AWS CLI profile. Bedrock models are enabled by default; Anthropic models need a one-time use-case form. Titan Text Embeddings V2 runs in-region in eu-central-1.

**To verify, do not assume:** Claude models in eu-central-1 (Frankfurt) are only available through cross-region inference, and the docs for this account type say cross-region features are not supported. Test Claude in Frankfurt at block 2; fallback region: eu-west-1 (Ireland) or eu-north-1 (Stockholm), where Claude Sonnet 5 is in-region. Also verify at the time: Kubernetes docs license (block 3), S3 native state locking in Terraform (block 9), NAT/ALB/Fargate prices (block 10). Upgrading to the paid plan keeps unused credits; only do it if the free plan blocks something.

## Current block
Update this section at the start of each session.
- Stage / block: A / block 2 (Thu Nov 12) — Bedrock access from the Mac. Blocks 0 and 1 are done (commit `aebbe95`).
- Goal: a Python script talks to a Claude model and to the embeddings model on Bedrock.
- Steps: IAM user (not root) with MFA + AWS CLI profile; in the Bedrock playground (Frankfurt) submit the Anthropic form and test Claude, switch region to eu-west-1 / eu-north-1 if it fails; fix region and model IDs; install `boto3`; smoke-test script in `scripts/` calling Claude and Titan Embeddings V2; region and model IDs from environment variables.
- Done when: `aws sts get-caller-identity --profile <name>` returns the IAM user; the script prints a Claude answer and the embedding vector length; region and models recorded here under "Architecture and decisions"; no credentials in the repo.

## Who I work with
The developer is learning Terraform, Kubernetes and CI/CD while building this. He must be able to explain every part of the project in a job interview without AI help. Reply to him in Spanish. Code, comments, commit messages, names and the README are in English.

## How to work
- Explain each new concept briefly, with an example, before asking him to use it.
- He decides in each part who writes the code: if he already knows the concept, you may write it; if it is new, you explain and he writes it with your guidance; or split it: he writes the essential parts with your explanation and you do the repetitive ones. If he has not said which, ask before starting that part. For Terraform and the GitHub Actions pipeline the default is that he writes them and you explain, point out mistakes and review line by line.
- Whoever writes it, he reviews every line and must understand it. Do not let him move on with something he cannot explain.
- Work in small steps matching the current block. Start each block by stating its goal and its "done when".
- If he is stuck on the same problem for more than 90 minutes, stop and propose stepping back.
- Say clearly when something is an estimate or when you are not sure (AWS prices, regions, Bedrock models, free plan limits). Say how to check it.

## Security
- Never put AWS keys, tokens or secrets in the repo, in commit history or in chat. Local access uses the AWS CLI profile. The pipeline uses OIDC. App secrets go in SSM Parameter Store.
- Keep `.env` and credentials files in `.gitignore`. If a secret shows up in a diff, stop and explain how to rotate it.
- IAM: least privilege. No administrator permissions for the app or the pipeline.

## Costs
Monthly AWS budget: 20 EUR (25 EUR if needed). Before suggesting anything that costs money, give the approximate cost and how to tear it down. At the end of each session that used AWS, remind him to run `terraform destroy` on costly resources (load balancer, ECS service, EC2) and check the console.

## Code conventions
- Python 3.12, FastAPI, pytest, ruff. Tests must not call Bedrock (mock it).
- Small, frequent commits with clear messages. One logical change per commit.
- Keep the code simple. Prefer clarity over cleverness.

## Commands
Fill these in as they exist:
- Run locally: `uvicorn main:app --reload`
- Tests: `pytest`
- Lint: `ruff check .`
