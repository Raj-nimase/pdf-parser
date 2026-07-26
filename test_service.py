import fitz
from fastapi.testclient import TestClient
from app.main import app
from app.services.markdown_engine import convert_pdf_bytes_to_markdown

def create_sample_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello PyMuPDF4LLM!", fontsize=24)
    page.insert_text((50, 100), "This is a test document generated for verifying the FastAPI service.", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_engine():
    pdf_bytes = create_sample_pdf_bytes()
    
    # Test continuous markdown
    res_full = convert_pdf_bytes_to_markdown(pdf_bytes, filename="test.pdf", page_chunks=False)
    assert res_full["total_pages"] == 1
    assert "Hello PyMuPDF4LLM!" in res_full["markdown"]
    print("Engine Test (Full Markdown): PASSED")

    # Test chunked markdown
    res_chunks = convert_pdf_bytes_to_markdown(pdf_bytes, filename="test.pdf", page_chunks=True)
    assert len(res_chunks["chunks"]) == 1
    assert "Hello PyMuPDF4LLM!" in res_chunks["chunks"][0]["text"]
    print("Engine Test (Chunks): PASSED")

def test_api():
    client = TestClient(app)
    
    # Health test
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("API Health Check: PASSED")

    # Upload PDF test
    pdf_bytes = create_sample_pdf_bytes()
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    
    response = client.post("/api/v1/to-markdown", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert "Hello PyMuPDF4LLM!" in data["markdown"]
    print("API /to-markdown Endpoint: PASSED")

    # Raw Markdown endpoint test
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/v1/to-markdown/raw", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "Hello PyMuPDF4LLM!" in response.text
    print("API /to-markdown/raw Endpoint: PASSED")

if __name__ == "__main__":
    test_engine()
    test_api()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
