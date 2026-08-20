import React, { useState } from 'react';
import { Copy, Check, Sparkles } from 'lucide-react';
import type { AskResponse } from '../types/rag';

interface AnswerCardProps {
  response: AskResponse;
  onCitationClick: (chunkId: string) => void;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ response, onCitationClick }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(response.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy answer:', err);
    }
  };

  const renderInlineFormatted = (rawText: string) => {
    // 1. Process bold syntax **text** and citations [1]
    const tokenRegex = /(\*\*.*?\*\*|\[\d+\]|\[[A-Z0-9_-]+\])/g;
    const segments = rawText.split(tokenRegex);

    return segments.map((seg, idx) => {
      if (seg.startsWith('**') && seg.endsWith('**') && seg.length > 4) {
        const boldText = seg.substring(2, seg.length - 2);
        return (
          <strong key={idx} className="font-bold text-[var(--text-main)]">
            {boldText}
          </strong>
        );
      }

      if (seg.startsWith('[') && seg.endsWith(']')) {
        const citeRef = seg.substring(1, seg.length - 1);
        const citeNum = parseInt(citeRef, 10);
        let targetChunkId = citeRef;

        if (!isNaN(citeNum) && response.citations && response.citations[citeNum - 1]) {
          targetChunkId = response.citations[citeNum - 1].chunk_id;
        }

        return (
          <button
            key={idx}
            onClick={() => onCitationClick(targetChunkId)}
            className="inline-flex items-center justify-center px-1.5 py-0.5 mx-0.5 text-xs font-mono font-bold rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700 hover:bg-emerald-200 dark:hover:bg-emerald-900 transition-all cursor-pointer hover:scale-105 active:scale-95 align-baseline"
            title={`View citation source: ${targetChunkId}`}
          >
            [{citeRef}]
          </button>
        );
      }

      return <React.Fragment key={idx}>{seg}</React.Fragment>;
    });
  };

  return (
    <div className="w-full bg-[var(--card-bg)] border border-[var(--border-light)] rounded-2xl p-5 sm:p-7 shadow-sm space-y-4 animate-fade-in relative group transition-all">
      {/* Card Header with Exact Wireframe Title */}
      <div className="flex items-center justify-between border-b border-[var(--border-light)]/60 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-blue-600 dark:text-blue-400" />
          <h3 className="text-xs sm:text-sm font-extrabold uppercase tracking-wide text-[var(--text-heading)] font-sans">
            SHORT, EVIDENCE-GROUNDED ANSWER
          </h3>
        </div>

        <button
          onClick={handleCopy}
          className="opacity-70 hover:opacity-100 text-xs px-2.5 py-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all flex items-center gap-1.5 text-[var(--text-muted)] cursor-pointer"
          title="Copy answer"
        >
          {copied ? (
            <>
              <Check size={13} className="text-emerald-600 dark:text-emerald-400" />
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Copied</span>
            </>
          ) : (
            <>
              <Copy size={13} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Answer Body */}
      <div className="text-sm sm:text-base text-[var(--text-main)] font-normal leading-relaxed whitespace-pre-line space-y-2">
        {renderInlineFormatted(response.answer)}
      </div>

      {/* Evidence Summary Callout */}
      {response.evidence_summary && (
        <div className="text-xs text-[var(--text-muted)] pt-2 border-t border-[var(--border-light)] italic flex items-center gap-1.5">
          <span>{response.evidence_summary}</span>
        </div>
      )}
    </div>
  );
};
