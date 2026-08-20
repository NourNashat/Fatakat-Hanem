import React from 'react';

interface BottomActionAreaProps {
  suggestedAction?: string;
  errorMessage?: string | null;
  onRetry?: () => void;
}

export const BottomActionArea: React.FC<BottomActionAreaProps> = ({
  suggestedAction,
  errorMessage,
  onRetry,
}) => {
  const defaultAction = 'Suggested next action: consult a clinician';
  const defaultError = 'Error state: retrieval unavailable — try again';

  return (
    <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-4 pt-1 animate-fade-in">
      {/* Left: Suggested Next Action Pill Card (Peach / Amber) */}
      <div
        style={{
          backgroundColor: 'var(--pill-amber-bg)',
          borderColor: 'var(--pill-amber-border)',
          color: 'var(--pill-amber-text)',
        }}
        className="rounded-2xl p-4 sm:p-5 border text-xs sm:text-sm font-semibold flex items-center justify-between shadow-xs transition-all"
      >
        <span className="leading-relaxed">
          {suggestedAction
            ? suggestedAction.toLowerCase().startsWith('suggested')
              ? suggestedAction
              : `Suggested next action: ${suggestedAction}`
            : defaultAction}
        </span>
      </div>

      {/* Right: Error State / Status Banner (Soft Rose / Red) */}
      <div
        style={{
          backgroundColor: 'var(--pill-rose-bg)',
          borderColor: 'var(--pill-rose-border)',
          color: 'var(--pill-rose-text)',
        }}
        className="rounded-2xl p-4 sm:p-5 border text-xs sm:text-sm font-semibold flex items-center justify-between shadow-xs transition-all"
      >
        <span className="leading-relaxed">
          {errorMessage ? `Error state: ${errorMessage}` : defaultError}
        </span>

        {errorMessage && onRetry && (
          <button
            onClick={onRetry}
            className="ml-3 px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-full text-xs font-bold transition-all shrink-0 cursor-pointer"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
};
