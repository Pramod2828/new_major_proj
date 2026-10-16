import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Shield,
  Layers,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Cpu,
  Zap,
  Terminal,
  ExternalLink,
  ShieldCheck,
  Server,
  Clock,
  HelpCircle
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  Legend
} from 'recharts';
import { api } from '../services/api';
import { DashboardStats } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { AnimatedCounter } from '../components/common/AnimatedCounter';
import { CyberShield3D } from '../components/common/CyberShield3D';
import { EmptyState } from '../components/common/EmptyState';
import { StatusBadge } from '../components/common/StatusBadge';

export const DashboardPage: React.FC<{ onNavigate: (tab: string) => void }> = ({ onNavigate }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadStats = async (range: string = timeRange) => {
    try {
      setRefreshing(true);
      const data = await api.getDashboardStats(range);
      setStats(data);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStats(timeRange);
  }, [timeRange]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 text-slate-400 gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
        <span className="font-mono text-xs tracking-wider uppercase text-cyan-300">Synchronizing SOC Telemetry...</span>
      </div>
    );
  }

  const hasData = stats && stats.total_processed > 0;

  // Chart data for 3 categories
  const categoryRatioData = hasData ? [
    { name: 'Normal', count: stats.normal_count, fill: '#10B981', percent: stats.normal_percentage },
    { name: 'Medium Risk', count: stats.medium_count, fill: '#F59E0B', percent: stats.medium_percentage },
    { name: 'Anomalous', count: stats.anomalous_count, fill: '#EF4444', percent: stats.anomalous_percentage },
    ...(stats.unclassified_count > 0 ? [{ name: 'Unclassified', count: stats.unclassified_count, fill: '#64748B', percent: stats.unclassified_percentage }] : [])
  ] : [];

  const timelineData = stats?.timeline_24h || [];

  return (
    <div className="space-y-6">
      {/* Hero Section with 3D Cyber Emblem */}
      <CyberCard className="p-6 md:p-8 overflow-hidden" glow="cyan" hoverEffect={false}>
        <div className="flex flex-col lg:flex-row items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 text-center lg:text-left max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
              <Zap className="w-3.5 h-3.5 text-cyan-400" />
              <span>BEHAVIORAL THREAT INTELLIGENCE</span>
            </div>

            <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Security Operations Center
            </h2>
            <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans">
              Automated syslog anomaly detection powered by Random Forest & XGBoost with mathematical SHAP explainability and 3-level risk categorization (Normal, Medium, Anomalous).
            </p>

            {/* Quick Model Status Bar */}
            <div className="pt-2 flex flex-wrap items-center justify-center lg:justify-start gap-3">
              {stats?.active_model ? (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#070D1A] border border-cyan-500/30 text-xs font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                  <span className="text-slate-400">Production Model:</span>
                  <span className="text-cyan-300 font-bold">{stats.active_model.name}</span>
                  <span className="text-slate-500">({stats.active_model.algorithm.toUpperCase()})</span>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-950/40 border border-amber-500/30 text-xs font-mono text-amber-300">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>No Model Activated for Production</span>
                  </div>
                  <button
                    onClick={() => onNavigate('datasets')}
                    className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] cursor-pointer"
                  >
                    <span>Configure & Train</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* 3D Cyber Emblem */}
          <div className="shrink-0 py-2">
            <CyberShield3D />
          </div>
        </div>
      </CyberCard>

      {/* Time Range Selector & Controls Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span className="font-bold text-white uppercase tracking-wider text-[11px]">Telemetry Scope:</span>
          <span className="text-slate-400">Calculated strictly from actual stored events</span>
        </div>

        <div className="flex items-center gap-2 bg-[#070D1A] border border-[#1E3050] p-1 rounded-xl text-xs font-mono">
          {[
            { label: 'Last 24 Hours', value: '24h' },
            { label: 'Last 7 Days', value: '7d' },
            { label: 'Last 30 Days', value: '30d' },
            { label: 'All Time', value: 'all' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setTimeRange(tab.value)}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                timeRange === tab.value
                  ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
          <button
            onClick={() => loadStats(timeRange)}
            disabled={refreshing}
            className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Separate Unclassified Banner (Only when present) */}
      {stats && stats.unclassified_count > 0 && (
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-700/60 text-slate-300 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <HelpCircle className="w-4 h-4 text-slate-400 shrink-0" />
            <div>
              <span className="text-white font-bold">{stats.unclassified_count} Unclassified Events</span>
              <span className="text-slate-400"> ({stats.unclassified_percentage}% of total) require manual review due to missing model probability or uninitialized classifier.</span>
            </div>
          </div>
          <button
            onClick={() => onNavigate('history')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold"
          >
            Review In Audit Log
          </button>
        </div>
      )}

      {/* 4 Separate Statistics Cards: Total, Normal, Medium, Anomalous */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Logs */}
        <CyberCard className="p-5" glow="cyan">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-semibold uppercase tracking-wider text-slate-300">Total Logs</span>
            <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-500/30 text-blue-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
            <AnimatedCounter value={stats?.total_logs ?? 0} />
          </div>
          <div className="text-[11px] text-slate-500 font-mono mt-2 flex items-center gap-1">
            <Server className="w-3 h-3 text-cyan-400" />
            <span>Scope: {timeRange.toUpperCase()}</span>
          </div>
        </CyberCard>

        {/* Card 2: Normal Events (Green) */}
        <CyberCard className="p-5" glow="emerald">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-semibold uppercase tracking-wider text-slate-300">Normal Events</span>
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-extrabold font-mono text-emerald-400 tracking-tight">
              <AnimatedCounter value={stats?.normal_count ?? 0} />
            </div>
            <span className="text-xs font-mono font-bold text-emerald-300 bg-emerald-950/80 border border-emerald-500/40 px-2 py-0.5 rounded-full">
              {stats ? `${stats.normal_percentage}%` : '0%'}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 font-mono mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Low risk; baseline normal</span>
          </div>
        </CyberCard>

        {/* Card 3: Medium-Risk Events (Amber) */}
        <CyberCard className="p-5" glow="amber">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-semibold uppercase tracking-wider text-slate-300">Medium-Risk Events</span>
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-500/30 text-amber-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-extrabold font-mono text-amber-400 tracking-tight">
              <AnimatedCounter value={stats?.medium_count ?? 0} />
            </div>
            <span className="text-xs font-mono font-bold text-amber-300 bg-amber-950/80 border border-amber-500/40 px-2 py-0.5 rounded-full">
              {stats ? `${stats.medium_percentage}%` : '0%'}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 font-mono mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span>Borderline risk; uncertain</span>
          </div>
        </CyberCard>

        {/* Card 4: Anomalous Events (Red) */}
        <CyberCard className="p-5" glow="rose">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-semibold uppercase tracking-wider text-slate-300">Anomalous Events</span>
            <div className="p-2 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-3xl font-extrabold font-mono text-rose-400 tracking-tight">
              <AnimatedCounter value={stats?.anomalous_count ?? 0} />
            </div>
            <span className="text-xs font-mono font-bold text-rose-300 bg-rose-950/80 border border-rose-500/40 px-2 py-0.5 rounded-full">
              {stats ? `${stats.anomalous_percentage}%` : '0%'}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 font-mono mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            <span>High risk; statistical anomaly</span>
          </div>
        </CyberCard>
      </div>

      {/* Analytics & Activity Section */}
      {!hasData ? (
        <EmptyState
          icon={Activity}
          title="No Telemetry Recorded Yet"
          description="Smart-Log displays only authentic results from actual trained classifiers. To begin detecting anomalies and visualizing live threat telemetries, complete the two-step setup below."
          actionText="Go to Dataset Manager"
          onAction={() => onNavigate('datasets')}
          steps={[
            {
              title: 'Dataset Integration & Label Mapping',
              desc: 'Upload your server log dataset (CSV, JSON, or JSONL), inspect schema columns, map Normal (0) and Anomaly (1) labels, and approve the dataset.',
            },
            {
              title: 'Supervised Training & Activation',
              desc: 'Train Random Forest and XGBoost classifiers on the approved split, compare held-out test metrics, and activate the top-performing model for live inference.',
            },
          ]}
        />
      ) : (
        <div className="space-y-6">
          {/* 24-Hour Timeline Chart: Normal, Medium, Anomalous */}
          <CyberCard className="p-5" glow="cyan">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 border-b border-[#1E3050]/60 mb-4 gap-2">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  24-Hour Event Timeline
                </h3>
                <p className="text-[11px] text-slate-400 font-mono">
                  Chronological hourly volume of Normal (green), Medium (amber), and Anomalous (red) classifications
                </p>
              </div>
              <div className="flex items-center gap-4 text-[11px] font-mono">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>Normal</span>
                </span>
                <span className="flex items-center gap-1.5 text-amber-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <span>Medium</span>
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                  <span>Anomalous</span>
                </span>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gradNormal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="gradMedium" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="gradAnomalous" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.6} />
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#16233B" />
                  <XAxis dataKey="hour" stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#070D1A', borderColor: '#1E3050', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                  />
                  <Area type="monotone" dataKey="normal" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#gradNormal)" name="Normal" />
                  <Area type="monotone" dataKey="medium" stroke="#F59E0B" strokeWidth={2} fillOpacity={1} fill="url(#gradMedium)" name="Medium" />
                  <Area type="monotone" dataKey="anomalous" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#gradAnomalous)" name="Anomalous" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CyberCard>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 3-Category Distribution Chart (1 Col) */}
            <CyberCard className="p-5" glow="cyan">
              <div className="flex items-center justify-between pb-3 border-b border-[#1E3050]/60 mb-4">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Category Volume Breakdown</h3>
                  <p className="text-[11px] text-slate-400">Total events per risk band</p>
                </div>
              </div>

              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryRatioData} layout="vertical" margin={{ left: 15, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#16233B" horizontal={false} />
                    <XAxis type="number" stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                    <YAxis dataKey="name" type="category" stroke="#64748B" tick={{ fontSize: 11, fill: '#E2E8F0' }} width={90} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#070D1A', borderColor: '#1E3050', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                      formatter={(val: any, name: any, item: any) => [`${val.toLocaleString()} (${item.payload.percent}%)`, 'Events']}
                    />
                    <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                      {categoryRatioData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CyberCard>

            {/* Recent Activity Feed Table (2 Cols) */}
            <CyberCard className="lg:col-span-2 p-5 overflow-hidden" glow="cyan">
              <div className="flex items-center justify-between pb-3 border-b border-[#1E3050]/60 mb-3">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Live Threat Analysis Feed</h3>
                  <p className="text-[11px] text-slate-400">Recent server log classifications</p>
                </div>
                <button
                  onClick={() => onNavigate('history')}
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1 transition-colors cursor-pointer"
                >
                  <span>Full Audit History</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#070D1A]/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1E3050]/60">
                    <tr>
                      <th className="p-2.5">Timestamp</th>
                      <th className="p-2.5">Classification</th>
                      <th className="p-2.5">Risk Score</th>
                      <th className="p-2.5">Model</th>
                      <th className="p-2.5">Log Record Content</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1E3050]/50 text-slate-300">
                    {stats.recent_activity.map((item) => (
                      <tr key={item.id} className="hover:bg-[#121E36]/40 transition-colors">
                        <td className="p-2.5 text-slate-400 whitespace-nowrap">{item.timestamp.substring(0, 19)}</td>
                        <td className="p-2.5 whitespace-nowrap">
                          <StatusBadge status={(item.category || (item.is_anomaly ? 'anomalous' : 'normal')).toLowerCase()} size="sm" />
                        </td>
                        <td className="p-2.5 font-bold text-white whitespace-nowrap">
                          {item.risk_score !== null && item.risk_score !== undefined
                            ? `${(item.risk_score * 100).toFixed(1)}%`
                            : item.probability !== null && item.probability !== undefined
                            ? `${(item.probability * 100).toFixed(1)}%`
                            : '-'}
                        </td>
                        <td className="p-2.5 text-slate-400 whitespace-nowrap">{item.model_name || 'N/A'}</td>
                        <td className="p-2.5 text-slate-300 max-w-xs truncate" title={item.raw_log}>
                          {item.raw_log}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CyberCard>
          </div>
        </div>
      )}
    </div>
  );
};
