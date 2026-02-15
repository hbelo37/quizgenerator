from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Directories
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "quiz.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# LLM configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface")  # "ollama" or "huggingface"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # e.g. "mistral", "llama3"
HUGGINGFACE_API_URL = os.getenv(
    "HUGGINGFACE_API_URL",
    "https://router.huggingface.co/hf-inference/models",
)
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "HuggingFaceTB/SmolLM3-3B")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")

# Quiz settings
MIN_QUESTIONS = 5
MAX_QUESTIONS = 50
DIFFICULTIES = ["easy", "medium", "hard"]

# Upload constraints
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
