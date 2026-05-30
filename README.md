# AgentForgeOps

![AgentForgeOps CI](https://img.shields.io/github/actions/workflow/status/mikegyim/agentforgeops/evals.yml?branch=main&label=AgentForgeOps%20CI)
![python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-Qdrant-DC382D)
![kubernetes](https://img.shields.io/badge/kubernetes-ready-326CE5?logo=kubernetes&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-yellow)

**AI-Native DevOps & Software Engineering Platform.**
Author: **Michael Opoku-Gyimah** · GitHub: [@mikegyim](https://github.com/mikegyim)

RAG over your team's docs and code, a fleet of specialized agents for code review, test generation, deployment validation, incident triage, and docs, a multi-agent orchestrator, and end-to-end CI/CD wiring.

> A full-stack AI engineering platform that provides centralized team context, retrieval-augmented generation, multi-agent workflows, automated pull request review, test generation, deployment validation, and AI-assisted incident triage for Kubernetes and cloud infrastructure teams.

---

## What's inside

- **FastAPI backend** with REST endpoints for chat, RAG search, upload+index, agents, orchestration, and GitHub webhooks.
- **Five agents** — Code Review, Test Generation, Deployment Validation, Incident Triage, Documentation — each grounded with RAG where it helps.
- **LangGraph-style orchestrator** that threads state between agents to express multi-step workflows declaratively.
- **Vector store abstraction** — Qdrant by default, in-memory fallback so the stack runs without infra. Optional Chroma path is reserved.
- **LLM abstraction** — OpenAI / Anthropic / Bedrock-compatible, with a deterministic mock so the platform boots without keys.
- **Next.js 14 frontend** with pages for chat, agents, upload, search, incidents, and PR review.
- **Docker Compose** dev stack (Postgres, Qdrant, Prometheus, Grafana, backend, frontend).
- **Kubernetes manifests** (Deployment, Service, StatefulSet for Qdrant, Ingress).
- **Terraform scaffold** for VPC + encrypted S3 uploads bucket on AWS.
- **GitHub Actions** workflow that posts AI PR reviews back to the pull request.
- **Sample data** — runbooks, logs, and Kubernetes manifests for end-to-end demos.

## Architecture

```
                 ┌─────────────────────────────────────────────┐
                 │                Next.js frontend             │
                 │  /chat  /agents  /upload  /search /incidents│
                 └───────────────┬─────────────────────────────┘
                                 │ /api/*
                                 ▼
                 ┌─────────────────────────────────────────────┐
                 │                FastAPI backend              │
                 │ ┌───────────┐ ┌──────────────┐ ┌──────────┐ │
                 │ │  RAG      │ │  Agents      │ │ Webhook  │ │
                 │ │  indexer  │ │  orchestrator│ │ /github  │ │
                 │ └─────┬─────┘ └──────┬───────┘ └────┬─────┘ │
                 └───────┼──────────────┼──────────────┼───────┘
                         ▼              ▼              ▼
                  ┌────────────┐  ┌──────────┐  ┌──────────────┐
                  │  Qdrant    │  │   LLM    │  │   GitHub     │
                  │  vectors   │  │  client  │  │   API        │
                  └────────────┘  └──────────┘  └──────────────┘
                         ▲
                         │
                  ┌────────────┐
                  │  Postgres  │  app metadata, run history
                  └────────────┘
```

## Quick start (Docker)

```bash
cd infra
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Qdrant: http://localhost:6333
- Grafana: http://localhost:3001 (admin / admin)

The stack boots without any API keys — agents and chat will use the deterministic mock LLM. Set `LLM_PROVIDER=anthropic` (or `openai`) and the corresponding key in `backend/.env.example` to use a real model.

## Local dev (without Docker)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Indexing your team's context

Use the **/upload** page or POST files directly:

```bash
curl -F 'files=@sample-data/runbooks/checkout-503-saturation.md' \
     -F 'files=@sample-data/runbooks/service-ownership.md' \
     http://localhost:8000/api/upload
```

Then ask a grounded question:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what do I do if checkout returns 503?"}'
```

## Running agents

```bash
# Code review (e.g. from a CI step)
curl -X POST http://localhost:8000/api/agents/code-review \
  -H 'Content-Type: application/json' \
  -d '{"diff": "diff --git a/x.py b/x.py\n+def add(a,b): return a+b", "files":[{"filename":"x.py"}]}'

# Deployment validation
curl -X POST http://localhost:8000/api/agents/deploy-validator \
  -H 'Content-Type: application/json' \
  -d @<(jq -n '{manifests: [{path: "bad.yaml", content: "kind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - image: foo:latest\n        securityContext:\n          privileged: true\n"}]}')

# Incident triage
curl -X POST http://localhost:8000/api/agents/incident-triage \
  -H 'Content-Type: application/json' \
  -d "$(jq -Rs '{logs: .,service:"checkout"}' < sample-data/logs/checkout-incident-001.log)"
```

## Multi-agent orchestration

The orchestrator runs a list of nodes and threads state between them. Example:
review the diff, then synthesize tests from the same diff:

```json
{
  "workflow": [
    {"agent": "code-review", "as": "review", "input": {"diff": "...", "files": []}},
    {"agent": "test-gen",    "as": "tests",  "input": {"code": "...", "language": "python"}}
  ],
  "input": {}
}
```

POST that to `/api/agents/orchestrate`.

## GitHub PR review

Two integration modes:

1. **GitHub Actions** (`github-actions/ai-pr-review.yml`) — copy into `.github/workflows/` of any repo. Set `AGENTFORGE_URL` and `AGENTFORGE_TOKEN` secrets. The workflow posts a comment with the agent's review on every PR.
2. **Webhook** (`/api/webhooks/github`) — point a GitHub webhook at your AgentForgeOps deployment. Set `GITHUB_WEBHOOK_SECRET` and `GITHUB_TOKEN`.

## Tech stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async), Pydantic v2
- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind
- **Vector DB:** Qdrant (default), in-memory fallback (Chroma path reserved)
- **LLM:** OpenAI / Anthropic / Bedrock-compatible client (mock by default)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`) with a deterministic hash fallback
- **Infra:** Docker Compose, Kubernetes manifests, Terraform (AWS)
- **Observability:** Prometheus + Grafana (compose), mocked metrics for triage demos
- **CI/CD:** GitHub Actions

## Repo layout

```
agentforgeops/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers
│   │   ├── agents/         # Code review, test gen, deploy validator, triage, docs, orchestrator
│   │   ├── rag/            # Embeddings, vector store, indexer, retriever
│   │   ├── integrations/   # LLM, GitHub, Prometheus (mock)
│   │   ├── models/         # ORM + Pydantic schemas
│   │   └── main.py
│   ├── tests/
│   └── Dockerfile
├── frontend/               # Next.js app
├── infra/
│   ├── docker-compose.yml
│   ├── kubernetes/
│   └── terraform/
├── .github/workflows/
│   ├── ai-pr-review.yml
│   └── evals.yml
├── github-actions/        # copies kept for documentation
│   ├── ai-pr-review.yml
│   └── evals.yml
└── sample-data/
    ├── runbooks/
    ├── logs/
    └── k8s-manifests/
```

## Tests

```bash
cd backend
pytest -q
```

The smoke tests exercise the agents and RAG round-trip with the in-memory store + mock LLM — no external services required.

## Evals

A small evaluation harness ships in `evals/`. It runs labeled examples
through each agent and reports pass-rate + per-example scores.

```bash
cd backend
PYTHONPATH=. python ../evals/run.py
```

Add new cases by dropping JSON files into `evals/cases/<agent>/`. Each case
declares its `assertions` — substrings, regexes, or risk levels the agent's
output must match. See `evals/README.md` for the schema.

## License

MIT — see `LICENSE`.

## Author

Michael Opoku-Gyimah — [@mikegyim](https://github.com/mikegyim)
