import React from 'react';
import { X, History, Clock, ArrowRight, MessageSquare } from 'lucide-react';
import type { HistoryItem } from '../types/rag';
import { StatusBadge } from './StatusBadge';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  history: HistoryItem[];
  onSelectQuery: (question: string) => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  history,
  onSelectQuery,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg h-full bg-slate-950 border-l border-slate-800 p-6 flex flex-col space-y-5 overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <History size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">
                Query History
              </h3>
              <p className="text-xs text-slate-400">
                Recent evidence retrieval sessions
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {history.map((item, idx) => (
            <div
              key={idx}
              onClick={() => {
                onSelectQuery(item.question);
                onClose();
              }}
              className="glass-panel p-4 hover:border-emerald-500/50 cursor-pointer group transition-all space-y-2.5"
            >
              <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {item.ts}
                </span>
                <div className="flex items-center gap-1.5">
                  <StatusBadge status={item.status} />
                </div>
              </div>

              <h4 className="text-sm font-semibold text-slate-200 group-hover:text-emerald-300 transition-colors flex items-start justify-between gap-2">
                <span className="line-clamp-2">{item.question}</span>
                <ArrowRight size={15} className="text-slate-600 group-hover:text-emerald-400 shrink-0 mt-0.5" />
              </h4>

              {item.answer && (
                <p className="text-xs text-slate-400 line-clamp-2 font-normal leading-relaxed">
                  {item.answer}
                </p>
              )}

              {item.citations && item.citations.length > 0 && (
                <div className="flex items-center gap-2 pt-2 border-t border-slate-800/40 text-[11px] text-emerald-400">
                  <MessageSquare size={12} />
                  <span>{item.citations.length} cited source{item.citations.length > 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          ))}

          {history.length === 0 && (
            <div className="text-center py-16 text-slate-500 text-sm">
              No query history available yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
