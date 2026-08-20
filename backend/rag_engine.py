import os
import re
import json
import time
import math
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import numpy as np
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend import config
from backend.schemas import (
    AskResponse,
    EvidenceItem,
    CitationItem,
    TraceInfo,
    GuardsInfo,
    CatalogResponse,
    ProductInfo,
    HealthResponse,
    HistoryItem,
)

logger = logging.getLogger("rag_engine")
logging.basicConfig(level=logging.INFO)

# Domain Knowledge Constants
SAFETY_LABELS = [
    "AVOID DURING PREGNANCY",
    "CONSULT A DOCTOR FIRST",
    "SAFE",
]

INTENT_KEYWORDS = {
    "pregnancy_safety": [
        "pregnant", "pregnancy", "expecting", "breastfeeding", "safe during pregnancy",
        "avoid during pregnancy", "doctor first", "pregnancy safety",
    ],
    "ingredients": ["ingredient", "ingredients", "contains", "formula", "inci"],
    "usage": ["how to use", "use it", "apply", "frequency", "how often", "routine"],
    "benefits": ["benefit", "benefits", "helps", "good for", "what does it do"],
    "skin_type": ["skin type", "dry skin", "oily skin", "combination skin", "sensitive skin"],
    "hair_type": ["hair type", "dry hair", "oily scalp", "frizzy hair", "damaged hair"],
    "comparison": ["compare", "comparison", "difference", "versus", "vs"],
}

OUT_OF_SCOPE_PATTERNS = [
    "diagnose", "diagnosis", "what disease do i have", "prescribe", "prescription",
    "what medication should i take", "blood test", "medical diagnosis",
    "dose of", "dosage of", "emergency", "hospital", "doctor for my condition",
]

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["answered", "insufficient_evidence", "out_of_scope"]
        },
        "answer": {"type": "string"},
        "evidence_summary": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "chunk_id": {"type": "string"},
                    "document": {"type": "string"},
                    "page": {"type": "integer"},
                    "section": {"type": "string"},
                    "product": {"type": "string"},
                },
                "required": ["chunk_id", "document", "page", "section", "product"],
            },
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low", "insufficient"]
        },
    },
    "required": ["status", "answer", "evidence_summary", "citations", "confidence"],
}

SYSTEM_PROMPT = """You are the Parkville Skin & Hair Care Expert.

You are a strict, citation-bound RAG assistant.
Your ONLY source of truth is the retrieved context supplied in the user message.

Rules:
1. Never use outside medical, cosmetic, product, or ingredient knowledge.
2. Never invent a product, ingredient, benefit, usage instruction, pregnancy label, brand, or citation.
3. Preserve pregnancy-safety labels EXACTLY when they appear in the context:
   SAFE
   CONSULT A DOCTOR FIRST
   AVOID DURING PREGNANCY
4. Do not infer a pregnancy label from an ingredient unless that classification is explicitly present in the retrieved source.
5. Every substantive answer must be supported by one or more cited chunk_ids.
6. If the context is insufficient, say so explicitly and return status="insufficient_evidence".
7. If the question is outside the supported product-information domain, return status="out_of_scope".
8. Keep answers concise, clear, and professional. Mention uncertainty when the source is incomplete.
9. Return ONLY valid JSON matching the supplied schema. No markdown fences.

You can answer questions about:
- Product names and descriptions
- Ingredients
- Key benefits
- Skin or hair type
- How to use
- Usage frequency
- Product properties
- Sun exposure information
- Pregnancy safety
- Comparisons between products, when the supplied context contains information about both products
"""

SAMPLE_QUESTIONS = [
    "What are the ingredients in Shaan Cleanser?",
    "Is CLARY Leave-In Cream safe during pregnancy?",
    "How should Clary Booster Shot be used?",
    "What is Seropipe Hair Dropper designed to help with?",
    "What are the benefits of Shaan Cica Cream?",
    "Which hair-care products are classified as AVOID DURING PREGNANCY?",
    "What is the pregnancy safety classification of Starville Whitening Cream?",
    "Compare Shaan Cleanser and Starville Whitening Cleanser.",
    "Compare Clary Hair Mask and Seropipe Hair Mask.",
    "What blood tests should be ordered during pregnancy?",
]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9\u0600-\u06FF][a-z0-9\u0600-\u06FF%+.-]*", text.lower())


def embedding_text(metadata: Dict[str, Any], text: str) -> str:
    prefix = " | ".join([
        f"category={metadata.get('category', '')}",
        f"brand={metadata.get('brand', '')}",
        f"product={metadata.get('product', '')}",
        f"section={metadata.get('section', '')}",
    ])
    return f"{prefix}\n{text}"


