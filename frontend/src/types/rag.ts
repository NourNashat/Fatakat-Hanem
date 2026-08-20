export type AnswerStatus = 'answered' | 'insufficient_evidence' | 'out_of_scope' | 'error';
export type EvidenceQuality = 'high' | 'medium' | 'low' | 'insufficient';

export interface Citation {
  chunk_id: string;
  document: string;
  page: number;
  section: string;
  product: string;
}

export interface EvidenceItemData {
  chunk_id: string;
  document: string;
  document_id: string;
  page: number;
  category: string;
  brand: string;
  product: string;
  section: string;
  section_type: string;
  safety_label: string;
  score: number;
  dense_score?: number;
  sparse_score?: number;
  text: string;
}

export interface ConfidenceGateData {
  score: number;
  allowed: boolean;
  top_rerank_score?: number;
  top_rerank_normalized?: number;
  margin?: number;
  agreement?: number;
  reason?: string;
}

export interface TraceData {
  latency_ms: number;
  analysis: {
    category?: string | null;
    intent?: string;
    products?: string[];
    brands?: string[];
  };
  confidence?: ConfidenceGateData;
  dense_candidates?: number;
  sparse_candidates?: number;
  fused_candidates?: number;
  final_context_chunks?: number;
}

export interface GuardsData {
  citation?: {
    valid: boolean;
    invalid_chunk_ids?: string[];
    citation_count?: number;
  };
  safety?: {
    valid: boolean;
    expected_labels?: string[];
    mentioned_labels?: string[];
    invalid_mentions?: string[];
  };
  confidence_gate?: ConfidenceGateData;
}

export interface AskResponse {
  status: AnswerStatus;
  answer: string;
  evidence_summary: string;
  citations: Citation[];
  confidence: EvidenceQuality;
  evidence: EvidenceItemData[];
  suggested_next_action: string;
  trace?: TraceData;
  guards?: GuardsData;
}

export interface ProductInfo {
  product: string;
  brand: string;
  category: string;
  chunk_count: number;
  safety_label: string;
  sections: string[];
}

export interface CatalogResponse {
  products: ProductInfo[];
  brands: string[];
  categories: string[];
  total_chunks: number;
  sample_questions: string[];
}

export interface HealthResponse {
  status: string;
  assistant: string;
  chunk_count: number;
  collection: string;
  embedding_model: string;
  reranker_model: string;
  llm_model: string;
  llm_configured: boolean;
}

export interface HistoryItem {
  ts: string;
  question: string;
  status: AnswerStatus;
  answer: string;
  evidence_summary: string;
  confidence: EvidenceQuality;
  citations: Citation[];
}
