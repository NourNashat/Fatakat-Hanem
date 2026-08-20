import React, { useState, useEffect } from 'react';
import { AppShell } from './components/AppShell';
import { QuestionComposer } from './components/QuestionComposer';
import { StatusBadge } from './components/StatusBadge';
import { EvidenceQualityBadge } from './components/EvidenceQualityBadge';
import { AnswerCard } from './components/AnswerCard';
import { EvidencePanel } from './components/EvidencePanel';
import { BottomActionArea } from './components/BottomActionArea';
import { CatalogDrawer } from './components/CatalogDrawer';
import { HistoryDrawer } from './components/HistoryDrawer';
import { askQuestion, fetchHealth, fetchCatalog, fetchHistory } from './api/ragApi';
import type { AskResponse, HealthResponse, CatalogResponse, HistoryItem } from './types/rag';

const INITIAL_PLACEHOLDER_RESPONSE: AskResponse = {
  status: 'answered',
  answer: 'Plain-language recommendation, clearly separated from the evidence panel below.',
  evidence_summary: 'Ask a question above or select a guideline chip to retrieve cited clinical evidence.',
  citations: [],
  confidence: 'high',
  evidence: [],
  suggested_next_action: 'consult a clinician',
};

export const App: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [response, setResponse] = useState<AskResponse | null>(INITIAL_PLACEHOLDER_RESPONSE);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [highlightedChunkId, setHighlightedChunkId] = useState<string | null>(null);

  // System metadata
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Drawer toggles
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Initialize theme and load catalog/health
  useEffect(() => {
    const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (isDark) {
      setTheme('dark');
      document.documentElement.classList.add('dark');
    }

    const initData = async () => {
      try {
        const [h, c, hist] = await Promise.all([
          fetchHealth(),
          fetchCatalog(),
          fetchHistory(),
        ]);
        setHealth(h);
        setCatalog(c);
        setHistory(hist);
      } catch (err) {
        console.error('Failed to load initial data:', err);
      }
    };

    initData();
  }, []);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    if (next === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleAsk = async (question: string) => {
    setIsLoading(true);
    setError(null);
    setLastQuery(question);
    setHighlightedChunkId(null);

    try {
      const data = await askQuestion(question);
      setResponse(data);
      // Refresh history in background
      fetchHistory().then(setHistory).catch(() => {});
    } catch (err: any) {
      console.error('Query error:', err);
      setError(err.message || 'Retrieval failed. Please try again.');
      setResponse({
        status: 'error',
        answer: 'Failed to retrieve evidence from the server. Please ensure the backend is running.',
        evidence_summary: 'Error during retrieval execution.',
        citations: [],
        confidence: 'insufficient',
        evidence: [],
        suggested_next_action: 'Check server connection and retry your query.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCitationClick = (chunkId: string) => {
    setHighlightedChunkId(chunkId);
    const element = document.getElementById(`evidence-${chunkId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <AppShell
      health={health}
      theme={theme}
      toggleTheme={toggleTheme}
      onOpenCatalog={() => setIsCatalogOpen(true)}
      onOpenHistory={() => setIsHistoryOpen(true)}
    >
      {/* Exact Wireframe Container Box */}
      <div className="w-full bg-[var(--card-bg)] border border-[var(--border-light)] rounded-3xl p-5 sm:p-9 shadow-[var(--shadow-card)] space-y-6 sm:space-y-7 transition-all">
        {/* 1. Top Search Box */}
        <QuestionComposer
          onSubmit={handleAsk}
          isLoading={isLoading}
          sampleQuestions={catalog?.sample_questions || []}
        />

        {/* 2. Status Area with side-by-side capsule pills */}
        <div className="flex flex-wrap items-center gap-3 pt-0.5">
          <StatusBadge status={response ? response.status : 'answered'} />
          <EvidenceQualityBadge quality={response ? response.confidence : 'high'} />
        </div>

        {/* 3. Short, Evidence-Grounded Answer Card */}
        {response && (
          <AnswerCard
            response={response}
            onCitationClick={handleCitationClick}
          />
        )}

        {/* 4. Evidence Panel (Structured table with Document, Section, Page, Chunk ID, Score) */}
        <EvidencePanel
          evidence={response ? response.evidence : []}
          highlightedChunkId={highlightedChunkId}
        />

        {/* 5. Bottom Area with Suggested Next Action and Error/Status Banners */}
        <BottomActionArea
          suggestedAction={response?.suggested_next_action}
          errorMessage={error}
          onRetry={() => lastQuery && handleAsk(lastQuery)}
        />
      </div>

      {/* Drawers */}
      <CatalogDrawer
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
        catalog={catalog}
        onSelectProduct={(p: string) => {
          setIsCatalogOpen(false);
          handleAsk(p);
        }}
      />

      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onSelectQuery={(q: string) => {
          setIsHistoryOpen(false);
          handleAsk(q);
        }}
      />
    </AppShell>
  );
};

export default App;
