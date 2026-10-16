import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Zap,
  BarChart2
} from 'lucide-react';
import { api } from '../services/api';
import { Model } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';

export const ModelsPage: React.FC<{ onNavigate: (tab: string) => void }> = ({ onNavigate }) => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activatingId, setActivatingId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadModels = async () => {
    try {
      setLoading(true);
      const data = await api.listModels();
      setModels(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch models');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  const handleActivate = async (id: string) => {
    try {
      setActivatingId(id);
      setErrorMsg(null);
      setSuccessMsg(null);
      await api.activateModel(id);
      setSuccessMsg(`Model successfully activated for live production inference!`);
      await loadModels();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to activate model');
    } finally {
      setActivatingId(null);
    }
  };

  // Comparison state
  const [comparisonData, setComparisonData] = useState<any[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  const handleCompare = async () => {
    if (selectedIds.length < 2) {
      setErrorMsg('Select at least two models to compare.');
      return;
    }
    try {
      const data = await api.compareModels(selectedIds);
      setComparisonData(data.comparison || []);
      setShowComparison(true);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to compare models');
    }
  };

  const hasModels = models.length > 0;
  const anySelected = selectedIds.length > 0;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 text-slate-400 gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
        <span className="font-mono text-xs tracking-wider uppercase text-cyan-300">Loading Model Registry...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Model Registry & Evaluation Comparison"
        subtitle="Compare Random Forest and XGBoost classifiers evaluated on the identical held-out test split"
        badge="Model Registry"
        actions={
          <button
            onClick={loadModels}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#070D1A] border border-[#1E3050] hover:border-cyan-500/40 text-xs font-mono text-slate-300 hover:text-white transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Models</span>
          </button>
        }
      />

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {!hasModels ? (
        <EmptyState
          icon={Cpu}
          title="No Models Trained Yet"
          description="True performance metrics and confusion matrices will appear here once Random Forest and XGBoost classifiers are trained on an approved dataset."
          actionText="Go to Training Center"
          onAction={() => onNavigate('training')}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {models.map((m) => {
              const metrics = m.metrics || {};
              const cm = metrics.confusion_matrix || { tn: 0, fp: 0, fn: 0, tp: 0 };
              return (
                <CyberCard
                  key={m.id}
                  className={`p-6 flex flex-col justify-between ${
                    m.is_active ? 'border-cyan-400/80 bg-[#0E1A33] shadow-[0_0_30px_rgba(6,182,212,0.25)]' : ''
                  }`}
                  glow={m.is_active ? 'cyan' : 'none'}
                  hoverEffect={!m.is_active}
                >
                  <div>
                    {/* Card Header */}
                    <div className="flex items-center justify-between pb-4 border-b border-[#1E3050]/70 mb-5">
                      <div>
                        <div className="flex items-center gap-2.5">
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(m.id)}
                            onChange={() => toggleSelect(m.id)}
                            className="mr-2"
                          />
                          <span className="font-extrabold text-base text-white tracking-wide">{m.name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase bg-[#070D1A] text-cyan-400 border border-cyan-500/30">
                            {m.algorithm.toUpperCase()}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 font-mono mt-1">
                          Version v{m.version} • Training duration: {m.training_duration_seconds}s
                        </div>
                      </div>

                      <div>
                        {m.is_active ? (
                          <StatusBadge status="active" text="ACTIVE FOR INFERENCE" />
                        ) : (
                          <button
                            onClick={() => handleActivate(m.id)}
                            disabled={activatingId === m.id}
                            className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-mono font-semibold text-xs shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all cursor-pointer"
                          >
                            {activatingId === m.id ? 'Activating...' : 'Set as Active'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Primary Metric Badges */}
                    <div className="grid grid-cols-4 gap-2.5 mb-5 text-center font-mono">
                      <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <div className="text-[10px] text-slate-400 uppercase">Accuracy</div>
                        <div className="text-base font-extrabold text-white mt-0.5">
                          {metrics.accuracy != null ? `${(metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <div className="text-[10px] text-slate-400 uppercase">Precision</div>
                        <div className="text-base font-extrabold text-cyan-400 mt-0.5">
                          {metrics.precision != null ? `${(metrics.precision * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <div className="text-[10px] text-slate-400 uppercase">Recall</div>
                        <div className="text-base font-extrabold text-emerald-400 mt-0.5">
                          {metrics.recall != null ? `${(metrics.recall * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <div className="text-[10px] text-slate-400 uppercase">F1-Score</div>
                        <div className="text-base font-extrabold text-amber-400 mt-0.5">
                          {metrics.f1_score != null ? `${(metrics.f1_score * 100).toFixed(1)}%` : 'N/A'}
                        </div>
                      </div>
                    </div>

                    {/* Secondary Metrics */}
                    <div className="grid grid-cols-3 gap-2.5 text-xs font-mono mb-5">
                      <div className="p-2.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <span className="text-slate-400 text-[10px] uppercase block">ROC-AUC</span>
                        <span className="font-bold text-white text-sm">
                          {metrics.roc_auc !== null ? metrics.roc_auc : 'N/A'}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <span className="text-slate-400 text-[10px] uppercase block">PR-AUC</span>
                        <span className="font-bold text-white text-sm">
                          {metrics.pr_auc !== null ? metrics.pr_auc : 'N/A'}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                        <span className="text-slate-400 text-[10px] uppercase block">False Positive Rate</span>
                        <span className="font-bold text-rose-400 text-sm">
                          {metrics.false_positive_rate != null ? `${(metrics.false_positive_rate * 100).toFixed(2)}%` : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Confusion Matrix Table */}
                    <div className="p-4 rounded-xl bg-[#070D1A] border border-[#1E3050]">
                      <div className="text-[11px] font-bold text-slate-400 font-mono uppercase tracking-wider mb-2.5 flex items-center justify-between">
                        <span>Confusion Matrix (Held-out Test Split)</span>
                        <span className="text-cyan-400">{metrics.test_samples || 0} samples</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-center font-mono">
                        <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/40">
                          <div className="text-[10px] text-emerald-400">True Negatives (TN)</div>
                          <div className="text-lg font-extrabold text-emerald-300">{cm.tn}</div>
                        </div>
                        <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/40">
                          <div className="text-[10px] text-rose-400">False Positives (FP)</div>
                          <div className="text-lg font-extrabold text-rose-300">{cm.fp}</div>
                        </div>
                        <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/40">
                          <div className="text-[10px] text-rose-400">False Negatives (FN)</div>
                          <div className="text-lg font-extrabold text-rose-300">{cm.fn}</div>
                        </div>
                        <div className="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-500/40">
                          <div className="text-[10px] text-cyan-400">True Positives (TP)</div>
                          <div className="text-lg font-extrabold text-cyan-300">{cm.tp}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CyberCard>
              );
            })}
          </div>
          {anySelected && (
            <button onClick={handleCompare} className="mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded">
              Compare Selected Models
            </button>
          )}
          {showComparison && (
            <div className="mt-6">
              <h2 className="text-xl font-bold text-white mb-4">Model Comparison</h2>
              <table className="min-w-full bg-[#070D1A] border border-[#1E3050]">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-slate-400">Model</th>
                    <th className="px-4 py-2 text-left text-slate-400">Algorithm</th>
                    <th className="px-4 py-2 text-left text-slate-400">Accuracy</th>
                    <th className="px-4 py-2 text-left text-slate-400">Precision</th>
                    <th className="px-4 py-2 text-left text-slate-400">Recall</th>
                    <th className="px-4 py-2 text-left text-slate-400">F1 Score</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.map((c) => (
                    <tr key={c.id} className="border-t border-[#1E3050]/30">
                      <td className="px-4 py-2 text-white">{c.name}</td>
                      <td className="px-4 py-2 text-cyan-400">{c.algorithm}</td>
                      <td className="px-4 py-2 text-white">{c.accuracy != null ? `${(c.accuracy * 100).toFixed(1)}%` : 'N/A'}</td>
                      <td className="px-4 py-2 text-cyan-400">{c.precision != null ? `${(c.precision * 100).toFixed(1)}%` : 'N/A'}</td>
                      <td className="px-4 py-2 text-emerald-400">{c.recall != null ? `${(c.recall * 100).toFixed(1)}%` : 'N/A'}</td>
                      <td className="px-4 py-2 text-amber-400">{c.f1_score != null ? `${(c.f1_score * 100).toFixed(1)}%` : 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button onClick={() => setShowComparison(false)} className="mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded">
                Close
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
