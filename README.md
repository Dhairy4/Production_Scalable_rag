# Enterprise Agentic RAG

A FastAPI service that answers technical questions from a private document collection. It ingests local PDF, HTML, text, Word, and PowerPoint files into Qdrant, then uses a LangGraph workflow to plan, retrieve, rerank, and generate an answer.

## What it does

- Parses documents in [`DATA/`](DATA/) and splits them into 1,500-character chunks.
- Creates embeddings with Gemini, with a local Sentence Transformers fallback.
- Stores and searches vectors in Qdrant.
- Uses FlashRank to rerank the most relevant retrieved chunks.
- Uses LangGraph with per-thread conversation memory to choose between a conversational response and document retrieval.
- Generates responses through Portkey with Groq models and exposes a FastAPI API.
- Adds observability with Logfire.

## Architecture

```text
Documents → parser → chunker → embeddings → Qdrant
                                         ↓
Client → FastAPI → LangGraph planner → retriever → FlashRank → Portkey/Groq → response
```

## Project layout

```text
app/
├── agents/                 # LangGraph state, routing, and response nodes
├── gateway/                # Portkey client configuration
├── ingestion/              # Local parsers, chunking, and Qdrant indexing
├── services/retrieval/     # Embeddings, Qdrant search, and reranking
├── config.py               # Environment-backed settings
└── main.py                 # FastAPI application
DATA/
├── true_data/              # Curated source documents
└── noisy_data/             # Additional/noisy source documents
```

## Requirements

- Python 3.13 or newer
- A Qdrant instance (cloud or self-hosted)
- API keys for Gemini, Groq, and Portkey
- Optional: a Logfire token for tracing

## Setup

Clone the repository and create a virtual environment:

```bash
git clone <your-repository-url>
cd Productioh_RAG_1_Krish_naik
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Alternatively, this repository includes `pyproject.toml` and `uv.lock`, so you can use `uv sync` if you use uv.

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=https://your-qdrant-instance
QDRANT_API_KEY=your_qdrant_api_key

# Needed by the Portkey-backed response generator
PORTKEY_API_KEY=your_portkey_api_key
GROQ_SLUG=your_portkey_primary_groq_provider_slug
GROQ_SLUG_2=your_portkey_fallback_groq_provider_slug

# Optional observability
LOGFIRE_TOKEN=your_logfire_token
```

The default Qdrant collection name is `enterprise_rag`; change it in `app/config.py` if required. Never commit `.env`—it is already ignored by Git.

## Ingest documents

Place documents under `DATA/` (or point the command at another directory), then build the vector collection:

```bash
python -m app.ingestion.processor DATA --wipe
```

`--wipe` deletes and recreates the configured Qdrant collection before indexing. Omit it to add documents to an existing collection:

```bash
python -m app.ingestion.processor DATA/true_data true
```

Supported formats are PDF, HTML, TXT, DOCX, and PPTX. Parsed chunk metadata is written locally to `processed_data/` during ingestion.

## Run the API

Start the service from the repository root:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open the interactive API documentation at <http://127.0.0.1:8000/docs>.

### Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Health-style welcome response |
| `GET` | `/graph` | PNG diagram of the LangGraph workflow |
| `POST` | `/query` | Run the RAG workflow |

Example query:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"q":"How does Kubernetes autoscaling work?","thread_id":"demo-user"}'
```

Example response shape:

```json
{
  "question": "How does Kubernetes autoscaling work?",
  "answer": "...",
  "thought_process": ["Intent: Technical", "Context Retrieved"],
  "status": "Response generated.",
  "sources": ["CONTENT: ..."]
}
```

## Notes for contributors

- Run commands from the repository root so Python can resolve the `app` package.
- The first semantic-reranking request may download/load FlashRank's local model.
- Ingestion is an external-state operation: use `--wipe` only when you intend to replace the Qdrant collection.
- `DATA/` currently contains approximately 100 MB of example material. Keep large additions out of normal Git history where appropriate; Git LFS is a good option for large binary datasets.

