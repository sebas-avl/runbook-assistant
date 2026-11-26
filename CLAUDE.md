# runbook-assistant

A FastAPI service that answers questions about technical documentation with
RAG on Amazon Bedrock and cites its sources. The app is deliberately small; the
repo is about deploying and operating it (Docker, Terraform, ECS, GitHub Actions,
later Kubernetes). The app, its Docker image, CI (GitHub Actions), the
Terraform remote state, the AWS network and the ECR repository exist so far.
See README.md for setup and how it works.

## Layout

```
main.py            Endpoints: /ingest, /ask, /health, /.
ingestion.py       Docs -> chunks -> Titan embeddings -> FAISS index.
retrieval.py       Top-3 search and the MIN_SCORE threshold.
generation.py      Prompt + Nova Lite call (Converse API).
data/docs/         Source docs (Kubernetes, CC BY 4.0, committed).
data/index/        Built by POST /ingest. Git-ignored.
eval/              Questions with expected sources, and the latest results.
.github/workflows/ CI on every pull request and push to main: job test (ruff,
                   pytest) and job scan (Trivy on the image and dependencies).
infra/bootstrap/   Terraform: the S3 bucket for remote state. Its own state lives
                   in that bucket (key bootstrap/terraform.tfstate).
infra/persistent/  Terraform: what survives sessions (ECR repository). Never
                   destroyed at the end of a session.
infra/app/         Terraform: what runs and bills by the hour. Destroyed after
                   every session. State in the S3 bucket.
                   network.tf: VPC, subnets, IGW, NAT, route tables, SGs.
docs/              Architecture diagram (network.png) and network.md.
```

## Commands

- Install: `pip install -r requirements-dev.txt` (app + test and lint tools; the
  Docker image installs only `requirements.txt`).
- Run: `uvicorn main:app --reload` from the repo root (paths are relative).
- Test: `pytest` (one test: `pytest test_main.py::test_ask`). Lint: `ruff check .`
- Coverage: `pytest --cov=. --cov-report=term-missing` (only the real Bedrock
  calls stay uncovered, on purpose).
- Bedrock connection check: `python scripts/bedrock_smoke.py`
- Docker: `docker build --platform linux/amd64 -t runbook-assistant:dev .` (run
  command in README.md).
- Terraform: from `infra/bootstrap/`, `infra/persistent/` or `infra/app/`,
  `terraform init`, `terraform fmt`, `terraform validate`, `terraform plan`.
  Needs `AWS_PROFILE=runbook-dev` in the tab.
- Push the image to ECR: in `infra/persistent/`,
  `REPO=$(terraform output -raw repository_url)`,
  `TAG=$(git rev-parse --short HEAD)` and
  `REGISTRY=$(echo $REPO | cut -d/ -f1)`; then
  `aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin $REGISTRY`,
  and from the repo root
  `docker build --platform linux/amd64 -t $REPO:$TAG .` and `docker push $REPO:$TAG`.

## Things that will bite you

- **AWS settings live in the shell, not the repo.** `/ingest`, `/ask` and the
  smoke test need `AWS_PROFILE=runbook-dev`, `AWS_REGION=eu-north-1`,
  `EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0` and
  `TEXT_MODEL_ID=eu.amazon.nova-lite-v1:0` in the same terminal tab. A new tab
  fails with `KeyError: 'AWS_REGION'`.
- **There is no index until `POST /ingest` runs.** `data/index/` is
  git-ignored, so a fresh clone answers 404 on `/ask` until the index is built.
- **Read env vars inside functions, never at import.** That is what lets
  `pytest` run without AWS. Tests must not call Bedrock: monkeypatch where the
  function is used (`main.retrieve`, `ingestion.embed_text`), not where it is defined.
- **Don't name AWS scripts `test_*.py` or `*_test.py`.** pytest collects them
  and calls Bedrock on every run.
- **The FAISS ids are list positions.** `metadata.json` must stay in the same
  order as the vectors, or answers cite the wrong text.
- **`/ask` reloads the index on every request on purpose.** `/ingest` rebuilds
  it; loading once at startup would serve a stale index.
- **`MIN_SCORE` (0.25) was tuned on 6 questions.** After changing it, the
  chunking or `k`, rerun `eval/` and record the results. Never change an expected
  source without writing why.
- **Don't run `pip freeze > requirements.txt`.** It mixes the test tools back
  into the app's list and they end up in the image. App packages go in
  `requirements.txt`, test and lint tools in `requirements-dev.txt`, pinned.
- **Build for `linux/amd64`.** Fargate runs x86; an image built on an Apple
  Silicon Mac without `--platform` is ARM and will not start there.
- **The container runs as `appuser` and can only write to `data/index/`.**
  Writing anywhere else fails with `PermissionError`; change the `chown` in the
  Dockerfile if the app needs a new writable folder.
- **The image copies only `*.py` from the root and `data/docs/`.** A new folder
  the app needs must get its own `COPY`; `test_*.py` and secrets are excluded by
  `.dockerignore`.
- **`main` is protected.** Direct pushes are rejected: work on a branch and open
  a PR. The required checks are named after the CI jobs (`test` and `scan`);
  renaming a job blocks every merge until the ruleset is updated.
- **`scan` fails on any CRITICAL vulnerability that has a fix.** In the image or
  in either requirements file. Fix it by upgrading the package; don't loosen
  the Trivy settings in `ci.yml`.
- **`ThrottlingException` on a first Bedrock call is a quota, not a bug.** New
  accounts can start with inference quotas at 0; check Service Quotas.
- **Never commit Terraform state.** `*.tfstate` and `.terraform/` are
  git-ignored; `.terraform.lock.hcl` is committed on purpose so every machine
  uses the same provider version.
- **`infra/bootstrap/` stores its state in the bucket it creates.** If the
  bucket were ever lost, remove the `backend` block and run
  `terraform init -migrate-state` to go back to local state before re-creating
  it; existing resources are recovered with `terraform import`.
- **Nothing persistent goes in `infra/app/`.** Its `destroy` runs after every
  session; ECR, data and IAM belong in `infra/persistent/`.
- **ECR tags are immutable.** One commit, one image: pushing an existing tag
  fails. Tag with `git rev-parse --short HEAD` and recompute `TAG` after every
  commit or merge; a shell variable does not update itself.
- **The NAT Gateway and its Elastic IP bill per hour.** Run `terraform destroy`
  in `infra/app/` after every session and check in the console that no NAT
  Gateway or Elastic IP is left.
- **`docs/network.png` must match `network.tf`.** Update the diagram and
  `docs/network.md` in the same PR as any network change.
- **`runbook-dev` has least-privilege IAM.** Its policy `runbook-terraform` only
  allows the state bucket, the keys `app/`, `persistent/` and `bootstrap/`,
  the network actions (EC2/VPC) in `eu-north-1` and the `runbook-assistant` ECR
  repository. A new state key or a new AWS service needs the policy updated
  first; add permissions from the `AccessDenied` message.

## Working agreement

Code, comments and commits in English. One logical change per commit. Work on a
branch and merge through a pull request. Ask before creating, changing or
destroying AWS resources.
