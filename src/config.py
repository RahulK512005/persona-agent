import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
GENERATION_MODEL = "models/gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY", ""),
    http_options=types.HttpOptions(apiVersion="v1"),
)
