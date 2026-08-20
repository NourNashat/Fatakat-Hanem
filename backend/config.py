import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Path configurations
CHROMA_DIR = os.getenv("CHROMA_DIR", str(PROJECT_ROOT))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "parkville_skin_hair_expert")
INDEX_MANIFEST_PATH = os.getenv("INDEX_MANIFEST_PATH", str(PROJECT_ROOT / "index_manifest.json"))
QUERY_LOG_PATH = os.getenv("QUERY_LOG_PATH", str(PROJECT_ROOT / "query_log.jsonl"))

# Assistant & domain configuration
ASSISTANT_NAME = "Parkville Skin & Hair Care Expert"
ALLOWED_CATEGORIES = {"skin_care", "hair_care"}
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "600"))

# Embedding & Reranker models
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2")
RERANK_MAX_LENGTH = int(os.getenv("RERANK_MAX_LENGTH", "384"))

# Hybrid retrieval settings
DENSE_TOP_K = int(os.getenv("DENSE_TOP_K", "20"))
SPARSE_TOP_K = int(os.getenv("SPARSE_TOP_K", "20"))
RRF_K = int(os.getenv("RRF_K", "60"))
RRF_POOL_K = int(os.getenv("RRF_POOL_K", "18"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "5"))

# Confidence thresholds
MIN_RERANK_SCORE = float(os.getenv("MIN_RERANK_SCORE", "0.35"))
MIN_RETRIEVAL_AGREEMENT = float(os.getenv("MIN_RETRIEVAL_AGREEMENT", "0.18"))
MIN_FINAL_CONFIDENCE = float(os.getenv("MIN_FINAL_CONFIDENCE", "0.42"))
CONFIDENCE_MARGIN_BONUS = float(os.getenv("CONFIDENCE_MARGIN_BONUS", "0.10"))

# LLM configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq_openai_compatible")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.05"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
