import React from 'react';
import type { AnswerStatus } from '../types/rag';

interface StatusBadgeProps {
  status: AnswerStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'answered':
        return {
          label: 'Status: Answered',
          bg: 'var(--pill-green-bg)',
          text: 'var(--pill-green-text)',
          border: 'var(--pill-green-border)',
        };
      case 'insufficient_evidence':
        return {
          label: 'Status: Insufficient Evidence',
          bg: 'var(--pill-amber-bg)',
          text: 'var(--pill-amber-text)',
          border: 'var(--pill-amber-border)',
        };
      case 'out_of_scope':
        return {
          label: 'Status: Out of Scope',
          bg: 'var(--pill-purple-bg)',
          text: 'var(--pill-purple-text)',
          border: 'var(--pill-purple-border)',
        };
      case 'error':
      default:
        return {
          label: 'Status: Error',
          bg: 'var(--pill-rose-bg)',
          text: 'var(--pill-rose-text)',
          border: 'var(--pill-rose-border)',
        };
    }
  };

  const config = getStatusConfig();

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
