<div align="center">

# 📄 docFoge

### *High-Performance PDF to LLM-Ready Markdown & RAG Engine*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyMuPDF4LLM](https://img.shields.io/badge/PyMuPDF4LLM-1.28%2B-ff69b4.svg?style=for-the-badge)](https://github.com/pymupdf/PyMuPDF)
[![Package Manager](https://img.shields.io/badge/uv-managed-58155A.svg?style=for-the-badge&logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<br />

**docFoge** is a high-speed document processing API designed to convert PDF files into clean, sanitized, and structured **LLM-ready Markdown**, complete with **LaTeX math expression conversion**, **embedded inline Base64 graphics**, and **RAG vector database chunking**.

[Key Features](#-key-features) •
[Quick Start](#-quick-start) •
[API Reference](#-api-reference) •
[RAG Integration](#-rag--vector-database-chunks) •
[Architecture](#-project-structure)

</div>

---

## 📌 Overview

Traditional PDF extraction tools often output unstructured plain text, mangle tables, drop inline math equations, or lose image context. **docFoge** addresses these challenges by wrapping PyMuPDF4LLM in an async FastAPI service enhanced with custom mathematical & structural filtering pipelines:

- **Mathematical Expressions**: Converts raw equations, symbols, matrices, and fractions into standardized LaTeX (`$...$` and `$$...$$`).
- **Inline Image Processing**: Extracts figures, charts, and embedded graphics, injecting them as Base64 Data URIs (`data:image/png;base64,...`) directly at their original positions.
- **RAG-Ready Page Chunking**: Breaks multi-page PDFs into structured page chunks with zero-indexed page numbers and metadata for instant vector indexing.
- **Clean Structure**: Automatically strips orphan page numbers, redundant header artifacts, and excessive whitespace.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| 🚀 **High Performance** | Powered by PyMuPDF C++ bindings for sub-second document processing. |
| 📐 **Deterministic Math Engine** | Transforms inline & block math into valid LaTeX syntax (`$\alpha + \beta$` / `$$\sum x_i$$`). |
| 🖼️ **Base64 Image Extraction** | Automatically encodes images directly into Markdown output without local file linkage issues. |
| 🧩 **RAG Page Chunking** | Splits content page-by-page into JSON chunks with page metadata for Vector DBs. |
| 🎯 **Selective Page Range** | Parse specific page subsets (e.g. `pages="0,1,4"`). |
| 🌐 **Interactive OpenAPI Docs** | Built-in Swagger UI & ReDoc documentation out of the box. |
| ⚡ **Managed with `uv`** | Ultra-fast environment synchronization and dependency management. |

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.12 or higher
- **uv**: Fast Python package installer (`pip install uv` or via `curl -sSf https://astral.sh/uv/install.sh | sh`)

### Installation & Running

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/docfoge.git
   cd docfoge
   ```

2. **Install & Sync Dependencies**
   ```bash
   uv sync
   ```

3. **Start the Development Server**
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

4. **Access OpenAPI Documentation**
   - **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Reference

### Endpoints Overview

| Endpoint | Method | Description | Content-Type |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Service status check | `application/json` |
| `/api/v1/to-markdown` | `POST` | Convert PDF to JSON Markdown / Page Chunks | `application/json` |
| `/api/v1/to-markdown/raw` | `POST` | Convert PDF directly to raw Markdown text | `text/markdown` |

---

### 1. Health Check
Checks service operational status and version.

```bash
curl -X GET "http://localhost:8000/health"
```

**Response (`200 OK`)**:
```json
{
  "status": "ok",
  "version": "0.2.0"
}
```

---

### 2. Convert PDF to Markdown (JSON)
Converts a PDF document into a structured JSON response containing the full Markdown string and metadata.

```bash
curl -X POST "http://localhost:8000/api/v1/to-markdown" \
  -F "file=@/path/to/document.pdf" \
  -F "write_images=true" \
  -F "image_format=png"
```

**Form Parameters**:
- `file` *(file, required)*: The PDF document to process.
- `page_chunks` *(boolean, default: false)*: Set to `true` to return array of per-page chunks.
- `pages` *(string, optional)*: Comma-separated page indices (0-indexed), e.g. `"0,1,2"`.
- `write_images` *(boolean, default: true)*: Extract inline images and embed as Base64.
- `image_format` *(string, default: "png")*: Format of extracted images (`"png"`, `"jpg"`).

**Response (`200 OK`)**:
```json
{
  "filename": "sample.pdf",
  "total_pages": 3,
  "markdown": "# Document Title\n\nHere is the parsed content with math $\\mathbf{A} x = b$ and embedded graphics...",
  "chunks": null
}
```

---

### 3. Convert PDF to Page Chunks (for RAG)
Generates page-by-page chunks tailored for embedding models and vector stores.

```bash
curl -X POST "http://localhost:8000/api/v1/to-markdown" \
  -F "file=@/path/to/document.pdf" \
  -F "page_chunks=true"
```

**Response (`200 OK`)**:
```json
{
  "filename": "sample.pdf",
  "total_pages": 2,
  "markdown": null,
  "chunks": [
    {
      "page": 0,
      "text": "# Executive Summary\n\nPage 1 detailed overview text...",
      "metadata": {
        "page": 0,
        "file_name": "sample.pdf"
      },
      "images": []
    },
    {
      "page": 1,
      "text": "## Technical Architecture\n\nPage 2 detailed technical notes...",
      "metadata": {
        "page": 1,
        "file_name": "sample.pdf"
      },
      "images": []
    }
  ]
}
```

---

### 4. Direct Raw Markdown Endpoint
Returns the Markdown output directly as raw text (`text/markdown`).

```bash
curl -X POST "http://localhost:8000/api/v1/to-markdown/raw" \
  -F "file=@/path/to/document.pdf" \
  --output result.md
```

---

## 🐍 Python Usage Example

You can integrate docFoge into Python pipelines using `httpx` or `requests`:

```python
import httpx

API_URL = "http://localhost:8000/api/v1/to-markdown"
PDF_FILE_PATH = "sample.pdf"

with open(PDF_FILE_PATH, "rb") as f:
    files = {"file": (PDF_FILE_PATH, f, "application/pdf")}
    data = {
        "page_chunks": "true",
        "write_images": "true"
    }
    response = httpx.post(API_URL, files=files, data=data, timeout=60.0)

result = response.json()
print(f"Total Pages: {result['total_pages']}")
for chunk in result['chunks']:
    print(f"--- Page {chunk['page'] + 1} ---")
    print(chunk['text'][:200]) # First 200 chars
```

---

## 🏗️ Project Structure

```
docfoge/
├── app/
│   ├── api/
│   │   └── router.py                 # FastAPI endpoints & route handlers
│   ├── schemas/
│   │   └── parser.py                 # Pydantic response & chunk schemas
│   ├── services/
│   │   ├── deterministic_math_converter.py  # Math to LaTeX regex & engine
│   │   ├── markdown_engine.py         # PyMuPDF4LLM parsing & Base64 image embedder
│   │   └── structure_filter.py        # Header & document layout sanitizer
│   ├── config.py                     # Service configuration & path settings
│   └── main.py                       # FastAPI application entry point
├── temp/                             # Ephemeral processing directory
├── test_service.py                   # Automated integration test suite
├── pyproject.toml                    # UV / Python dependency management
└── README.md                         # Documentation
```

---

## 🧪 Testing

Run the built-in test suite to verify the Markdown engine and API endpoints:

```bash
uv run python test_service.py
```

Expected Output:
```text
Engine Test (Full Markdown): PASSED
Engine Test (Chunks): PASSED
API Health Check: PASSED
API /to-markdown Endpoint: PASSED
API /to-markdown/raw Endpoint: PASSED

ALL VERIFICATION TESTS PASSED SUCCESSFULLY!
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
