import React from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  return (
    <div className="glass-panel p-6 md:p-8 border-rose-500/30 space-y-5 animate-fade-in">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-rose-500/15 text-rose-400 shrink-0">
          <AlertOctagon size={24} />
        </div>

        <div className="space-y-1.5">
          <h3 className="text-base font-bold text-rose-300">
            Retrieval unavailable — try again
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">
            {message || 'Unable to connect to the knowledge retrieval engine. Please ensure the backend server is active.'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2 border-t border-slate-800/60">
        <button
          onClick={onRetry}
          className="btn-primary bg-rose-600 hover:bg-rose-500 text-xs py-2 px-4 shadow-rose-900/40"
        >
          <RotateCcw size={14} className="mr-1" />
          <span>Retry Query</span>
        </button>
        <span className="text-xs text-slate-400">
          We strictly prefer honest failure over hallucinating inaccurate guideline answers.
        </span>
      </div>
    </div>
  );
};
