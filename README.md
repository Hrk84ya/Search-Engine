# 🔍 Nexus Search — Smart Semantic Search Engine with RAG

Production-grade semantic search system for internal documents using embeddings, pgvector, and Retrieval-Augmented Generation.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    React      │────▶│   FastAPI     │────▶│  PostgreSQL   │
│   Frontend    │     │   REST API    │     │  + pgvector   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
              ┌─────▼─────┐ ┌─────▼─────┐
              │ Embedding  │ │   RAG      │
              │ Service    │ │ Generator  │
              │ (MiniLM)   │ │(Flan-T5-L) │
              └───────────┘ └───────────┘
                    │              │
              ┌─────▼─────┐ ┌─────▼─────┐
              │  Redis     │ │  MLflow    │
              │  Cache     │ │  Tracking  │
              └───────────┘ └───────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI (async) |
| Database | PostgreSQL + pgvector |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | google/flan-t5-large |
| Experiment Tracking | MLflow |
| Cache | Redis |
| Auth | JWT (python-jose + passlib) |
| Frontend | React + Vite |
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes |

## Quick Start

### Prerequisites
- Python 3.11+ (tested on 3.13)
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### 1. Start Infrastructure

```bash
docker compose -f infra/docker/docker-compose.yml up -d postgres redis mlflow
```

This starts:
- PostgreSQL 16 with pgvector extension on port 5432
- Redis 7 on port 6379
- MLflow tracking server on port 5000

### 2. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

First request will download ML models (~90MB for embeddings, ~3GB for flan-t5-large). Subsequent starts use cached models.

### 4. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:3000 with API proxy to port 8000.

### 5. Index Sample Documents

```bash
curl -X POST http://localhost:8000/upload -F "file=@data/sample_ml_basics.txt"
curl -X POST http://localhost:8000/upload -F "file=@data/sample_kubernetes.txt"
```

### 6. Full Docker Deployment

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

## API Reference

### Health Check
```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"1.0.0","database":"connected"}
```

### Get Auth Token
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
# {"access_token":"eyJ...","token_type":"bearer"}
```

### Upload a Document
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@data/sample_ml_basics.txt"
# {"document_id":"...","filename":"sample_ml_basics.txt","chunk_count":3,"message":"Document indexed successfully with 3 chunks."}
```

Supported formats: PDF, TXT, DOCX.

### Semantic Search
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "top_k": 3}'
```

Response includes:
- `generated_answer` — AI-generated answer grounded in retrieved context
- `retrieved_chunks` — top-k source chunks with similarity scores
- `latency_ms` — end-to-end latency
- `model_info` — embedding model, LLM, and top-k used

## Kubernetes Deployment

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/redis.yaml
kubectl apply -f infra/k8s/app.yaml
```

Includes Ingress config at `search.local`. Update the host or add your domain.

## Project Structure

```
project-root/
├── app/
│   ├── api/            # FastAPI route handlers (health, auth, upload, search)
│   ├── core/           # Config, logging, JWT auth
│   ├── services/       # Ingestion, retrieval, chunking, caching, MLflow tracking
│   ├── models/         # SQLAlchemy models + Pydantic schemas
│   └── db/             # Async session + DB initialization
├── ml/
│   ├── embedding/      # sentence-transformers embedding service
│   └── rag/            # Flan-T5 answer generation with prompt engineering
├── infra/
│   ├── docker/         # Dockerfile + docker-compose
│   └── k8s/            # Namespace, Postgres, Redis, App + Ingress
├── frontend/           # React (Vite) — premium warm-tone UI
│   └── src/components/ # Header, SearchBar, ResultsPanel, UploadModal, HealthBadge
├── data/               # Sample documents for testing
├── tests/              # Unit tests (chunker, parser, API)
├── requirements.txt
├── .env.example        # Environment variable template
└── README.md
```

## Configuration

All settings are in `.env` (or environment variables):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async DB connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis cache URL |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HF embedding model |
| `LLM_MODEL` | `google/flan-t5-large` | HF text generation model |
| `CHUNK_SIZE` | `200` | Words per chunk |
| `CHUNK_OVERLAP` | `30` | Overlapping words between chunks |
| `TOP_K` | `5` | Default retrieval count |
| `SECRET_KEY` | — | JWT signing key (change in production) |

## Running Tests

```bash
pip install pytest pytest-asyncio anyio httpx
pytest tests/ -v
```

## Performance Notes

- First query is slow (~20s on CPU) due to model loading. Subsequent queries are 2-5s.
- With GPU, inference drops to under 1s.
- Redis caching returns repeated queries instantly (300s TTL).
- Chunk deduplication prevents duplicate results from re-uploaded documents.

## MLflow Dashboard

Visit http://localhost:5000 after starting MLflow to view:
- Search query metrics (latency, result count, top similarity score)
- Document ingestion tracking (chunk count, model params)
