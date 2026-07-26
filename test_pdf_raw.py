import sys
from app.services.markdown_engine import convert_pdf_bytes_to_markdown

sys.stdout.reconfigure(encoding='utf-8')

with open("../NIPS-2017-attention-is-all-you-need-Paper.pdf", "rb") as f:
    pdf_bytes = f.read()

result = convert_pdf_bytes_to_markdown(pdf_bytes=pdf_bytes, filename="NIPS.pdf")
markdown = result["markdown"]

idx = markdown.find("Scaled Dot-Product Attention")
if idx != -1:
    print("--- EXTRACTED & CONVERTED SECTION 3.2.1 ---")
    print(markdown[idx:idx+1200])

