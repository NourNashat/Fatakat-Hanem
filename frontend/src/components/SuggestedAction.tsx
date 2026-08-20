import React from 'react';
import { ArrowRightCircle, AlertCircle } from 'lucide-react';

interface SuggestedActionProps {
  action: string;
}

export const SuggestedAction: React.FC<SuggestedActionProps> = ({ action }) => {
  if (!action) return null;

  return (
    <div className="glass-panel p-4 md:p-5 border-l-4 border-l-emerald-500 space-y-2 animate-fade-in">
      <div className="flex items-start gap-3">
        <ArrowRightCircle size={18} className="text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
            SUGGESTED NEXT ACTION
          </h4>
          <p className="text-sm font-medium text-slate-100 leading-relaxed">
            {action}
          </p>
        </div>
      </div>

      <div className="pt-2 mt-2 border-t border-slate-800/40 flex items-center gap-1.5 text-[11px] text-slate-400">
        <AlertCircle size={12} className="text-slate-500 shrink-0" />
        <span>
          This assistant provides evidence-grounded product and cosmetic safety information. It does not provide medical diagnoses or replace qualified medical judgment.
        </span>
      </div>
    </div>
  );
};
