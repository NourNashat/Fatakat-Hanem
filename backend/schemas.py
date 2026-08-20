from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="User question about Parkville guidelines/products")
    debug: bool = Field(False, description="Whether to include full internal debug traces")


class CitationItem(BaseModel):
    chunk_id: str
    document: str
    page: int
    section: str
    product: str


class EvidenceItem(BaseModel):
    chunk_id: str
    document: str
    document_id: str = ""
    page: int
    category: str
    brand: str
    product: str
    section: str
    section_type: str = "general"
    safety_label: str = ""
    score: float = Field(..., description="Cross-encoder rerank relevance score or cosine score")
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    text: str


class ConfidenceGate(BaseModel):
    score: float = 0.0
    allowed: bool = False
    top_rerank_score: Optional[float] = None
    top_rerank_normalized: Optional[float] = None
    margin: Optional[float] = None
    agreement: Optional[float] = None
    reason: Optional[str] = None


class GuardsInfo(BaseModel):
    citation: Optional[Dict[str, Any]] = None
    safety: Optional[Dict[str, Any]] = None
    confidence_gate: Optional[Dict[str, Any]] = None


class TraceInfo(BaseModel):
    latency_ms: float = 0.0
    analysis: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[Dict[str, Any]] = None
    dense_candidates: Optional[int] = None
    sparse_candidates: Optional[int] = None
    fused_candidates: Optional[int] = None
    final_context_chunks: Optional[int] = None


class AskResponse(BaseModel):
    status: str = Field(..., description="'answered', 'insufficient_evidence', 'out_of_scope', or 'error'")
    answer: str
    evidence_summary: str = ""
    citations: List[CitationItem] = Field(default_factory=list)
    confidence: str = Field(..., description="'high', 'medium', 'low', or 'insufficient'")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    suggested_next_action: str = ""
    trace: Optional[TraceInfo] = None
    guards: Optional[GuardsInfo] = None


class ProductInfo(BaseModel):
    product: str
    brand: str
    category: str
    chunk_count: int
    safety_label: str
    sections: List[str]


class CatalogResponse(BaseModel):
    products: List[ProductInfo]
    brands: List[str]
    categories: List[str]
    total_chunks: int
    sample_questions: List[str]


class HealthResponse(BaseModel):
    status: str
    assistant: str
    chunk_count: int
    collection: str
    embedding_model: str
    reranker_model: str
    llm_model: str
    llm_configured: bool


class HistoryItem(BaseModel):
    ts: str
    question: str
    status: str
    answer: str
    evidence_summary: str
    confidence: str
    citations: List[CitationItem] = Field(default_factory=list)
