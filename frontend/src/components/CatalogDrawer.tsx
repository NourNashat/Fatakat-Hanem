import React, { useState } from 'react';
import { X, Search, BookOpen, Shield, ArrowRight } from 'lucide-react';
import type { CatalogResponse } from '../types/rag';

interface CatalogDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  catalog: CatalogResponse | null;
  onSelectProduct: (productName: string) => void;
}

export const CatalogDrawer: React.FC<CatalogDrawerProps> = ({
  isOpen,
  onClose,
  catalog,
  onSelectProduct,
}) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  if (!isOpen || !catalog) return null;

  const filteredProducts = catalog.products.filter((p) => {
    const matchesSearch =
      p.product.toLowerCase().includes(search.toLowerCase()) ||
      p.brand.toLowerCase().includes(search.toLowerCase());
    const matchesCategory =
      selectedCategory === 'all' || p.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-xl h-full bg-slate-950 border-l border-slate-800 p-6 flex flex-col space-y-5 overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <BookOpen size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">
                Knowledge Base Catalog
              </h3>
              <p className="text-xs text-slate-400">
                {catalog.products.length} Products • {catalog.total_chunks} Chunks Indexed
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

        <div className="space-y-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search products or brands (e.g. Shaan, Clary, Seropipe)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === 'all'
                  ? 'bg-emerald-500 text-slate-950'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              All ({catalog.products.length})
            </button>
            {catalog.categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                  selectedCategory === cat
                    ? 'bg-emerald-500 text-slate-950'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {cat.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {filteredProducts.map((p) => (
            <div
              key={p.product}
              onClick={() => {
                onSelectProduct(`Tell me about ${p.product} including ingredients, usage and pregnancy safety.`);
                onClose();
              }}
              className="glass-panel p-4 hover:border-emerald-500/50 cursor-pointer group transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono">
                      {p.brand}
                    </span>
                    <span className="text-xs text-slate-400 capitalize">
                      {p.category.replace('_', ' ')}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-100 group-hover:text-emerald-300 transition-colors">
                    {p.product}
                  </h4>
                </div>

                <ArrowRight size={16} className="text-slate-600 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all shrink-0 mt-1" />
              </div>

              <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800/50 text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  {p.safety_label && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                      <Shield size={11} />
                      {p.safety_label}
                    </span>
                  )}
                </div>
                <span>{p.chunk_count} Knowledge Chunks</span>
              </div>
            </div>
          ))}

          {filteredProducts.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-sm">
              No products found matching &quot;{search}&quot;
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
