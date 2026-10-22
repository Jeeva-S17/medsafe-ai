import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure runtime directories exist
for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR, UPLOADS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DATABASE_URL = str(DATA_DIR / "medisafe.db")

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
FDA_API_KEY = os.getenv("FDA_API_KEY", "")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = True
