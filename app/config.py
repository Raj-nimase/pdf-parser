import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)
IMAGES_DIR = TEMP_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

APP_TITLE = "PyMuPDF4LLM FastAPI Service"
APP_VERSION = "0.2.0"
