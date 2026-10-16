import React from 'react';

export type BadgeStatus =
  | 'active'
  | 'inactive'
  | 'anomaly'
  | 'anomalous'
  | 'normal'
  | 'medium'
  | 'unclassified'
  | 'approved'
  | 'validated'
  | 'pending'
  | 'warning';

interface StatusBadgeProps {
  status: BadgeStatus | string;
  text?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  text,
  size = 'md',
}) => {
  const normStatus = (status || '').toLowerCase();

  const configs: Record<string, { bg: string; dot: string; label: string }> = {
    normal: {
      bg: 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300',
      dot: 'bg-emerald-400',
      label: text || 'Normal',
    },
    medium: {
      bg: 'bg-amber-950/60 border-amber-500/50 text-amber-300',
      dot: 'bg-amber-400',
      label: text || 'Medium',
    },
    anomalous: {
      bg: 'bg-rose-950/70 border-rose-500/60 text-rose-300',
      dot: 'bg-rose-400 animate-pulse',
      label: text || 'Anomalous',
    },
    anomaly: {
      bg: 'bg-rose-950/70 border-rose-500/60 text-rose-300',
      dot: 'bg-rose-400 animate-pulse',
      label: text || 'Anomalous',
    },
    unclassified: {
      bg: 'bg-slate-900/70 border-slate-600/50 text-slate-400',
      dot: 'bg-slate-500',
      label: text || 'Unclassified',
    },
    active: {
      bg: 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300',
      dot: 'bg-emerald-400 animate-pulse',
      label: text || 'ACTIVE',
    },
    inactive: {
      bg: 'bg-slate-900/60 border-slate-700/40 text-slate-400',
      dot: 'bg-slate-500',
      label: text || 'INACTIVE',
    },
    approved: {
      bg: 'bg-cyan-950/60 border-cyan-500/50 text-cyan-300',
      dot: 'bg-cyan-400',
      label: text || 'APPROVED',
    },
    validated: {
      bg: 'bg-blue-950/60 border-blue-500/50 text-blue-300',
      dot: 'bg-blue-400',
      label: text || 'VALIDATED',
    },
    pending: {
      bg: 'bg-amber-950/60 border-amber-500/40 text-amber-300',
      dot: 'bg-amber-400 animate-pulse',
      label: text || 'PENDING',
    },
    warning: {
      bg: 'bg-amber-950/60 border-amber-500/50 text-amber-300',
      dot: 'bg-amber-400',
      label: text || 'WARNING',
    },
  };

  const current = configs[normStatus] || configs.unclassified;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-semibold tracking-wider ${padding} ${current.bg}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${current.dot}`} />
      <span>{current.label}</span>
    </span>
  );
};
