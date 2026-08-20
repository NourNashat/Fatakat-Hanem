import React, { useState, useEffect } from 'react';
import { Sparkles, Search, GitMerge, ShieldCheck } from 'lucide-react';

export const LoadingState: React.FC = () => {
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: 'Analyzing Question & Intent',
      desc: 'Classifying category (Skin/Hair) and extracting product & brand entities...',
      icon: <Search size={16} className="text-emerald-400" />,
    },
    {
      title: 'Hybrid Retrieval (Dense + BM25)',
      desc: 'Querying multilingual vector index and sparse keyword index across 303 chunks...',
      icon: <Sparkles size={16} className="text-teal-400" />,
    },
    {
      title: 'Reranking & Confidence Gating',
      desc: 'Cross-encoder scoring, dense/sparse agreement check, and safety label gating...',
      icon: <GitMerge size={16} className="text-cyan-400" />,
    },
    {
      title: 'Synthesizing Grounded Answer',
      desc: 'Verifying citation lineage and ensuring pregnancy safety label integrity...',
      icon: <ShieldCheck size={16} className="text-emerald-300" />,
    },
  ];

  useEffect(() => {
    const timer1 = setTimeout(() => setStep(1), 700);
    const timer2 = setTimeout(() => setStep(2), 1600);
    const timer3 = setTimeout(() => setStep(3), 2800);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  return (
    <div className="glass-panel p-6 md:p-8 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
            PROCESSING RAG PIPELINE
          </span>
        </div>
        <span className="text-xs text-slate-400">Retrieving Evidence...</span>
      </div>

      <div className="space-y-4">
        {steps.map((s, idx) => {
          const isActive = step === idx;
          const isDone = step > idx;

          return (
            <div
              key={idx}
              className={`flex items-start gap-3 p-3 rounded-xl transition-all duration-300 ${
                isActive
                  ? 'bg-emerald-500/10 border border-emerald-500/30'
                  : isDone
                  ? 'opacity-60'
                  : 'opacity-30'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 ${
                  isActive
                    ? 'bg-emerald-500/20 text-emerald-300 animate-pulse'
                    : isDone
                    ? 'bg-slate-800 text-emerald-400'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {s.icon}
              </div>

              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-bold text-slate-200">{s.title}</h4>
                  {isActive && (
                    <div className="w-3 h-3 border-2 border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin" />
                  )}
                </div>
                <p className="text-xs text-slate-400">{s.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
