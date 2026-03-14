---
title: Ask the Guru
emoji: 🧘
colorFrom: yellow
colorTo: blue
sdk: docker
app_port: 7860
---

# RAG Q&A Assistant

A retrieval-augmented question-answering (RAG) system built on curated YouTube subtitle transcripts.

The project provides:
- A FastAPI backend (`/ask`) for question answering.
- A static frontend served by FastAPI.
- A data pipeline to download subtitles, preprocess text, embed transcripts, and retrieve relevant context.
- A CLI flow for local/offline querying.

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Run with Docker](#run-with-docker)
- [API Reference](#api-reference)
- [Data Pipeline](#data-pipeline)
- [Deployment](#deployment)
- [Operational Notes](#operational-notes)
- [Troubleshooting](#troubleshooting)

## Architecture

1. User asks a question from the UI or directly through `POST /ask`.
2. Query is embedded using `all-MiniLM-L6-v2`.
3. Top-K transcript chunks are retrieved from the FAISS index.
4. Retrieved context is token-trimmed (`MAX_CONTEXT_TOKENS`).
5. Groq chat completion API generates the final answer using a domain-aligned system prompt.

Core runtime flow:
- `app.py` loads `data/file_paths.pkl` and `data/transcripts.pkl` at startup.
- `api/retrieve_context.py` handles vector retrieval.
- `api/generate_response.py` handles LLM generation.
- `frontend/index.html` is mounted and served from `/`.

## Project Structure

```text
.
├── api/
│   ├── embed_transcripts.py
│   ├── generate_response.py
│   └── retrieve_context.py
├── data/
│   ├── subtitles_vtt/
│   ├── transcripts_txt/
│   ├── file_paths.pkl
│   ├── transcript_index.faiss
│   └── transcripts.pkl
├── frontend/
│   ├── assets/images/
│   └── index.html
├── outputs/
│   ├── generated_response.txt
│   └── retrieved_transcripts.txt
├── utils/
│   ├── download_vtt.py
│   ├── preprocess.py
│   ├── token.py
│   └── vtt_to_txt.py
├── app.py
├── config.py
├── main.py
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Tech Stack

- Python 3.11+ (project metadata), FastAPI, Uvicorn
- FAISS (`faiss-cpu`) for vector search
- Sentence Transformers (`all-MiniLM-L6-v2`) for embeddings
- Groq API for response generation (`llama-3.1-8b-instant`)
- Static HTML/CSS/JS frontend

## Prerequisites

- Python 3.11 or later
- `pip` or `uv`
- `yt-dlp` (required only when running subtitle download stage)
- A valid `GROQ_API_KEY`

## Configuration

Environment variables read by the app:

- `GROQ_API_KEY`: required for answer generation
- `GITHUB_TOKEN`: optional; present in config but not required for runtime flow
- `HF_API_TOKEN`: optional; present in config but not required for runtime flow

Important runtime paths are defined in `config.py`, including:
- `data/file_paths.pkl`
- `data/transcripts.pkl`
- `data/transcript_index.faiss`
- `outputs/generated_response.txt`

## Quick Start

### 1. Install dependencies

Using `uv`:

```bash
uv sync
```

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Set environment variable

```bash
export GROQ_API_KEY="your_groq_api_key"
```

### 3. Start API + frontend

```bash
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

Open `http://localhost:7860`.

## Run with Docker

Build:

```bash
docker build -t rag-qa-assistant .
```

Run:

```bash
docker run --rm -p 7860:7860 -e GROQ_API_KEY="your_groq_api_key" rag-qa-assistant
```

## API Reference

### `POST /ask`

Request body:

```json
{
  "query": "How do I deal with fear?"
}
```

Success response (`200`):

```json
{
  "answer": "..."
}
```

Error responses:
- `400`: missing or empty `query`
- `404`: no relevant transcripts retrieved
- `500`: internal error

Example:

```bash
curl -X POST "http://localhost:7860/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is desire?"}'
```

## Data Pipeline

`main.py` includes stages for data preparation and querying.

Pipeline stages:
1. Download subtitles from configured channels (`utils/download_vtt.py`)
2. Convert `.vtt` to cleaned `.txt` (`utils/vtt_to_txt.py`, `utils/preprocess.py`)
3. Load and persist transcript corpus (`data/*.pkl`)
4. Create FAISS index (`api/embed_transcripts.py`)
5. Retrieve context + generate response

Current state of `main.py`:
- Download/preprocess/embed stages are present but commented out in `main()`.
- Default execution expects prebuilt artifacts in `data/`.

Run CLI query flow:

```bash
python main.py
```

## Deployment

This repository is configured for Hugging Face Spaces (Docker SDK):
- README front matter defines Space metadata.
- `.github/workflows/main.yml` syncs `main` branch to HF Space.
- `.github/workflows/space-keepalive.yml` pings the deployed Space every 12 hours.

## Operational Notes

- Data artifacts are currently committed to the repository (`data/*.pkl`, `.faiss`).
- CORS in `app.py` is permissive (`allow_origins=["*"]`) and suitable for dev/demo, not strict production hardening.
- `frontend/index.html` references `assets/images/hero-background.jpg`, but this file is not present in `frontend/assets/images/`.
- `api/embed_transcripts.py` currently treats `transcript_index` as a directory path (`mkdir`) though it is configured as a file path; this affects index regeneration workflows.

## Troubleshooting

- `Error: AI client not configured.`
  - Ensure `GROQ_API_KEY` is set in the shell/container before startup.

- `No relevant transcripts found` (`404` from `/ask`)
  - Check that `data/transcript_index.faiss`, `data/file_paths.pkl`, and `data/transcripts.pkl` exist and are compatible.

- API starts but UI looks incomplete
  - Verify static assets under `frontend/assets/images/`.

- Subtitle download stage fails
  - Install `yt-dlp` and verify network access and YouTube rate limits.
