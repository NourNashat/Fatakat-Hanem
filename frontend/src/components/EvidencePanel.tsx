import React, { useState } from 'react';
import { Shield } from 'lucide-react';
import type { EvidenceItemData } from '../types/rag';

interface EvidencePanelProps {
  evidence: EvidenceItemData[];
  highlightedChunkId: string | null;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  evidence,
  highlightedChunkId,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  const toggleRow = (chunkId: string) => {
    setExpandedRowId(expandedRowId === chunkId ? null : chunkId);
  };

  const getSafetyBadge = (label: string) => {
    const clean = (label || '').toUpperCase();
    if (clean === 'SAFE') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300">
          <Shield size={10} /> SAFE
        </span>
      );
    }
    if (clean === 'CONSULT A DOCTOR FIRST') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300">
          <Shield size={10} /> CONSULT DOCTOR
        </span>
      );
    }
    if (clean.includes('AVOID')) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 dark:bg-rose-900/40 text-rose-800 dark:text-rose-300">
          <Shield size={10} /> AVOID IN PREGNANCY
        </span>
      );
    }
    return null;
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--panel-evidence-bg)',
        borderColor: 'var(--panel-evidence-border)',
      }}
      className="w-full rounded-2xl p-5 sm:p-7 border shadow-xs transition-all space-y-4 animate-fade-in"
    >
      {/* Exact Wireframe Header: ▼ EVIDENCE (expand) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs sm:text-sm font-bold text-[var(--text-heading)] hover:opacity-80 transition-opacity cursor-pointer select-none"
      >
        <span className="text-[11px]">{isExpanded ? '▼' : '►'}</span>
        <span className="uppercase tracking-wide">
          EVIDENCE {isExpanded ? '(collapse)' : '(expand)'}
        </span>
        {evidence && evidence.length > 0 && (
          <span className="ml-1 text-xs font-normal text-[var(--text-muted)]">
            ({evidence.length} retrieved {evidence.length === 1 ? 'chunk' : 'chunks'})
          </span>
        )}
      </button>

      {/* Structured Table matching wireframe */}
      {isExpanded && (
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[550px]">
            <thead>
              <tr className="border-b border-[var(--border-light)] text-[var(--text-muted)] font-semibold">
                <th className="pb-3 pr-4 font-semibold">Document</th>
                <th className="pb-3 pr-4 font-semibold">Section</th>
                <th className="pb-3 pr-4 font-semibold">Page</th>
                <th className="pb-3 pr-4 font-semibold">Chunk ID</th>
                <th className="pb-3 font-semibold">Score</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[var(--border-light)]/60 text-[var(--text-main)]">
              {evidence && evidence.length > 0 ? (
                evidence.map((item, idx) => {
                  const isTarget = highlightedChunkId === item.chunk_id;
                  const isRowOpen = expandedRowId === item.chunk_id;

                  return (
                    <React.Fragment key={item.chunk_id || idx}>
                      <tr
                        id={`evidence-${item.chunk_id}`}
                        onClick={() => toggleRow(item.chunk_id)}
                        className={`hover:bg-white/60 dark:hover:bg-slate-800/50 cursor-pointer transition-colors ${
                          isTarget ? 'row-highlight bg-emerald-500/10 font-medium' : ''
                        }`}
                      >
                        <td className="py-3.5 pr-4 max-w-[220px]">
                          <div className="truncate font-medium" title={item.document}>
                            {item.document}
                          </div>
                          {item.product && (
                            <div className="text-[11px] text-[var(--text-muted)] truncate">
                              {item.product}
                            </div>
                          )}
                        </td>

                        <td className="py-3.5 pr-4 max-w-[150px]">
                          <span className="truncate block" title={item.section}>
                            {item.section}
                          </span>
                        </td>

                        <td className="py-3.5 pr-4 font-mono font-medium text-[var(--text-muted)]">
                          {item.page}
                        </td>

                        <td className="py-3.5 pr-4 font-mono text-xs text-emerald-700 dark:text-emerald-400 font-semibold">
                          {item.chunk_id}
                        </td>

                        <td className="py-3.5 font-mono text-xs font-semibold">
                          {item.score.toFixed(3)}
                        </td>
                      </tr>

                      {/* Expandable Snippet Row */}
                      {isRowOpen && (
                        <tr className="bg-white/80 dark:bg-slate-900/80">
                          <td colSpan={5} className="p-4 space-y-2 border-l-2 border-emerald-500 rounded-b-lg">
                            <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                              <span className="font-semibold text-[var(--text-main)]">
                                Full Extracted Chunk Text ({item.chunk_id}):
                              </span>
                              {item.safety_label && getSafetyBadge(item.safety_label)}
                            </div>
                            <div className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 font-normal leading-relaxed whitespace-pre-line bg-slate-50/80 dark:bg-slate-950/60 p-3 rounded-lg border border-slate-200/70 dark:border-slate-800">
                              {item.text}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                /* Default empty state matching wireframe dashes */
                <tr className="text-[var(--text-muted)]">
                  <td className="py-4 pr-4">—</td>
                  <td className="py-4 pr-4">—</td>
                  <td className="py-4 pr-4">—</td>
                  <td className="py-4 pr-4">—</td>
                  <td className="py-4">—</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
