import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import config
from backend.schemas import (
    AskRequest,
    AskResponse,
    CatalogResponse,
    HealthResponse,
    HistoryItem,
)
from backend.rag_engine import rag_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Parkville RAG FastAPI server...")
    try:
        rag_engine.initialize()
    except Exception as e:
        logger.error(f"Error during RAG engine startup: {e}")
    yield
    logger.info("Shutting down Parkville RAG server...")


app = FastAPI(
    title="Parkville Skin & Hair Care Expert API",
    description="Evidence-grounded RAG API for Parkville skincare, haircare, and pregnancy-safety guidelines.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def get_health():
    """Health check endpoint returning system status and indexed collection statistics."""
    try:
        return rag_engine.get_health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="degraded",
            assistant=config.ASSISTANT_NAME,
            chunk_count=0,
            collection=config.CHROMA_COLLECTION,
            embedding_model=config.EMBEDDING_MODEL,
            reranker_model=config.RERANKER_MODEL,
            llm_model=config.LLM_MODEL,
            llm_configured=False,
        )


@app.get("/api/manifest", tags=["Knowledge Base"])
def get_manifest():
    """Returns the index manifest detailing the 2 PDF source manuals and chunking configuration."""
    manifest_path = Path(config.INDEX_MANIFEST_PATH)
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "assistant": config.ASSISTANT_NAME,
        "collection": config.CHROMA_COLLECTION,
        "chunk_count": len(rag_engine.chunks),
    }


@app.get("/api/catalog", response_model=CatalogResponse, tags=["Knowledge Base"])
def get_catalog():
    """Returns all indexed products, brands, categories, and sample questions."""
    return rag_engine.get_catalog()


@app.get("/api/history", response_model=list[HistoryItem], tags=["History"])
def get_history(limit: int = 20):
    """Returns recent query interactions from the persistent query log."""
    return rag_engine.get_history(limit=limit)


@app.post("/api/ask", response_model=AskResponse, tags=["RAG"])
def ask_question(req: AskRequest):
    """
    Main RAG question-answering endpoint.
    Retrieves evidence from the 303 chunks, calculates confidence, checks guardrails,
    and returns a citation-grounded response.
    """
    try:
        response = rag_engine.ask(req.question, debug=req.debug)
        return response
    except Exception as e:
        logger.error(f"Unexpected error in /api/ask: {e}", exc_info=True)
        return AskResponse(
            status="error",
            answer="An internal processing error occurred while retrieving evidence. Please try again.",
            evidence_summary=f"Internal error: {str(e)}",
            confidence="insufficient",
            suggested_next_action="Try rephrasing your question or check the server logs.",
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "answer": "A server error occurred. Please try again later.",
            "error_detail": str(exc),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=config.HOST, port=config.PORT, reload=True)
