# PDF Parser Service (PyMuPDF4LLM FastAPI)

High-performance REST API built with **FastAPI** and **PyMuPDF4LLM** for converting PDF files into LLM-ready Markdown, structured page chunks, and extracted inline images. Managed with [`uv`](https://github.com/astral-sh/uv).

## Features

- 🚀 **Fast Markdown Conversion**: Powered by `pymupdf4llm`.
- 🧩 **Page Chunking**: Optional chunking per page with metadata for RAG vector databases.
- 🖼️ **Image Extraction**: Extract embedded images from PDFs.
- ⚡ **Managed with `uv`**: Ultra-fast environment setup and dependency management.

---

## Setup & Running

### 1. Sync Dependencies
```bash
uv sync
```

### 2. Start Dev Server
```bash
uv run uvicorn app.main:app --reload --port 8000
```
Swagger UI documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## API Documentation & Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Convert PDF to Markdown (JSON response)
```bash
curl -X POST "http://localhost:8000/api/v1/to-markdown" \
  -F "file=@/path/to/document.pdf"
```

### Convert PDF to Page Chunks (for RAG / Embeddings)
```bash
curl -X POST "http://localhost:8000/api/v1/to-markdown" \
  -F "file=@/path/to/document.pdf" \
  -F "page_chunks=true"
```

### Direct Raw Markdown Output (`text/markdown`)
```bash
curl -X POST "http://localhost:8000/api/v1/to-markdown/raw" \
  -F "file=@/path/to/document.pdf"
```
