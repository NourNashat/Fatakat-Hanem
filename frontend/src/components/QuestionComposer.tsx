import React, { useState } from 'react';
import { X, ArrowUpRight } from 'lucide-react';

interface QuestionComposerProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
  sampleQuestions: string[];
}

export const QuestionComposer: React.FC<QuestionComposerProps> = ({
  onSubmit,
  isLoading,
  sampleQuestions,
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = query.trim();
    if (trimmed && !isLoading) {
      onSubmit(trimmed);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSelectSample = (question: string) => {
    setQuery(question);
    onSubmit(question);
  };

  return (
    <div className="w-full space-y-3">
      {/* Wireframe Top Search Box */}
      <form
        onSubmit={handleSubmit}
        className="w-full bg-[var(--card-bg)] border border-[var(--border-light)] rounded-2xl p-2 sm:p-2.5 flex items-center gap-3 shadow-sm focus-within:border-[#00a884] focus-within:ring-2 focus-within:ring-[#00a884]/20 transition-all"
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a guideline..."
          disabled={isLoading}
          maxLength={600}
          className="flex-1 bg-transparent border-none outline-none px-3 py-1.5 text-sm sm:text-base italic text-[var(--text-main)] placeholder:text-slate-400 placeholder:italic font-normal disabled:opacity-60"
        />

        {query && !isLoading && (
          <button
            type="button"
            onClick={() => setQuery('')}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Clear"
          >
            <X size={16} />
          </button>
        )}

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          style={{ backgroundColor: 'var(--teal-btn)' }}
          className="text-white font-medium text-sm sm:text-base px-6 sm:px-8 py-2 sm:py-2.5 rounded-full transition-all duration-150 hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:pointer-events-none cursor-pointer shrink-0 shadow-sm"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin mx-2" />
          ) : (
            'Ask'
          )}
        </button>
      </form>

      {/* Suggested Guideline Queries */}
      {sampleQuestions.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1 px-1">
          <span className="text-xs font-semibold text-[var(--text-muted)] mr-1">
            Try asking:
          </span>
          {sampleQuestions.slice(0, 4).map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSelectSample(sq)}
              disabled={isLoading}
              className="text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800/80 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 text-slate-700 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-300 border border-slate-200 dark:border-slate-700/60 hover:border-emerald-300 dark:hover:border-emerald-700 transition-all flex items-center gap-1 cursor-pointer disabled:opacity-50"
            >
              <span>{sq}</span>
              <ArrowUpRight size={11} className="opacity-60" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
