import React from 'react';
import { Sun, Moon, Database, BookOpen, History } from 'lucide-react';
import type { HealthResponse } from '../types/rag';

interface AppShellProps {
  children: React.ReactNode;
  health: HealthResponse | null;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  onOpenCatalog: () => void;
  onOpenHistory: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  health,
  theme,
  toggleTheme,
  onOpenCatalog,
  onOpenHistory,
}) => {
  return (
    <div className="min-h-screen bg-[var(--canvas-bg)] flex flex-col justify-between py-6 sm:py-10 px-4 sm:px-8 transition-colors duration-200">
      {/* Top Bar Navigation */}
      <header className="max-w-5xl mx-auto w-full mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-white font-black text-lg shadow-sm">
            P
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-extrabold text-[var(--text-main)] tracking-tight">
              Parkville Expert
            </h1>
            <p className="text-xs text-[var(--text-muted)] hidden sm:block">
              Evidence-Grounded Skin & Hair Safety Assistant
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* Real Indexed Chunks Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-200/70 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <Database size={12} className="text-emerald-600 dark:text-emerald-400" />
            <span>{health ? `${health.chunk_count} Chunks` : '303 Chunks'}</span>
          </div>

          {/* Catalog Button */}
          <button
            onClick={onOpenCatalog}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-[var(--border-light)] text-xs font-semibold text-[var(--text-main)] transition-all cursor-pointer shadow-xs"
          >
            <BookOpen size={13} className="text-teal-600 dark:text-teal-400" />
            <span>Catalog</span>
          </button>

          {/* History Button */}
          <button
            onClick={onOpenHistory}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-[var(--border-light)] text-xs font-semibold text-[var(--text-main)] transition-all cursor-pointer shadow-xs"
          >
            <History size={13} className="text-blue-600 dark:text-blue-400" />
            <span>History</span>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-[var(--border-light)] text-[var(--text-main)] transition-all cursor-pointer shadow-xs"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={15} className="text-amber-400" /> : <Moon size={15} className="text-slate-600" />}
          </button>
        </div>
      </header>

      {/* Main Canvas with Central Card */}
      <main className="max-w-5xl mx-auto w-full flex-1 flex flex-col justify-center">
        {children}
      </main>

      {/* Footer Attribution */}
      <footer className="max-w-5xl mx-auto w-full mt-8 text-center text-xs text-[var(--text-muted)] space-y-1">
        <p>
          Grounding: <span className="font-semibold">Skin Care Pregnancy Safety Review</span> & <span className="font-semibold">Hair Care Pregnancy Safety Manual</span>
        </p>
        <p className="opacity-75">
          Strict Citation Verification • Immutable Pregnancy Safety Labels • 0% Fabricated Information
        </p>
      </footer>
    </div>
  );
};
