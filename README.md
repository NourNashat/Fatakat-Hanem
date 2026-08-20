# Parkville Skin & Hair Care Expert — Full-Stack RAG Web Application

A production-grade, citation-bound, evidence-grounded AI knowledge platform built on top of the **Parkville Skin & Hair Care Expert** RAG system.

---

## 1. Overview & Architecture

This application turns the existing Parkville hybrid RAG pipeline into a high-trust, production-quality full-stack web application.

```
                          ┌──────────────────────────┐
                          │   2 PDF Source Manuals   │
                          │  (Skin Care + Hair Care) │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │  303 Structured Chunks   │
                          │   Page/Product Lineage   │
                          └─────────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
            Dense Embeddings                            BM25
       (multilingual-e5-small)                      Sparse Index
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
                                Hybrid Retrieval
                                        │
                                        ▼
                                    RRF Fusion
                                        │
                                        ▼
                             Cross-Encoder Reranking
                           (ms-marco-MiniLM-L6-v2)
                                        │
                                        ▼
                                 Confidence Gate
                                 /             \
                       (Passed) /               \ (Refused)
                               ▼                 ▼
                     Citation-Bound LLM    Honest Refusal
                       (OpenAI/Groq)        (No Hallucination)
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
             Schema        Citation         Safety
           Validation        Guard          Guard
                └──────────────┼──────────────┘
                               ▼
                       FastAPI Backend API
                               │
                               ▼
                React 19 + TypeScript + Tailwind CSS
```

---

## 2. RAG Pipeline Capabilities Preserved

- **Real Knowledge Base**: 303 chunks indexed in persistent Chroma DB (`chroma.sqlite3`) and BM25 sparse index from:
  1. *Skin Care Pregnancy Safety Review* (Document ID: `SKIN-KB-001`)
  2. *Hair Care Pregnancy Safety Rebuilt* (Document ID: `HAIR-KB-001`)
- **Brands & Products**: Shaan, Clary, Seropipe, Starville, Glamy Lab, Bobana, etc.
- **Hybrid Retrieval**: Dense cosine similarity + BM25Okapi keyword scores, fused using Reciprocal Rank Fusion ($k=60$).
- **Cross-Encoder Reranking**: shortlists candidate chunks down to top relevant context.
- **Multi-factor Confidence Scoring**:
  $$\text{Score} = 0.55 \cdot \sigma(\text{rerank}) + 0.20 \cdot \text{agreement} + 0.10 \cdot \text{margin} + 0.10 \cdot \text{product\_signal} + 0.05 \cdot \text{safety\_signal}$$
- **Hard Citation Guard**: Validates that every citation chunk exists in the retrieved context and strictly matches document, page number, product, and section.
- **Safety Label Guard**: Ensures immutable pregnancy-safety classifications (`SAFE`, `CONSULT A DOCTOR FIRST`, `AVOID DURING PREGNANCY`).
- **Scope Guard & Refusal**: Rejects out-of-scope medical/diagnostic questions without hallucinations.

---

## 3. Web Application Features & UX Design

- **App Header & Status**: Live index status pill (303 chunks), light/dark mode switch, Catalog browser, and History drawer.
- **Question Composer**: Large input with auto-resize, clear button, keyboard shortcuts (Enter to submit, Shift+Enter for newline), and suggested guideline chips.
- **Evidence-Grounded Answer Card**:
  - `SHORT, EVIDENCE-GROUNDED ANSWER` header with copy button and latency metrics.
  - Interactive clickable inline citations (`[1]`, `[2]`) that smoothly scroll to and highlight corresponding evidence chunks.
  - Formatted evidence summary callout box.
- **Evidence Panel (First-Class Citizen)**:
  - Collapsible section with chunk count, filtering by product/document/content.
  - Detailed metadata for each chunk: Document name, Page number, Section, Product, Brand, Chunk ID, Rerank score, and Safety label.
  - Expandable text snippet with full context review.
- **Suggested Next Action**: Contextual advice (e.g. routine patch test, obstetrician consultation for pregnancy safety warnings) with a clear clinical disclaimer.
- **Knowledge Base Catalog Drawer**: Browse all 40+ products and guidelines directly.
- **Query History Drawer**: Review previous queries and rerun them with one click.
- **Multi-Stage Intelligent Loading Experience**: Animated progress reflecting real pipeline operations.
- **Error Recovery UI**: User-friendly error display with retry action.

---

## 4. API Contract

### `POST /api/ask`
**Request Body**:
```json
{
  "question": "What are the ingredients in Shaan Cleanser?",
  "debug": false
}
```

**Response Body**:
```json
{
  "status": "answered",
  "answer": "The Shaan Cleanser contains Vit C, Glycerin, Honey, Olive Oil, Hyaluronic Acid, Deacyl Glucoside, and Citric Acid [1].",
  "evidence_summary": "Retrieved from Product Overview for Shaan Cleanser in Skin Care Pregnancy Safety Review.",
  "citations": [
    {
      "chunk_id": "SKIN-KB-001-CH-0002",
      "document": "Skin_Care_Pregnancy_Safety_Review_Updated (2) (1).pdf",
      "page": 1,
      "section": "Product Overview",
      "product": "Shaan Cleanser"
    }
  ],
  "confidence": "high",
  "evidence": [
    {
      "chunk_id": "SKIN-KB-001-CH-0002",
      "document": "Skin_Care_Pregnancy_Safety_Review_Updated (2) (1).pdf",
      "page": 1,
      "category": "skin_care",
      "brand": "Shaan",
      "product": "Shaan Cleanser",
      "section": "Product Overview",
      "safety_label": "SAFE",
      "score": 8.3317,
      "text": "..."
    }
  ],
  "suggested_next_action": "Review the official Parkville product packaging and instructions for best application practices.",
  "trace": {
    "latency_ms": 182.4,
    "confidence": {
      "score": 0.8699,
      "allowed": true
    }
  }
}
```

### `GET /api/health`
Returns system status, chunk count (303), and loaded models.

### `GET /api/catalog`
Returns all indexed products, brands, categories, and sample guideline questions.

### `GET /api/manifest`
Returns source PDF metadata and chunk configuration.

### `GET /api/history`
Returns recent query interactions from `query_log.jsonl`.

---

## 5. Quick Start Instructions

### Prerequisites
- Python 3.10+ (with virtual environment)
- Node.js 18+ and npm

### 1-Click Launch (Windows)
Double-click `run_app.bat` or run in terminal:
```cmd
run_app.bat
```

### Manual Launch

**1. Backend**:
```powershell
# Activate virtual environment
.\.venv\Scripts\activate

# Start FastAPI server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Docs available at:* `http://localhost:8000/docs`

**2. Frontend**:
```powershell
cd frontend
npm run dev
```
*Web Application available at:* `http://localhost:5173`

---

## 6. Testing & Quality Assurance

Run the automated backend test suite:
```powershell
.\.venv\Scripts\python -m pytest backend/tests/test_api.py -v
```

Build the frontend bundle:
```powershell
cd frontend
npm run build
```
