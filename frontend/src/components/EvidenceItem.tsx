import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Shield, Hash } from 'lucide-react';
import type { EvidenceItemData } from '../types/rag';

interface EvidenceItemProps {
  item: EvidenceItemData;
  index: number;
  citationNumber?: number;
  isHighlighted?: boolean;
}

export const EvidenceItem: React.FC<EvidenceItemProps> = ({
  item,
  citationNumber,
  isHighlighted,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSafetyBadge = (label: string) => {
    const clean = (label || '').toUpperCase();
    if (clean === 'SAFE') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          <Shield size={11} />
          SAFE
        </span>
      );
    }
    if (clean === 'CONSULT A DOCTOR FIRST') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
          <Shield size={11} />
          CONSULT DOCTOR FIRST
        </span>
      );
    }
    if (clean.includes('AVOID')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">
          <Shield size={11} />
          AVOID DURING PREGNANCY
        </span>
      );
    }
    return null;
  };

  return (
    <div
      id={`evidence-${item.chunk_id}`}
      className={`glass-panel p-4 md:p-5 transition-all duration-300 ${
        isHighlighted ? 'citation-target-highlight border-emerald-500/80 shadow-emerald-500/20 shadow-lg' : ''
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2 pb-3 border-b border-slate-800/60">
        <div className="flex flex-wrap items-center gap-2">
          {citationNumber !== undefined && (
            <span className="px-2 py-0.5 rounded bg-emerald-500 text-slate-950 font-bold font-mono text-xs">
              [{citationNumber}]
            </span>
          )}

          <div className="flex items-center gap-1.5 text-xs font-mono font-semibold text-emerald-400">
            <Hash size={13} />
            <span>{item.chunk_id}</span>
          </div>

          <span className="text-slate-600">•</span>

          <div className="flex items-center gap-1 text-xs text-slate-300">
            <FileText size={13} className="text-slate-400" />
            <span className="truncate max-w-[220px]" title={item.document}>
              {item.document}
            </span>
            <span className="text-slate-400 font-mono font-medium">(p. {item.page})</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {item.safety_label && getSafetyBadge(item.safety_label)}
          <span className="px-2.5 py-0.5 rounded-md text-[11px] font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
            Score: {item.score.toFixed(3)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 py-3 text-xs text-slate-400">
        {item.product && (
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold">Product:</span>
            <span className="font-semibold text-slate-200 truncate block">{item.product}</span>
          </div>
        )}
        {item.brand && (
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold">Brand:</span>
            <span className="font-medium text-slate-300">{item.brand}</span>
          </div>
        )}
        {item.section && (
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold">Section:</span>
            <span className="font-medium text-slate-300">{item.section}</span>
          </div>
        )}
        {item.category && (
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold">Category:</span>
            <span className="font-medium capitalize text-slate-300">{item.category.replace('_', ' ')}</span>
          </div>
        )}
      </div>

      <div className="space-y-2 pt-2 border-t border-slate-800/40">
        <div
          className={`text-xs md:text-sm text-slate-300 font-normal leading-relaxed whitespace-pre-line ${
            !isExpanded ? 'line-clamp-3' : ''
          }`}
        >
          {item.text}
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors pt-1"
        >
          {isExpanded ? (
            <>
              <span>Show less</span>
              <ChevronUp size={14} />
            </>
          ) : (
            <>
              <span>Show full extracted chunk</span>
              <ChevronDown size={14} />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
