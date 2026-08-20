import type { AskResponse, CatalogResponse, HealthResponse, HistoryItem } from '../types/rag';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export async function askQuestion(question: string, debug: boolean = false): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, debug }),
  });

  if (!response.ok) {
    const errText = await response.text();
    let errorDetail = 'Network response was not ok';
    try {
      const errJson = JSON.parse(errText);
      errorDetail = errJson.error_detail || errJson.message || errorDetail;
    } catch {
      // keep fallback text
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function fetchCatalog(): Promise<CatalogResponse> {
  const response = await fetch(`${API_BASE_URL}/api/catalog`);
  if (!response.ok) {
    throw new Error('Failed to fetch catalog');
  }
  return response.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error('Failed to fetch system health');
  }
  return response.json();
}

export async function fetchHistory(limit: number = 20): Promise<HistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch query history');
  }
  return response.json();
}
