import React from 'react';
import type { EvidenceQuality } from '../types/rag';

interface EvidenceQualityBadgeProps {
  quality: EvidenceQuality;
}

export const EvidenceQualityBadge: React.FC<EvidenceQualityBadgeProps> = ({ quality }) => {
  const getQualityConfig = () => {
    switch (quality) {
      case 'high':
        return {
          label: 'Evidence quality: High',
          bg: 'var(--pill-green-bg)',
          text: 'var(--pill-green-text)',
          border: 'var(--pill-green-border)',
        };
      case 'medium':
        return {
          label: 'Evidence quality: Medium',
          bg: 'var(--pill-green-bg)',
          text: 'var(--pill-green-text)',
          border: 'var(--pill-green-border)',
        };
      case 'low':
        return {
          label: 'Evidence quality: Low',
          bg: 'var(--pill-amber-bg)',
          text: 'var(--pill-amber-text)',
          border: 'var(--pill-amber-border)',
        };
      case 'insufficient':
      default:
        return {
          label: 'Evidence quality: Insufficient',
          bg: 'var(--pill-rose-bg)',
          text: 'var(--pill-rose-text)',
          border: 'var(--pill-rose-border)',
        };
    }
  };

  const config = getQualityConfig();

  return (
    <div
      style={{
        backgroundColor: config.bg,
        color: config.text,
        borderColor: config.border,
      }}
      className="inline-flex items-center px-5 py-1.5 rounded-full text-xs sm:text-sm font-semibold border shadow-xs transition-all"
    >
      <span>{config.label}</span>
    </div>
  );
};
