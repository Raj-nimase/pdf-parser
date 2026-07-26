from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Response
from app.schemas.parser import ParsePDFResponse
from app.services.markdown_engine import convert_pdf_bytes_to_markdown_async

router = APIRouter(prefix="/api/v1", tags=["PDF Parser"])

def parse_pages_param(pages_str: Optional[str]) -> Optional[List[int]]:
    if not pages_str:
        return None
    try:
        return [int(p.strip()) for p in pages_str.split(",") if p.strip().isdigit()]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid pages format. Use comma-separated numbers, e.g. '0,1,2'")

@router.post("/to-markdown", response_model=ParsePDFResponse)
async def convert_pdf_to_markdown(
    file: UploadFile = File(...),
    page_chunks: bool = Form(False, description="Whether to break markdown into page chunks with metadata"),
    pages: Optional[str] = Form(None, description="Comma-separated zero-indexed page numbers, e.g., '0,1,2'"),
    write_images: bool = Form(True, description="Extract inline images from the PDF"),
    image_format: str = Form("png", description="Format for extracted images (png, jpg, etc.)")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        pdf_bytes = await file.read()
        parsed_pages = parse_pages_param(pages)
        
        result = await convert_pdf_bytes_to_markdown_async(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
            pages=parsed_pages,
            page_chunks=page_chunks,
            write_images=write_images,
            image_format=image_format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

@router.post("/to-markdown/raw")
async def convert_pdf_to_markdown_raw(
    file: UploadFile = File(...),
    pages: Optional[str] = Form(None, description="Comma-separated page numbers, e.g., '0,1,2'")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        pdf_bytes = await file.read()
        parsed_pages = parse_pages_param(pages)
        
        result = await convert_pdf_bytes_to_markdown_async(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
            pages=parsed_pages,
            page_chunks=False,
            write_images=True
        )
        markdown_text = result.get("markdown") or ""
        return Response(content=markdown_text, media_type="text/markdown")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")
