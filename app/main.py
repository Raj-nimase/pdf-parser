from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import APP_TITLE, APP_VERSION
from app.schemas.parser import HealthResponse
from app.api.router import router as api_router

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="FastAPI service powered by pymupdf4llm for converting PDF documents into LLM-ready Markdown."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="ok", version=APP_VERSION)
