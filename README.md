# CyberSift

An LLM-based security data extraction chatbot. Ingests files in any format
and extracts security-relevant data (IOCs, threat/pentest data, PII,
credentials/secrets, network/infrastructure artifacts, malware/forensic
artifacts) using a fully LLM-based pipeline -- no regex/hybrid extraction.

## Structure

```text
backend/            FastAPI backend (deployed on Vercel)
  app/core/         pipeline, chunker, verifier, LLM client
  app/core/prompts.py   every system prompt in one place
  app/core/tools.py     tools the chat agent can call
  app/core/agent.py     the tool-use chat loop behind /api/chat
  app/extractors/   one extractor per category (ioc, pii, creds, network, forensic)
  app/loaders/      one loader per file format (txt, pdf, docx, csv)
  app/schemas/      Pydantic models
frontend/           Streamlit chat UI
api/index.py        Vercel serverless entrypoint (re-exports the FastAPI app)
```

## Running

Backend (hosted at <https://cybersift.vercel.app>, or locally):

```bash
cd backend
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-ant-... uvicorn app.main:app --port 8000
```

Frontend:

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/streamlit_app.py                       # uses the hosted API
CYBERSIFT_API_URL=http://localhost:8000 streamlit run frontend/streamlit_app.py   # local API
```

## API

- `GET /api/health` -- status, supported formats and categories
- `POST /api/ingest` -- multipart file -> plain text
- `POST /api/extract` -- file and/or text + categories -> verified findings
- `POST /api/chat` -- one turn of the tool-using chat agent (JSON: messages + optional document)

## Stack

- Backend: Python, FastAPI, Anthropic API (Claude Sonnet 5 by default; override with `CYBERSIFT_MODEL`)
- Frontend: Streamlit
- Guardrail: every finding's `original_form` must appear verbatim in the source text or it is discarded
- Corpus memory (Layer 2): every scan's findings are recorded (as HMAC digests only -- no raw
  values leave the server) in Vercel Blob storage; findings come back annotated with novelty
  ("first time seen" vs "seen in N previous scans") and same-entity anomaly findings are merged