class RAGEngine:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.chunk_by_id: Dict[str, Dict[str, Any]] = {}
        self.all_products: List[str] = []
        self.all_brands: List[str] = []
        self.bm25: Optional[BM25Okapi] = None
        self.embedding_model = None
        self.reranker = None
        self.chroma_collection = None
        self.llm_client = None
        self.initialized = False
        self._model_loading_thread = None

    def initialize(self):
        if self.initialized:
            return

        logger.info("Initializing Parkville RAG Engine core...")
        self._load_chunks_from_chroma_db()
        self._init_bm25()
        self._init_llm_client()
        self._start_model_loader_thread()
        self.initialized = True
        logger.info(f"RAG Engine successfully initialized with {len(self.chunks)} chunks.")

    def _load_chunks_from_chroma_db(self):
        db_path = Path(config.CHROMA_DIR) / "chroma.sqlite3"
        if not db_path.exists():
            raise FileNotFoundError(f"Chroma SQLite database not found at {db_path}")

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        cur.execute("""
            SELECT id, key, string_value, int_value, float_value
            FROM embedding_metadata;
        """)
        meta_rows = cur.fetchall()

        id_to_meta: Dict[int, Dict[str, Any]] = {}
        for row in meta_rows:
            emb_id, key, str_val, int_val, float_val = row
            if emb_id not in id_to_meta:
                id_to_meta[emb_id] = {}
            val = str_val if str_val is not None else (int_val if int_val is not None else float_val)
            id_to_meta[emb_id][key] = val

        cur.execute("SELECT id, embedding_id FROM embeddings;")
        emb_rows = cur.fetchall()

        self.chunks = []
        self.chunk_by_id = {}

        for emb_id, chunk_id in emb_rows:
            meta = id_to_meta.get(emb_id, {})
            doc_text = meta.pop("chroma:document", "")
            
            metadata = {
                "chunk_id": chunk_id,
                "document_id": str(meta.get("document_id", "")),
                "document_name": str(meta.get("document_name", "")),
                "title": str(meta.get("title", "")),
                "category": str(meta.get("category", "")),
                "page_number": int(meta.get("page_number", 1)) if meta.get("page_number") is not None else 1,
                "product_number": str(meta.get("product_number", "")),
                "product": str(meta.get("product", "")).strip(),
                "brand": str(meta.get("brand", "")).strip(),
                "section": str(meta.get("section", "General")),
                "section_type": str(meta.get("section_type", "overview")),
                "piece_index": int(meta.get("piece_index", 1)) if meta.get("piece_index") is not None else 1,
                "safety_label": str(meta.get("safety_label", "")).strip(),
            }

            chunk_obj = {
                "chunk_id": chunk_id,
                "text": doc_text,
                "metadata": metadata,
            }
            self.chunks.append(chunk_obj)
            self.chunk_by_id[chunk_id] = chunk_obj

        conn.close()

        self.all_products = sorted(
            {c["metadata"]["product"] for c in self.chunks if c["metadata"]["product"]},
            key=len, reverse=True
        )
        self.all_brands = sorted(
            {c["metadata"]["brand"] for c in self.chunks if c["metadata"]["brand"]},
            key=len, reverse=True
        )

        logger.info(f"Loaded {len(self.chunks)} chunks, {len(self.all_products)} products, {len(self.all_brands)} brands.")

    def _init_bm25(self):
        bm25_tokens = [
            tokenize(embedding_text(c["metadata"], c["text"]))
            for c in self.chunks
        ]
        self.bm25 = BM25Okapi(bm25_tokens)

    def _start_model_loader_thread(self):
        def _load():
            try:
                import chromadb
                chroma_client = chromadb.PersistentClient(path=config.CHROMA_DIR)
                self.chroma_collection = chroma_client.get_collection(name=config.CHROMA_COLLECTION)
                logger.info(f"Chroma collection connected ({self.chroma_collection.count()} docs)")
            except Exception as e:
                logger.warning(f"Chroma client connect notice: {e}")

            try:
                from sentence_transformers import SentenceTransformer, CrossEncoder
                logger.info(f"Loading transformer models: {config.EMBEDDING_MODEL}")
                self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
                self.reranker = CrossEncoder(config.RERANKER_MODEL, max_length=config.RERANK_MAX_LENGTH)
                logger.info("SentenceTransformer & CrossEncoder successfully loaded in background.")
            except Exception as e:
                logger.warning(f"Neural models loading notice: {e}")

        self._model_loading_thread = threading.Thread(target=_load, daemon=True)
        self._model_loading_thread.start()

    def _init_llm_client(self):
        api_key = config.GROQ_API_KEY or config.OPENAI_API_KEY or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            base_url = config.LLM_BASE_URL if (config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")) else os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            self.llm_client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=30.0,
                max_retries=0,
            )
            logger.info(f"LLM Client initialized with base URL: {base_url}")
        else:
            logger.info("No external LLM key provided; deterministic grounded extraction enabled.")

    def detect_category(self, query: str) -> Optional[str]:
        q = query.lower()
        skin_terms = ["skin", "face", "cleanser", "cream", "serum", "sunscreen", "toner", "lip balm", "cica", "whitening"]
        hair_terms = ["hair", "shampoo", "conditioner", "scalp", "hair fall", "hair loss", "hair mask", "hair serum", "dropper", "booster shot"]
        s = sum(t in q for t in skin_terms)
        h = sum(t in q for t in hair_terms)
        if s > h and s > 0:
            return "skin_care"
        if h > s and h > 0:
            return "hair_care"
        return None

    def detect_intent(self, query: str) -> str:
        q = query.lower().strip()
        if any(p in q for p in OUT_OF_SCOPE_PATTERNS):
            return "out_of_scope"
        scores = {
            intent: sum(1 for kw in kws if kw in q)
            for intent, kws in INTENT_KEYWORDS.items()
        }
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return "product_lookup"

    def extract_product_hints(self, query: str, fuzzy_threshold: int = 85) -> List[str]:
        q = query.lower()
        exact = [p for p in self.all_products if p.lower() in q]
        if exact:
            return sorted(set(exact), key=len, reverse=True)

        fuzzy_hits = [
            p for p in self.all_products
            if fuzz.partial_ratio(p.lower(), q) >= fuzzy_threshold
        ]
        return sorted(set(fuzzy_hits), key=len, reverse=True)

    def extract_brand_hints(self, query: str) -> List[str]:
        q = query.lower()
        return [b for b in self.all_brands if b.lower() in q]

    def analyze_query(self, query: str) -> Dict[str, Any]:
        return {
            "category": self.detect_category(query),
            "intent": self.detect_intent(query),
            "products": self.extract_product_hints(query),
            "brands": self.extract_brand_hints(query),
        }

    def _metadata_match(self, meta: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        # Avoid aggressive filtering that drops valid cross-category or product hits
        return True

    def dense_search(self, query: str, k: int, analysis: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], float]]:
        if not self.embedding_model or not self.chroma_collection:
            return []

        try:
            q_emb = self.embedding_model.encode([query], normalize_embeddings=True).astype("float32")[0].tolist()
            n_res = min(max(k * 4, k), len(self.chunks))

            raw = self.chroma_collection.query(
                query_embeddings=[q_emb],
                n_results=n_res,
                include=["documents", "metadatas", "distances"],
            )

            hits = []
            for doc_text, meta, distance in zip(raw["documents"][0], raw["metadatas"][0], raw["distances"][0]):
                if not self._metadata_match(meta, analysis):
                    continue
                score = 1.0 - float(distance)
                cid = meta["chunk_id"]
                chunk_doc = self.chunk_by_id.get(cid, {"text": doc_text, "metadata": meta})
                hits.append((cid, chunk_doc, score))
                if len(hits) >= k:
                    break
            return hits
        except Exception:
            return []

    def sparse_search(self, query: str, k: int, analysis: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], float]]:
        if not self.bm25:
            return []

        q_tokens = tokenize(query)
        scores = self.bm25.get_scores(q_tokens)
        ranked_idx = np.argsort(scores)[::-1]

        hits = []
        for idx in ranked_idx:
            c = self.chunks[int(idx)]
            if not self._metadata_match(c["metadata"], analysis):
                continue
            score_val = float(scores[int(idx)])
            if score_val <= 0:
                continue
            hits.append((c["chunk_id"], c, score_val))
            if len(hits) >= k:
                break
        return hits

    def rrf_fusion(self, dense_hits: List[Tuple[str, Dict[str, Any], float]],
                   sparse_hits: List[Tuple[str, Dict[str, Any], float]],
                   rrf_k: int = 60) -> List[Tuple[str, Dict[str, Any], float]]:
        if not dense_hits and not sparse_hits:
            # Fallback if both empty
            return [(c["chunk_id"], c, 1.0) for c in self.chunks[:5]]

        if not dense_hits:
            return [(cid, doc, score) for cid, doc, score in sparse_hits]

        if not sparse_hits:
            return [(cid, doc, score) for cid, doc, score in dense_hits]

        fused_score: Dict[str, float] = {}
        doc_lookup: Dict[str, Dict[str, Any]] = {}

        for ranked_list in [dense_hits, sparse_hits]:
            for rank, (chunk_id, doc, _) in enumerate(ranked_list, start=1):
                fused_score[chunk_id] = fused_score.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
                doc_lookup[chunk_id] = doc

        ordered = sorted(fused_score.items(), key=lambda x: x[1], reverse=True)
        return [(cid, doc_lookup[cid], score) for cid, score in ordered]

    def rerank_results(self, query: str, fused_results: List[Tuple[str, Dict[str, Any], float]],
                       top_n: int, pool_k: int) -> List[Tuple[str, Dict[str, Any], float]]:
        if not fused_results:
            return []

        candidates = fused_results[:pool_k]
        if self.reranker:
            try:
                pairs = [[query, item[1]["text"]] for item in candidates]
                scores = self.reranker.predict(pairs, show_progress_bar=False)
                reranked = []
                for (chunk_id, doc, _), score in zip(candidates, scores):
                    reranked.append((chunk_id, doc, float(score)))
                reranked.sort(key=lambda x: x[2], reverse=True)
                return reranked[:top_n]
            except Exception:
                return candidates[:top_n]
        return candidates[:top_n]

    def hybrid_retrieve(self, query: str) -> Dict[str, Any]:
        analysis = self.analyze_query(query)

        if analysis["intent"] == "out_of_scope":
            return {
                "analysis": analysis,
                "dense": [],
                "sparse": [],
                "fused": [],
                "reranked": [],
            }

        qlow = query.lower()
        is_set_query = (
            analysis["intent"] == "pregnancy_safety"
            and any(term in qlow for term in ["which products", "what products", "list the products"])
        )

        dense_k = 40 if is_set_query else config.DENSE_TOP_K
        sparse_k = 40 if is_set_query else config.SPARSE_TOP_K
        final_k = min(12, len(self.chunks)) if is_set_query else config.FINAL_TOP_K

        dense_hits = self.dense_search(query, dense_k, analysis)
        sparse_hits = self.sparse_search(query, sparse_k, analysis)
        fused = self.rrf_fusion(dense_hits, sparse_hits, rrf_k=config.RRF_K)

        rerank_pool = min(40 if is_set_query else config.RRF_POOL_K, len(fused))
        reranked = self.rerank_results(query, fused, final_k, pool_k=rerank_pool)

        return {
            "analysis": analysis,
            "dense": dense_hits,
            "sparse": sparse_hits,
            "fused": fused,
            "reranked": reranked,
        }

    def compute_confidence(self, retrieval: Dict[str, Any]) -> Dict[str, Any]:
        analysis = retrieval["analysis"]
        reranked = retrieval["reranked"]
        dense_ids = {x[0] for x in retrieval["dense"]}
        sparse_ids = {x[0] for x in retrieval["sparse"]}

        if not reranked:
            return {"score": 0.0, "allowed": False, "reason": "no_retrieval"}

        top_score = float(reranked[0][2])
        second_score = float(reranked[1][2]) if len(reranked) > 1 else top_score - 0.1
        margin = max(0.0, top_score - second_score)

        union = len(dense_ids | sparse_ids) or 1
        intersection = len(dense_ids & sparse_ids)
        agreement = (intersection / union) if (dense_ids and sparse_ids) else 1.0

        exact_product_signal = 1.0 if analysis.get("products") else 0.0

        safety_signal = 0.0
        if analysis["intent"] == "pregnancy_safety":
            safety_hits = [
                x for x in reranked
                if x[1]["metadata"].get("safety_label")
                and x[1]["metadata"].get("section_type") == "pregnancy_safety"
            ]
            safety_signal = 1.0 if safety_hits else 0.0

        rerank_component = 1.0 / (1.0 + math.exp(-top_score)) if (self.reranker and top_score > 0) else 0.95

        score = (
            0.55 * rerank_component
            + 0.20 * agreement
            + 0.10 * min(margin * 2.0, 1.0)
            + 0.10 * exact_product_signal
            + 0.05 * safety_signal
        )

        allowed = (
            rerank_component >= config.MIN_RERANK_SCORE
            and agreement >= config.MIN_RETRIEVAL_AGREEMENT
            and score >= config.MIN_FINAL_CONFIDENCE
        )

        return {
            "score": round(float(score), 4),
            "allowed": bool(allowed),
            "top_rerank_score": round(top_score, 4),
            "top_rerank_normalized": round(rerank_component, 4),
            "margin": round(margin, 4),
            "agreement": round(agreement, 4),
            "reason": "pass" if allowed else "low_confidence",
        }

    def build_context(self, reranked: List[Tuple[str, Dict[str, Any], float]]) -> str:
        blocks = []
        for rank, (chunk_id, doc, score) in enumerate(reranked, 1):
            m = doc["metadata"]
            blocks.append(
                f"[SOURCE {rank}]\n"
                f"chunk_id: {chunk_id}\n"
                f"document: {m['document_name']}\n"
                f"page: {m['page_number']}\n"
                f"category: {m['category']}\n"
                f"brand: {m['brand']}\n"
                f"product: {m['product']}\n"
                f"section: {m['section']}\n"
                f"safety_label: {m['safety_label']}\n"
                f"rerank_score: {score:.4f}\n"
                f"text:\n{doc['text']}\n"
            )
        return "\n\n".join(blocks)

    def extract_json_object(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])

        raise ValueError("No JSON object found in model output.")

    @retry(
        stop=stop_after_attempt(config.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def call_llm(self, messages: List[Dict[str, str]]) -> str:
        if not self.llm_client:
            raise RuntimeError("LLM client not configured.")
        response = self.llm_client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content

    def validate_citations(self, answer: Dict[str, Any], reranked: List[Tuple[str, Dict[str, Any], float]]) -> Dict[str, Any]:
        allowed = {cid: doc["metadata"] for cid, doc, _ in reranked}
        invalid = []

        for c in answer.get("citations", []):
            cid = c.get("chunk_id")
            if cid not in allowed:
                invalid.append(cid)
                continue

            source = allowed[cid]
            if str(c.get("document")) != str(source.get("document_name")):
                invalid.append(cid)
            elif int(c.get("page", 0)) != int(source.get("page_number", 0)):
                invalid.append(cid)
            elif str(c.get("product", "")).strip().lower() != str(source.get("product", "")).strip().lower():
                invalid.append(cid)
            elif str(c.get("section", "")).strip().lower() != str(source.get("section", "")).strip().lower():
                invalid.append(cid)

        return {
            "valid": len(invalid) == 0,
            "invalid_chunk_ids": invalid,
            "citation_count": len(answer.get("citations", [])),
        }

    def validate_safety_label(self, answer: Dict[str, Any], reranked: List[Tuple[str, Dict[str, Any], float]], intent: str) -> Dict[str, Any]:
        if intent != "pregnancy_safety":
            return {"valid": True, "expected_labels": [], "mentioned_labels": []}

        source_labels = {
            x[1]["metadata"].get("safety_label")
            for x in reranked
            if x[1]["metadata"].get("safety_label")
        }

        mentioned = {
            label for label in SAFETY_LABELS
            if label.lower() in answer.get("answer", "").lower()
        }

        invalid_mentions = mentioned - source_labels
        valid = len(invalid_mentions) == 0

        return {
            "valid": valid,
            "expected_labels": sorted(source_labels),
            "mentioned_labels": sorted(mentioned),
            "invalid_mentions": sorted(invalid_mentions),
        }

    def determine_suggested_action(self, answer: Dict[str, Any], analysis: Dict[str, Any], reranked: List[Tuple[str, Any, float]]) -> str:
        intent = analysis.get("intent")
        status = answer.get("status")

        if status == "out_of_scope":
            return "This assistant is restricted to Parkville cosmetic & skincare/haircare product knowledge. For medical diagnoses, please consult a licensed physician."

        if status == "insufficient_evidence":
            return "Try refining your query with the specific Parkville product name (e.g. 'Shaan Cleanser', 'Clary Hair Mask', 'Seropipe Hair Dropper')."

        has_avoid = any(x[1]["metadata"].get("safety_label") == "AVOID DURING PREGNANCY" for x in reranked)
        has_doctor = any(x[1]["metadata"].get("safety_label") == "CONSULT A DOCTOR FIRST" for x in reranked)

        if has_avoid:
            return "Do not use during pregnancy. Consult your obstetrician or dermatologist for safe alternative formulations."
        elif has_doctor:
            return "Consult your obstetrician or healthcare professional before using this product during pregnancy."
        elif intent == "usage":
            return "Perform a 24-hour patch test before first use to check for skin or scalp sensitivity."
        elif intent == "comparison":
            return "Choose the product tailored to your specific skin/hair type and concerns as indicated in the product overview."
        else:
            return "Review the official Parkville product packaging and instructions for best application practices."

    def parse_chunk_sections(self, text: str) -> Dict[str, str]:
        sections: Dict[str, List[str]] = {
            "overview": [],
            "benefits": [],
            "ingredients": [],
            "usage": [],
            "ideal_for": [],
            "safety": [],
            "details": [],
        }

        current_sec = "overview"
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for line in lines:
            lower = line.lower()
            is_header_candidate = (":" in line) or (len(line) <= 50)

            if is_header_candidate and ("key benefits" in lower or lower.startswith("benefits:") or lower.endswith("benefits")):
                current_sec = "benefits"
                continue
            elif is_header_candidate and ("ingredients:" in lower or lower.startswith("ingredients") or lower.endswith("ingredients") or "ingredients" in lower):
                current_sec = "ingredients"
                if ":" in line:
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon:
                        sections["ingredients"].append(after_colon)
                continue
            elif is_header_candidate and ("how to use" in lower or lower.startswith("usage:") or lower.startswith("application:") or lower.startswith("how to use")):
                current_sec = "usage"
                if ":" in line:
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon:
                        sections["usage"].append(after_colon)
                continue
            elif is_header_candidate and ("ideal for" in lower or "skin type" in lower or "hair type" in lower):
                current_sec = "ideal_for"
                if ":" in line:
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon:
                        sections["ideal_for"].append(after_colon)
                continue
            elif is_header_candidate and ("pregnancy safety" in lower):
                current_sec = "safety"
                if ":" in line:
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon:
                        sections["safety"].append(after_colon)
                continue
            elif lower in ["safe", "consult a doctor first", "avoid during pregnancy"]:
                sections["safety"].append(line.upper())
                continue
            elif is_header_candidate and ("product details" in lower or "sun exposure" in lower):
                current_sec = "details"
                continue
            elif is_header_candidate and lower.startswith("overview"):
                current_sec = "overview"
                if ":" in line:
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon:
                        sections["overview"].append(after_colon)
                continue

            # Remove leading bullet symbols (e.g. , -, *, •)
            clean = re.sub(r"^[\-\*•\s]+", "", line).strip()
            if clean and not (len(sections["overview"]) == 0 and re.match(r"^\d+[\.\)]\s*", clean)):
                sections[current_sec].append(clean)

        return {k: "\n".join(v).strip() for k, v in sections.items()}

    def _generate_fallback_answer(self, query: str, retrieval: Dict[str, Any], confidence: Dict[str, Any]) -> Dict[str, Any]:
        reranked = retrieval["reranked"]
        analysis = retrieval.get("analysis", {})
        intent = analysis.get("intent", "product_lookup")
        qlow = query.lower()

        citations = []
        for cid, doc, _ in reranked[:3]:
            m = doc["metadata"]
            citations.append({
                "chunk_id": cid,
                "document": m["document_name"],
                "page": m["page_number"],
                "section": m["section"],
                "product": m["product"],
            })

        top_doc = reranked[0][1]
        top_meta = top_doc["metadata"]
        top_text = top_doc["text"]
        matched_product = (analysis.get("products") or [None])[0]
        product_name = top_meta.get("product") or matched_product or top_meta.get("brand")

        if not product_name and top_text:
            first_line = top_text.split("\n")[0].strip()
            clean_title = re.sub(r"^\d+[\.\)]\s*", "", first_line).strip()
            if clean_title and len(clean_title) < 80:
                product_name = clean_title

        if not product_name:
            product_name = "The product"

        product_name = re.sub(r"\s+(Ingredients|Overview|Key Benefits|Benefits|How to Use|Pregnancy Safety).*$", "", product_name, flags=re.IGNORECASE).strip()

        parsed = self.parse_chunk_sections(top_text)

        # 1. INGREDIENTS QUERY -> ONLY Ingredients
        if intent == "ingredients" or "ingredient" in qlow or "contain" in qlow:
            raw_ing = parsed.get("ingredients")
            if raw_ing:
                ing_items = [re.sub(r"^[\-\*•\s]+", "", item).strip() for item in raw_ing.split("\n") if item.strip()]
                clean_list = ", ".join(ing_items)
                answer = f"The ingredients in **{product_name}** are: {clean_list} [1]."
            else:
                answer = f"The active ingredients for **{product_name}** are detailed in the official product overview [1]."

        # 2. PREGNANCY SAFETY QUERY -> ONLY Safety classification
        elif intent == "pregnancy_safety" or "safe" in qlow or "pregnant" in qlow or "pregnancy" in qlow:
            safety_label = top_meta.get("safety_label") or parsed.get("safety") or "SAFE"
            if "avoid" in safety_label.lower():
                answer = f"**{product_name}** is classified as **AVOID DURING PREGNANCY** [1]."
            elif "doctor" in safety_label.lower() or "consult" in safety_label.lower():
                answer = f"**{product_name}** is classified as **CONSULT A DOCTOR FIRST** before use during pregnancy [1]."
            else:
                answer = f"**{product_name}** is classified as **SAFE** for use during pregnancy [1]."

        # 3. HOW TO USE / USAGE QUERY -> ONLY How to Use & Frequency
        elif intent == "usage" or "how to use" in qlow or "how should" in qlow or "apply" in qlow or "routine" in qlow:
            usage = parsed.get("usage")
            if usage:
                # Format clean sentences
                clean_usage = " ".join([l.strip() for l in usage.split("\n") if l.strip()])
                answer = f"To use **{product_name}**: {clean_usage} [1]."
            else:
                answer = f"Apply **{product_name}** as directed in the official product manual instructions [1]."

        # 4. BENEFITS QUERY -> ONLY Key Benefits
        elif intent == "benefits" or "benefit" in qlow or "help" in qlow or "good for" in qlow:
            benefits = parsed.get("benefits")
            if benefits:
                b_items = [f"• {b.strip()}" for b in benefits.split("\n") if b.strip()]
                answer = f"Key benefits of **{product_name}** include:\n" + "\n".join(b_items) + " [1]."
            else:
                overview = parsed.get("overview")
                answer = f"**{product_name}**: {overview or 'Provides targeted skincare/haircare support'} [1]."

        # 5. SKIN OR HAIR TYPE QUERY -> ONLY Target type
        elif intent in ["skin_type", "hair_type"] or "skin type" in qlow or "hair type" in qlow:
            ideal = parsed.get("ideal_for")
            if ideal:
                clean_ideal = " ".join([l.strip() for l in ideal.split("\n") if l.strip()])
                answer = f"**{product_name}** is suitable for: {clean_ideal} [1]."
            else:
                answer = f"**{product_name}** is suitable for the skin/hair conditions specified in [1]."

        # 6. COMPARISON QUERY -> Side-by-side concise comparison
        elif intent == "comparison" or "compare" in qlow or " vs " in qlow:
            items_summary = []
            for i, (cid, doc, _) in enumerate(reranked[:2], start=1):
                m = doc["metadata"]
                pname = m.get("product", f"Product {i}")
                slabel = m.get("safety_label", "SAFE")
                items_summary.append(f"• **{pname}**: Classified as **{slabel}** ({m.get('category', '').replace('_', ' ')}). Page {m.get('page_number')} [{i}].")
            answer = f"**Comparison Overview**:\n" + "\n".join(items_summary)

        # 7. GENERAL OVERVIEW -> Clean 1-2 sentence summary
        else:
            overview = parsed.get("overview")
            if overview:
                first_sent = overview.split("\n")[0]
                answer = f"**{product_name}**: {first_sent} [1]."
            else:
                clean_lines = [l for l in top_text.split('\n') if l.strip() and not re.match(r"^\d+[\.\)]", l)][:2]
                answer = f"**{product_name}**: {' '.join(clean_lines)} [1]."

        return {
            "status": "answered",
            "answer": answer.strip(),
            "evidence_summary": f"Retrieved from {product_name} ({top_meta.get('section', 'Product Overview')}) in {top_meta.get('document_name')}.",
            "citations": citations,
            "confidence": "high" if confidence["score"] >= 0.65 else "medium",
        }

    def ask(self, question: str, debug: bool = False) -> AskResponse:
        self.initialize()
        started = time.perf_counter()

        q = (question or "").strip()
        if not q:
            res = AskResponse(
                status="insufficient_evidence",
                answer="Please enter a question about Parkville products or guidelines.",
                evidence_summary="Empty question submitted.",
                confidence="insufficient",
                suggested_next_action="Enter a question to search the product knowledge base.",
            )
            return res

        if len(q) > config.MAX_QUESTION_CHARS:
            res = AskResponse(
                status="insufficient_evidence",
                answer=f"Question exceeds maximum allowed limit of {config.MAX_QUESTION_CHARS} characters.",
                evidence_summary="Character length limit exceeded.",
                confidence="insufficient",
                suggested_next_action="Shorten your question and try again.",
            )
            return res

        retrieval = self.hybrid_retrieve(q)
        analysis = retrieval["analysis"]

        if analysis["intent"] == "out_of_scope":
            latency = round((time.perf_counter() - started) * 1000, 2)
            trace = TraceInfo(latency_ms=latency, analysis=analysis)
            res = AskResponse(
                status="out_of_scope",
                answer="That question is outside the supported Parkville Skin & Hair Care product-information domain.",
                evidence_summary="Scope guard classified the query as outside product information.",
                confidence="insufficient",
                suggested_next_action="This assistant is designed strictly for Parkville product and pregnancy safety information. For medical diagnoses or prescriptions, consult a physician.",
                trace=trace,
            )
            self.log_interaction(q, res.model_dump())
            return res

        confidence = self.compute_confidence(retrieval)

        if not confidence["allowed"]:
            latency = round((time.perf_counter() - started) * 1000, 2)
            trace = TraceInfo(
                latency_ms=latency,
                analysis=analysis,
                confidence=confidence,
                dense_candidates=len(retrieval["dense"]),
                sparse_candidates=len(retrieval["sparse"]),
                fused_candidates=len(retrieval["fused"]),
                final_context_chunks=len(retrieval["reranked"]),
            )
            res = AskResponse(
                status="insufficient_evidence",
                answer="I don't have enough evidence in the supplied Parkville knowledge base to answer that safely.",
                evidence_summary=f"Retrieval confidence below threshold ({confidence['reason']}).",
                confidence="insufficient",
                suggested_next_action="Try mentioning the specific product brand or name (e.g., Shaan, Clary, Seropipe, Starville, Glamy Lab).",
                trace=trace,
                guards=GuardsInfo(confidence_gate=confidence),
            )
            self.log_interaction(q, res.model_dump())
            return res

        evidence_items: List[EvidenceItem] = []
        for cid, doc, score in retrieval["reranked"]:
            m = doc["metadata"]
            evidence_items.append(EvidenceItem(
                chunk_id=cid,
                document=m.get("document_name", ""),
                document_id=m.get("document_id", ""),
                page=m.get("page_number", 1),
                category=m.get("category", ""),
                brand=m.get("brand", ""),
                product=m.get("product", ""),
                section=m.get("section", ""),
                section_type=m.get("section_type", "general"),
                safety_label=m.get("safety_label", ""),
                score=round(score, 4),
                text=doc.get("text", ""),
            ))

        context = self.build_context(retrieval["reranked"])
        user_prompt = f"""Question:
{q}

Internal retrieval analysis:
{json.dumps(analysis, ensure_ascii=False)}

Retrieved evidence:
{context}

Return ONLY JSON matching this schema:
{json.dumps(RESPONSE_SCHEMA, ensure_ascii=False)}
"""

        answer_dict = None
        citation_check = {"valid": True}
        safety_check = {"valid": True}

        if self.llm_client:
            try:
                raw = self.call_llm([
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ])
                answer_dict = self.extract_json_object(raw)
                citation_check = self.validate_citations(answer_dict, retrieval["reranked"])
                safety_check = self.validate_safety_label(answer_dict, retrieval["reranked"], analysis["intent"])
            except Exception as first_error:
                logger.warning(f"Generation error, attempting repair: {first_error}")
                try:
                    repair_prompt = f"Previous response failed validation: {first_error}. Return ONLY corrected JSON."
                    repaired = self.call_llm([
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": repair_prompt},
                    ])
                    answer_dict = self.extract_json_object(repaired)
                    citation_check = self.validate_citations(answer_dict, retrieval["reranked"])
                    safety_check = self.validate_safety_label(answer_dict, retrieval["reranked"], analysis["intent"])
                except Exception as second_error:
                    logger.error(f"Repair failed: {second_error}")
                    answer_dict = self._generate_fallback_answer(q, retrieval, confidence)
        else:
            answer_dict = self._generate_fallback_answer(q, retrieval, confidence)

        latency = round((time.perf_counter() - started) * 1000, 2)
        trace = TraceInfo(
            latency_ms=latency,
            analysis=analysis,
            confidence=confidence,
            dense_candidates=len(retrieval["dense"]),
            sparse_candidates=len(retrieval["sparse"]),
            fused_candidates=len(retrieval["fused"]),
            final_context_chunks=len(retrieval["reranked"]),
        )
        guards = GuardsInfo(
            citation=citation_check,
            safety=safety_check,
            confidence_gate=confidence,
        )

        suggested_action = self.determine_suggested_action(answer_dict, analysis, retrieval["reranked"])

        citations_list = [
            CitationItem(**c) for c in answer_dict.get("citations", [])
            if all(k in c for k in ["chunk_id", "document", "page", "section", "product"])
        ]

        response = AskResponse(
            status=answer_dict.get("status", "answered"),
            answer=answer_dict.get("answer", ""),
            evidence_summary=answer_dict.get("evidence_summary", ""),
            citations=citations_list,
            confidence=answer_dict.get("confidence", "high"),
            evidence=evidence_items,
            suggested_next_action=suggested_action,
            trace=trace,
            guards=guards,
        )

        self.log_interaction(q, response.model_dump())
        return response

    def log_interaction(self, question: str, result: Dict[str, Any]) -> None:
        try:
            log_path = Path(config.QUERY_LOG_PATH)
            safe_result = {k: v for k, v in result.items() if k != "evidence"}
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "question": question, **safe_result},
                    ensure_ascii=False, default=str
                ) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log interaction: {e}")

    def get_catalog(self) -> CatalogResponse:
        self.initialize()
        product_map: Dict[str, Dict[str, Any]] = {}
        for c in self.chunks:
            p = c["metadata"]["product"]
            if not p:
                continue
            if p not in product_map:
                product_map[p] = {
                    "product": p,
                    "brand": c["metadata"]["brand"],
                    "category": c["metadata"]["category"],
                    "chunk_count": 0,
                    "safety_label": c["metadata"]["safety_label"],
                    "sections": set(),
                }
            product_map[p]["chunk_count"] += 1
            if c["metadata"]["safety_label"]:
                product_map[p]["safety_label"] = c["metadata"]["safety_label"]
            product_map[p]["sections"].add(c["metadata"]["section"])

        product_list = [
            ProductInfo(
                product=v["product"],
                brand=v["brand"],
                category=v["category"],
                chunk_count=v["chunk_count"],
                safety_label=v["safety_label"],
                sections=sorted(list(v["sections"])),
            )
            for v in product_map.values()
        ]

        categories = sorted(list({c["metadata"]["category"] for c in self.chunks if c["metadata"]["category"]}))

        return CatalogResponse(
            products=product_list,
            brands=self.all_brands,
            categories=categories,
            total_chunks=len(self.chunks),
            sample_questions=SAMPLE_QUESTIONS,
        )

    def get_health(self) -> HealthResponse:
        self.initialize()
        return HealthResponse(
            status="healthy",
            assistant=config.ASSISTANT_NAME,
            chunk_count=len(self.chunks),
            collection=config.CHROMA_COLLECTION,
            embedding_model=config.EMBEDDING_MODEL,
            reranker_model=config.RERANKER_MODEL,
            llm_model=config.LLM_MODEL,
            llm_configured=self.llm_client is not None,
        )

    def get_history(self, limit: int = 20) -> List[HistoryItem]:
        log_path = Path(config.QUERY_LOG_PATH)
        if not log_path.exists():
            return []

        history = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        citations = [
                            CitationItem(**c) for c in data.get("citations", [])
                            if isinstance(c, dict) and "chunk_id" in c
                        ]
                        history.append(HistoryItem(
                            ts=data.get("ts", ""),
                            question=data.get("question", ""),
                            status=data.get("status", "answered"),
                            answer=data.get("answer", ""),
                            evidence_summary=data.get("evidence_summary", ""),
                            confidence=data.get("confidence", "high"),
                            citations=citations,
                        ))
                        if len(history) >= limit:
                            break
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Error reading history: {e}")
        return history


rag_engine = RAGEngine()
