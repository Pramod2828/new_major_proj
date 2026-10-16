import React, { useState, useEffect } from 'react';
import {
  Layers,
  Search,
  Filter,
  RefreshCw,
  Eye,
  X,
  ArrowRight,
  Clock,
  ShieldAlert,
  FileText,
  Cpu,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { PredictionRecord } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { AnimatedCounter } from '../components/common/AnimatedCounter';
import { EmptyState } from '../components/common/EmptyState';

export const HistoryPage: React.FC<{ onNavigate: (tab: string) => void }> = ({ onNavigate }) => {
  const [records, setRecords] = useState<PredictionRecord[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [normalCount, setNormalCount] = useState<number>(0);
  const [mediumCount, setMediumCount] = useState<number>(0);
  const [anomalousCount, setAnomalousCount] = useState<number>(0);
  const [unclassifiedCount, setUnclassifiedCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('all');
  const [selectedRecord, setSelectedRecord] = useState<PredictionRecord | null>(null);
  const [activeModalTab, setActiveModalTab] = useState<'facts' | 'model' | 'security'>('facts');

  const loadHistory = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (filterCategory !== 'all') params.category = filterCategory;
      if (timeRange !== 'all') params.time_range = timeRange;

      const data = await api.getHistory(params);
      setRecords(data.records || []);
      setTotal(data.total || 0);
      setNormalCount(data.normal_count || 0);
      setMediumCount(data.medium_count || 0);
      setAnomalousCount(data.anomalous_count || 0);
      setUnclassifiedCount(data.unclassified_count || 0);
    } catch {
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [filterCategory, timeRange]);

  const handleOpenDetail = async (id: string) => {
    try {
      const detail = await api.getPredictionDetail(id);
      setSelectedRecord(detail);
      setActiveModalTab('facts');
    } catch {
      // Keep
    }
  };

  const filteredRecords = records.filter((r) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      r.raw_log.toLowerCase().includes(term) ||
      (r.model_name && r.model_name.toLowerCase().includes(term)) ||
      (r.id && r.id.toLowerCase().includes(term)) ||
      (r.category && r.category.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit & Anomaly Prediction History"
        subtitle="Chronological audit records of all processed server logs across Normal, Medium, and Anomalous risk bands"
        badge="Audit Trail"
        actions={
          <button
            onClick={loadHistory}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#070D1A] border border-[#1E3050] hover:border-cyan-500/40 text-xs font-mono text-slate-300 hover:text-white transition-all cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh History</span>
          </button>
        }
      />

      {/* Metric Telemetry Row: 4 Separate Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono">
        <CyberCard className="p-4" glow="cyan">
          <div className="text-[11px] text-slate-400 uppercase tracking-wider">Total Audited Events</div>
          <div className="text-2xl font-extrabold text-white mt-1">
            <AnimatedCounter value={total} />
          </div>
        </CyberCard>
        <CyberCard className="p-4" glow="emerald">
          <div className="text-[11px] text-emerald-400 uppercase tracking-wider">Normal Events</div>
          <div className="text-2xl font-extrabold text-emerald-400 mt-1">
            <AnimatedCounter value={normalCount} />
          </div>
        </CyberCard>
        <CyberCard className="p-4" glow="amber">
          <div className="text-[11px] text-amber-400 uppercase tracking-wider">Medium-Risk Events</div>
          <div className="text-2xl font-extrabold text-amber-400 mt-1">
            <AnimatedCounter value={mediumCount} />
          </div>
        </CyberCard>
        <CyberCard className="p-4" glow="rose">
          <div className="text-[11px] text-rose-400 uppercase tracking-wider">Anomalous Events</div>
          <div className="text-2xl font-extrabold text-rose-400 mt-1">
            <AnimatedCounter value={anomalousCount} />
          </div>
        </CyberCard>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        <div className="relative w-full lg:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search logs, model names, IDs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#070D1A] border border-[#1E3050] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono shadow-inner"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          {/* Time range buttons */}
          <div className="flex items-center gap-1 bg-[#070D1A] border border-[#1E3050] p-1 rounded-xl">
            <Clock className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            {[
              { label: '24h', val: '24h' },
              { label: '7d', val: '7d' },
              { label: '30d', val: '30d' },
              { label: 'All', val: 'all' },
            ].map((t) => (
              <button
                key={t.val}
                onClick={() => setTimeRange(t.val)}
                className={`px-2 py-1 rounded-lg transition-colors cursor-pointer text-[11px] ${
                  timeRange === t.val ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Category buttons */}
          <div className="flex items-center gap-1 bg-[#070D1A] border border-[#1E3050] p-1 rounded-xl">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            {[
              { label: 'All', val: 'all', color: 'bg-cyan-600' },
              { label: 'Normal', val: 'Normal', color: 'bg-emerald-600' },
              { label: 'Medium', val: 'Medium', color: 'bg-amber-600' },
              { label: 'Anomalous', val: 'Anomalous', color: 'bg-rose-600' },
              { label: 'Unclassified', val: 'Unclassified', color: 'bg-slate-600' },
            ].map((c) => (
              <button
                key={c.val}
                onClick={() => setFilterCategory(c.val)}
                className={`px-2 py-1 rounded-lg transition-colors cursor-pointer text-[11px] ${
                  filterCategory === c.val ? `${c.color} text-white font-bold` : 'text-slate-400 hover:text-white'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table / Empty State */}
      {loading ? (
        <div className="p-12 text-center text-xs font-mono text-slate-400 flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
          <span>Querying SQLite audit database...</span>
        </div>
      ) : filteredRecords.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No Historical Events Found"
          description="Historical anomaly records will appear here once you process raw syslogs using an activated model."
          actionText="Go to Live Log Analysis"
          onAction={() => onNavigate('analysis')}
        />
      ) : (
        <CyberCard className="overflow-hidden p-0" glow="cyan" hoverEffect={false}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#070D1A] text-slate-400 uppercase text-[10px] border-b border-[#1E3050]">
                <tr>
                  <th className="p-3">Audit Timestamp</th>
                  <th className="p-3">Classification</th>
                  <th className="p-3">Risk / Conf</th>
                  <th className="p-3">Model</th>
                  <th className="p-3">Explanation Summary</th>
                  <th className="p-3">Raw Log Snippet</th>
                  <th className="p-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E3050]/60 text-slate-300">
                {filteredRecords.map((r) => {
                  const cat = r.category || (r.is_anomaly ? 'Anomalous' : 'Normal');
                  const riskStr = r.risk_score !== null && r.risk_score !== undefined
                    ? `${(r.risk_score * 100).toFixed(1)}%`
                    : r.probability !== null && r.probability !== undefined
                    ? `${(r.probability * 100).toFixed(1)}%`
                    : '-';

                  return (
                    <tr key={r.id} className="hover:bg-[#121E36]/40 transition-colors">
                      <td className="p-3 text-slate-400 whitespace-nowrap text-[11px]">{r.timestamp.substring(0, 19)}</td>
                      <td className="p-3 whitespace-nowrap">
                        <StatusBadge status={cat.toLowerCase()} size="sm" />
                      </td>
                      <td className="p-3 font-extrabold text-white whitespace-nowrap">
                        {riskStr}
                      </td>
                      <td className="p-3 text-slate-400 whitespace-nowrap">
                        {r.model_name || 'N/A'} (v{r.model_version || '1.0'})
                      </td>
                      <td className="p-3 text-slate-300 max-w-xs truncate" title={r.explanation_summary || ''}>
                        {r.explanation_summary || '-'}
                      </td>
                      <td className="p-3 text-slate-400 max-w-xs truncate" title={r.raw_log}>
                        {r.raw_log}
                      </td>
                      <td className="p-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => handleOpenDetail(r.id)}
                          className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-cyan-500/30 hover:border-cyan-400 text-cyan-300 text-[11px] inline-flex items-center gap-1 transition-all cursor-pointer"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CyberCard>
      )}

      {/* Record Modal with 3 Distinct Sections */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <CyberCard className="max-w-3xl w-full p-6 space-y-4 max-h-[92vh] overflow-y-auto" glow="cyan" hoverEffect={false}>
            <div className="flex items-center justify-between border-b border-[#1E3050]/80 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-sm text-white">Record Audit Inspection</h3>
                  <StatusBadge status={(selectedRecord.category || 'unclassified').toLowerCase()} size="md" />
                </div>
                <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                  ID: {selectedRecord.id} • {selectedRecord.timestamp}
                  {selectedRecord.risk_score !== null && selectedRecord.risk_score !== undefined && (
                    <span className="ml-2 text-cyan-300 font-bold">
                      Risk Score: {(selectedRecord.risk_score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#121E36] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-[#050811] border border-[#1E3050]">
              <div className="text-[10px] text-slate-500 uppercase font-mono mb-1">Raw Syslog Record</div>
              <div className="text-xs font-mono text-cyan-200 break-words">{selectedRecord.raw_log}</div>
            </div>

            {/* 3 Section Tabs */}
            <div className="flex items-center gap-2 border-b border-[#1E3050]/80 pb-2 text-xs font-mono">
              <button
                onClick={() => setActiveModalTab('facts')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeModalTab === 'facts'
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'text-slate-400 hover:text-white bg-[#070D1A]'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>1. Observed Facts</span>
              </button>

              <button
                onClick={() => setActiveModalTab('model')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeModalTab === 'model'
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'text-slate-400 hover:text-white bg-[#070D1A]'
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>2. Model Explanations & SHAP</span>
              </button>

              <button
                onClick={() => setActiveModalTab('security')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeModalTab === 'security'
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'text-slate-400 hover:text-white bg-[#070D1A]'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>3. Security Interpretation</span>
              </button>
            </div>

            {/* TAB 1: Facts */}
            {activeModalTab === 'facts' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="text-[11px] font-bold text-cyan-300 uppercase">Extracted Features & Fields</div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    {Object.entries(selectedRecord.features || selectedRecord.observed_facts || {}).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-[#1E3050]/60 pb-1">
                        <span className="text-slate-400">{k}:</span>
                        <span className="text-white font-semibold">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Model Explanations */}
            {activeModalTab === 'model' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="text-[11px] font-bold text-cyan-300 uppercase">Classification Policy Rationale</div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    {selectedRecord.model_explanation?.decision_rationale || selectedRecord.explanation_summary || 'Evaluated against policy thresholds.'}
                  </p>
                </div>

                {selectedRecord.shap?.available && (
                  <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Top SHAP Attributions</div>
                    <div className="space-y-1.5 font-mono text-xs">
                      {selectedRecord.shap.contributions.slice(0, 8).map((c, i) => (
                        <div key={i} className="flex items-center justify-between">
                          <span className="text-slate-300 text-[11px]">{c.feature}</span>
                          <span className={`text-[11px] font-bold ${c.direction === 'anomaly' ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {c.contribution > 0 ? `+${c.contribution}` : c.contribution} ({c.direction})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: Security Interpretation */}
            {activeModalTab === 'security' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="flex items-center gap-2 text-cyan-300 font-bold text-xs uppercase">
                    <ShieldAlert className="w-4 h-4 text-cyan-400" />
                    <span>Operational Context</span>
                  </div>
                  <p className="text-slate-200 text-xs leading-relaxed">
                    {selectedRecord.security_interpretation || 'Baseline behavioral observation.'}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 text-[10px]">
                  <b>Investigation Guidance:</b> Anomaly score reflects statistical divergence from models. Verify surrounding connection session records prior to blocking.
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-2 rounded-xl bg-[#121E36] hover:bg-[#182848] text-xs font-mono text-white transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </CyberCard>
        </div>
      )}
    </div>
  );
};
