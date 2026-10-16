import React from 'react';
import { LucideIcon, ArrowRight } from 'lucide-react';
import { CyberCard } from './CyberCard';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  steps?: Array<{ title: string; desc: string }>;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionText,
  onAction,
  steps,
}) => {
  return (
    <CyberCard className="p-8 md:p-12 text-center" hoverEffect={false}>
      <div className="relative w-16 h-16 mx-auto mb-4 flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-cyan-500/10 border border-cyan-500/30 animate-pulse" />
        <Icon className="w-8 h-8 text-cyan-400 relative z-10" />
      </div>

      <h3 className="text-base font-bold text-white tracking-wide">{title}</h3>
      <p className="text-xs text-slate-400 mt-1.5 max-w-md mx-auto leading-relaxed">
        {description}
      </p>

      {steps && steps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl mx-auto mt-6 text-left">
          {steps.map((s, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-lg bg-[#070D1A]/80 border border-[#1E3050]/60"
            >
              <div className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5 mb-1">
                <span className="w-4 h-4 rounded-full bg-cyan-950 border border-cyan-500/40 text-[10px] flex items-center justify-center text-cyan-300">
                  {idx + 1}
                </span>
                {s.title}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      )}

      {actionText && onAction && (
        <div className="mt-6">
          <button
            onClick={onAction}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all cursor-pointer"
          >
            <span>{actionText}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </CyberCard>
  );
};
