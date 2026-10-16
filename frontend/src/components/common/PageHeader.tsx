import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle: string;
  badge?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  badge,
  actions,
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1 border-b border-[#1E3050]/50">
      <div>
        <div className="flex items-center gap-2.5">
          <h2 className="text-xl font-extrabold text-white tracking-tight">{title}</h2>
          {badge && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-cyan-950/80 text-cyan-300 border border-cyan-500/40">
              {badge}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
      </div>

      {actions && <div className="flex items-center gap-2.5 shrink-0">{actions}</div>}
    </div>
  );
};
