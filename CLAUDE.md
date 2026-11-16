# CLAUDE.md

## Project
`runbook-assistant` (working name): a Python/FastAPI service that answers questions about technical documentation (RAG on Amazon Bedrock) and cites its sources. The service itself is secondary. The goal is a portfolio project that shows how it is built, deployed and operated like a platform team would: Docker, AWS (ECS Fargate + ALB), Terraform, GitHub Actions, observability, and later Kubernetes (k3s, Helm, ArgoCD, Prometheus/Grafana).

Planning and decisions happen outside this repo, in a separate claude.ai project. The developer tells you which block of the plan he is working on and what its goal is. If something he asks conflicts with what you already know about the project, ask which is current instead of assuming. Do not change the scope on your own: propose improvements as optional and state their cost in time.

## Architecture and decisions (already made)
**App:** FastAPI with `POST /ingest` (split documents into chunks, embed with Bedrock, build a FAISS index), `POST /ask` (retrieve chunks, call a text model on Bedrock, answer with cited sources), `GET /health`, `GET /metrics`. Target design: the FAISS index is stored in S3 and loaded at startup (block 14). Until then it lives in `data/index/` on the local disk, and `/metrics` does not exist yet (stage B). Documents: Kubernetes documentation (CC BY 4.0, checked on the kubernetes.io footer; attribution in `data/docs/ATTRIBUTION.md`) plus the developer's own study notes; nothing private. Tests mock Bedrock. Minimal scope: if the AI part gets complicated, reduce it to a simple model call; the infrastructure is what matters.

**Models (verified Nov 16, 2026, region eu-north-1):** embeddings with Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`), vector length 1024. Text model: Amazon Nova Lite through the inference profile `eu.amazon.nova-lite-v1:0` (routes to eu-central-1, eu-north-1, eu-west-1, eu-west-3), called with the Converse API. Claude is not used for now: the Anthropic use-case form asks for company data the developer does not have; it can be reconsidered later. Region, model IDs and profile come from environment variables (`AWS_REGION`, `EMBEDDING_MODEL_ID`, `TEXT_MODEL_ID`), never hard-coded.

**Stage A:** Docker image in ECR; ECS Fargate behind an ALB. Terraform for everything (ECR, ECS, ALB, IAM, S3, CloudWatch, VPC with public/private subnets and security groups), organized in reusable modules with two environments (`dev` and `prod`, normally only `dev` is deployed), remote state in S3 with locking. GitHub Actions: on PR run ruff, pytest, Trivy (image and dependencies) and `terraform plan`; on merge build, push and deploy. AWS access from the pipeline via OIDC. App secrets in SSM Parameter Store. Structured logs to CloudWatch.

**Stage B:** metrics endpoint, dashboard, a CloudWatch alarm that really fires, AWS Budgets alert.

**Stage C (mandatory):** the same service on Kubernetes (k3s on a small EC2, or local k3d/kind), with Helm, ArgoCD, Prometheus and Grafana (plus Alertmanager). Ansible configures the EC2 that runs k3s.

**Optional, only if the developer asks:** GitLab CI mirror of the pipeline, SLOs/runbook/postmortem example, pgvector inside the cluster instead of FAISS, versioned re-indexing, LangChain.

**Out of scope:** Azure, GCP, EKS, RDS.

**Undecided on purpose (decide after stage A):** demo for third parties (live URL, simple page) and protecting the public endpoint with an API key and rate limit.

**AWS account facts (updated Nov 16, 2026):** free plan of the new AWS account type (with "Projects"), ~140 USD in credits (2 of 5 activities done), expires around Mar 25, 2027. No charges on the free plan; if credits run out, the account closes, so tear down costly resources every session. All services the project needs are included in the free plan (Bedrock, ECS, ECR, Elastic Load Balancing, VPC, S3, Systems Manager, CloudWatch, IAM, EC2). Project region: eu-north-1 (Stockholm). IAM Identity Center (SSO) is NOT available on this account type, and the console did not offer MFA for the IAM user: local access uses the IAM user `runbook-dev` (CLI only, no console password, no MFA) with the AWS CLI profile `runbook-dev` (activated with the shell alias `aws-runbook`; the `default` profile is empty on purpose). Bedrock inference quotas were 0 on the new account until AWS Support (case 179450495800211) fixed them; if a first call returns `ThrottlingException`, check Service Quotas before debugging code.

**To verify, do not assume:** S3 native state locking in Terraform (block 9), NAT/ALB/Fargate prices (block 10), Nova Lite prices (Bedrock pricing page). Upgrading to the paid plan keeps unused credits; only do it if the free plan blocks something.

## Current block
Update this section at the start of each session.
- Stage / block: A / block 3 (`/ingest` real) is DONE (Nov 16, 2026). Next: block 4 (`/ask` real).
- Done in block 3: `/ingest` is real and tested. Modules: `chunking.py`, `embeddings.py` (Titan, cached client, adaptive retries against `ThrottlingException`), `vector_store.py` (FAISS `IndexFlatIP` with normalized vectors = cosine similarity: `build_index`, `save_index`, `load_index`, `search`), `ingestion.py` (`build_chunks` rejects names outside `data/docs/`, `ingest_documents`). `/ingest` takes a list of file names inside `data/docs/`, rebuilds the index from scratch every time, answers 400 (invalid name) or 404 (missing file). Real run: 3 documents, 191 chunks. 13 tests pass, none call AWS.
- Next (block 4): load the index at startup (`load_index("data/index")`), embed the question, `search` top-k, similarity threshold (below it answer "I don't know" without calling the text model), prompt with context via the Converse API and Nova Lite, cite sources, write `eval/questions.md` (5 questions with expected source + 1 off-topic).
- Done when (block 4): 5 of 5 questions answer with the right source; the off-topic question says it does not know; results noted in `eval/`.
- To run `/ingest` or `/ask` for real: `aws-runbook`, export `AWS_REGION=eu-north-1`, `EMBEDDING_MODEL_ID`, `TEXT_MODEL_ID` in the same tab, start `uvicorn main:app --reload` from the repo root (paths are relative). A full ingest takes about 2 minutes (one Titan call per chunk).

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
- `data/docs/` (Kubernetes docs with `ATTRIBUTION.md`) is committed; `data/index/` is generated by `/ingest` and git-ignored. Paths are relative: run the app from the repo root.
- Files named `test_*.py` or `*_test.py` are collected by pytest: do not give that name to scripts that call AWS.

## Commands
Fill these in as they exist:
- Run locally: `uvicorn main:app --reload`
- Tests: `pytest`
- Lint: `ruff check .`
- Bedrock smoke test (needs `aws-runbook` and the env vars `AWS_REGION`, `EMBEDDING_MODEL_ID`, `TEXT_MODEL_ID`): `python scripts/bedrock_smoke.py`
