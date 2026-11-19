# runbook-assistant

A FastAPI service that answers questions about technical documentation with
RAG on Amazon Bedrock and cites its sources. The app is deliberately small; the
repo is about deploying and operating it (Docker, Terraform, ECS, GitHub Actions,
later Kubernetes). Only the app exists so far. See README.md for setup and how
it works.

## Layout

```
main.py            Endpoints: /ingest, /ask, /health, /.
ingestion.py       Docs -> chunks -> Titan embeddings -> FAISS index.
retrieval.py       Top-3 search and the MIN_SCORE threshold.
generation.py      Prompt + Nova Lite call (Converse API).
data/docs/         Source docs (Kubernetes, CC BY 4.0, committed).
data/index/        Built by POST /ingest. Git-ignored.
eval/              Questions with expected sources, and the latest results.
```

## Commands

- Install: `pip install -r requirements-dev.txt` (app + test and lint tools; the
  Docker image installs only `requirements.txt`).
- Run: `uvicorn main:app --reload` from the repo root (paths are relative).
- Test: `pytest` (one test: `pytest test_main.py::test_ask`). Lint: `ruff check .`
- Coverage: `pytest --cov=. --cov-report=term-missing` (only the real Bedrock
  calls stay uncovered, on purpose).
- Bedrock connection check: `python scripts/bedrock_smoke.py`

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
- **`ThrottlingException` on a first Bedrock call is a quota, not a bug.** New
  accounts can start with inference quotas at 0; check Service Quotas.

## Working agreement

Code, comments and commits in English. One logical change per commit. Ask
before creating, changing or destroying AWS resources.
