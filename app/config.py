from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Wczytanie .env z katalogu głównego projektu
load_dotenv(ROOT_DIR / ".env")

# Ścieżki
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
PROCESSED_DIR = STATIC_DIR / "processed"

DB_PATH = BASE_DIR / "logs.db"

# Klucz (jakbyś chciał go gdzieś jawnie użyć)
OPENAI_API_KEY = os.getenv("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")
