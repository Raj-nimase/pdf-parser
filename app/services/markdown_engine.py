import re
import os
import base64
import tempfile
from typing import Any, Dict, List, Optional
import fitz
import pymupdf4llm
from app.services.structure_filter import process_markdown_structure
from app.services.deterministic_math_converter import DeterministicMathConverter

def log(msg: str):
    print(f"[MarkdownEngine] {msg}", flush=True)

def sanitize_and_convert_math(raw_markdown: str) -> str:
    """
    Applies deterministic math conversion, heading/list structure filtering,
    and general markdown sanitization.
    """
    if not raw_markdown:
        return ""
    
    # Step 1: Structural Filter for Headings, Subheadings & Lists
    structured_markdown = process_markdown_structure(raw_markdown)

    # Step 2: Deterministic Math to LaTeX conversion
    converter = DeterministicMathConverter()
    math_converted = converter.convert_markdown(structured_markdown)

    # Step 3: General Markdown Sanitization
    # Remove orphan page number lines (standalone numbers surrounded by empty lines)
    sanitized = re.sub(r"\n\s*\n\d+\s*\n\s*\n", "\n\n", math_converted)
    
    # Reduce 3+ consecutive newlines to double newlines
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    
    return sanitized.strip()

def embed_images_as_base64(markdown_text: str, tmpdir: str) -> str:
    """
    Replaces Markdown image file paths (e.g. ![](tmp/img.png)) with inline Base64 Data URIs.
    """
    if not markdown_text:
        return ""
    
    def replace_match(match):
        alt = match.group(1)
        img_path = match.group(2)
        target_path = img_path if os.path.isabs(img_path) else os.path.join(tmpdir, img_path)
        if os.path.exists(target_path):
            try:
                with open(target_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                ext = os.path.splitext(target_path)[1].lstrip(".").lower() or "png"
                return f"![{alt}](data:image/{ext};base64,{b64})"
            except Exception as e:
                log(f"Failed to encode image {target_path}: {e}")
        return match.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_match, markdown_text)

def extract_rich_base_markdown(
    doc: fitz.Document,
    pages: Optional[List[int]] = None,
    page_chunks: bool = False,
    write_images: bool = True,
    image_format: str = "png",
    image_path: Optional[str] = None
) -> Any:
    """
    Extracts 100% of PDF content (including all text, hidden/transparent text, tags, tables, and images)
    using PyMuPDF4LLM without stripping or omitting anything.
    """
    target_pages = pages if pages is not None else list(range(len(doc)))
    kwargs = {
        "pages": target_pages,
        "page_chunks": page_chunks,
        "write_images": write_images,
        "image_format": image_format,
        "ignore_alpha": False,
        "force_text": True
    }
    if write_images and image_path:
        kwargs["image_path"] = image_path
    return pymupdf4llm.to_markdown(doc, **kwargs)

def convert_pdf_bytes_to_markdown(
    pdf_bytes: bytes,
    filename: str,
    pages: Optional[List[int]] = None,
    page_chunks: bool = False,
    write_images: bool = True,
    image_format: str = "png",
    sanitize_math: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Converts PDF bytes directly into complete Markdown containing all PDF content,
    extracting images and embedding them as Base64 Data URIs at their exact positions,
    with deterministic math conversion and markdown sanitization applied.
    """
    log(f"Starting conversion for file: {filename} ({len(pdf_bytes)} bytes)")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    log(f"Opened PDF document. Total pages: {total_pages}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = extract_rich_base_markdown(
            doc,
            pages=pages,
            page_chunks=page_chunks,
            write_images=write_images,
            image_format=image_format,
            image_path=tmpdir if write_images else None
        )
        doc.close()
        log(f"Extracted base markdown for {filename}. Applying image embedding, math conversion & sanitization...")

        if page_chunks and isinstance(result, list):
            chunks = []
            for i, chunk in enumerate(result):
                metadata = chunk.get("metadata", {})
                page_num = metadata.get("page", i)
                raw_text = chunk.get("text", "")
                clean_text = sanitize_and_convert_math(raw_text) if sanitize_math else raw_text
                text_with_images = embed_images_as_base64(clean_text, tmpdir) if write_images else clean_text
                chunks.append({
                    "page": page_num,
                    "text": text_with_images,
                    "metadata": metadata,
                    "images": chunk.get("images", [])
                })
            return {
                "filename": filename,
                "total_pages": total_pages,
                "markdown": None,
                "chunks": chunks
            }
        else:
            raw_md = str(result) if result is not None else ""
            clean_md = sanitize_and_convert_math(raw_md) if sanitize_math else raw_md
            final_md = embed_images_as_base64(clean_md, tmpdir) if write_images else clean_md
            log(f"Completed processing & sanitization for {filename} successfully.")
            return {
                "filename": filename,
                "total_pages": total_pages,
                "markdown": final_md,
                "chunks": None
            }

async def convert_pdf_bytes_to_markdown_async(
    pdf_bytes: bytes,
    filename: str,
    pages: Optional[List[int]] = None,
    page_chunks: bool = False,
    write_images: bool = True,
    image_format: str = "png",
    sanitize_math: bool = True,
    **kwargs
) -> Dict[str, Any]:
    return convert_pdf_bytes_to_markdown(
        pdf_bytes=pdf_bytes,
        filename=filename,
        pages=pages,
        page_chunks=page_chunks,
        write_images=write_images,
        image_format=image_format,
        sanitize_math=sanitize_math,
        **kwargs
    )

