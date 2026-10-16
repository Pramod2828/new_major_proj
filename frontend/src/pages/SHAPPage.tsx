import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  RefreshCw,
  Sliders,
  ArrowRight,
  BarChart2
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { api } from '../services/api';
import { Model, PredictionRecord } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';

export const SHAPPage: React.FC<{ onNavigate: (tab: string) => void }> = ({ onNavigate }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [globalShap, setGlobalShap] = useState<any | null>(null);
  const [recentPredictions, setRecentPredictions] = useState<PredictionRecord[]>([]);
  const [selectedPred, setSelectedPred] = useState<PredictionRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const mList = await api.listModels();
      setModels(mList);

      const active = mList.find((m: any) => m.is_active);
      const chosenId = active ? active.id : (mList.length > 0 ? mList[0].id : '');
      setSelectedModelId(chosenId);

      if (chosenId) {
        const gShap = await api.getModelGlobalShap(chosenId);
        setGlobalShap(gShap);
      }

      const hist = await api.getHistory({ limit: 10 });
      setRecentPredictions(hist.records || []);
      if (hist.records && hist.records.length > 0) {
        const detail = await api.getPredictionDetail(hist.records[0].id);
        setSelectedPred(detail);
      }
    } catch {
      // Keep state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleModelChange = async (mid: string) => {
    setSelectedModelId(mid);
    try {
      const gShap = await api.getModelGlobalShap(mid);
      setGlobalShap(gShap);
    } catch {
      setGlobalShap(null);
    }
  };

  const handleSelectPrediction = async (predId: string) => {
    try {
      const detail = await api.getPredictionDetail(predId);
      setSelectedPred(detail);
    } catch {
      // Keep
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-80 text-slate-400 gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
        <span className="font-mono text-xs tracking-wider uppercase text-cyan-300">Loading SHAP Attribution Engine...</span>
      </div>
    );
  }

  const importanceChartData = globalShap?.native_importances
    ? Object.entries(globalShap.native_importances).map(([k, v]) => ({
        feature: k,
        importance: Number(v),
      })).sort((a, b) => b.importance - a.importance).slice(0, 10)
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="SHAP Model Explainability Engine"
        subtitle="Game-theoretic feature attributions via TreeExplainer explaining exactly why models flagged anomalous logs"
        badge="TreeExplainer"
      />

      {/* Explainability Notice */}
      <CyberCard className="p-4" glow="cyan" hoverEffect={false}>
        <div className="flex items-center gap-3 text-xs text-slate-300 font-sans">
          <HelpCircle className="w-5 h-5 text-cyan-400 shrink-0" />
          <span>
            <strong className="text-white font-mono">Attribution Policy:</strong> SHAP values explain the internal mathematical decision boundaries of the trained tree ensembles. They illuminate which features pushed the prediction score towards Anomaly versus Normal.
          </span>
        </div>
      </CyberCard>

      {models.length === 0 ? (
        <EmptyState
          icon={Sliders}
          title="No Models Available for Attribution"
          description="SHAP feature attribution requires a trained Random Forest or XGBoost model. Once trained, feature contributions are automatically calculated."
          actionText="Go to Training Center"
          onAction={() => onNavigate('training')}
        />
      ) : (
        <div className="space-y-6">
          {/* Global Feature Importance Section */}
          <CyberCard className="p-6" glow="cyan" hoverEffect={false}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1E3050]/60 pb-4 mb-4">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Global Feature Importance Ranking
                </h3>
                <p className="text-[11px] text-slate-400">
                  Relative weight of features across the decision tree ensemble
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-mono">Model:</span>
                <select
                  value={selectedModelId}
                  onChange={(e) => handleModelChange(e.target.value)}
                  className="bg-[#070D1A] border border-[#1E3050] rounded-xl px-3 py-1.5 text-xs text-white font-mono"
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.algorithm.toUpperCase()}) {m.is_active ? '★ ACTIVE' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {importanceChartData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={importanceChartData} layout="vertical" margin={{ left: 80, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#16233B" horizontal={false} />
                    <XAxis type="number" stroke="#64748B" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                    <YAxis
                      dataKey="feature"
                      type="category"
                      stroke="#64748B"
                      tick={{ fontSize: 11, fill: '#E2E8F0' }}
                      width={100}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#070D1A', borderColor: '#1E3050', borderRadius: '8px', fontSize: '11px' }}
                      formatter={(val: any) => [`${(Number(val) * 100).toFixed(2)}%`, 'Weight']}
                    />
                    <Bar dataKey="importance" fill="#06B6D4" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500 font-mono">
                Feature importance data initialized upon training.
              </div>
            )}
          </CyberCard>

          {/* Instance Attribution Section */}
          <CyberCard className="p-6" glow="cyan" hoverEffect={false}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1E3050]/60 pb-4 mb-4">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Per-Prediction SHAP Attribution Breakdown
                </h3>
                <p className="text-[11px] text-slate-400">
                  Feature contributions pushing this specific log event towards Anomaly (+) vs Normal (-)
                </p>
              </div>

              {recentPredictions.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-mono">Audit Record:</span>
                  <select
                    value={selectedPred?.id || ''}
                    onChange={(e) => handleSelectPrediction(e.target.value)}
                    className="bg-[#070D1A] border border-[#1E3050] rounded-xl px-3 py-1.5 text-xs text-white font-mono max-w-[220px] truncate"
                  >
                    {recentPredictions.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.is_anomaly ? '⚠ ANOMALY' : '✓ NORMAL'} - {p.id.substring(0, 8)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {!selectedPred ? (
              <div className="p-8 text-center text-xs text-slate-500 font-mono">
                No past predictions stored. Execute live logs in Live Log Analysis to inspect per-record attributions.
              </div>
            ) : (
              <div className="space-y-4">
                {/* Record Info Box */}
                <div className="p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Record ID: {selectedPred.id}</span>
                    <StatusBadge status={selectedPred.is_anomaly ? 'anomaly' : 'normal'} size="sm" />
                  </div>
                  <div className="text-xs font-mono text-cyan-200 break-words">
                    {selectedPred.raw_log}
                  </div>
                </div>

                {/* Impact Bars */}
                {selectedPred.shap?.available && selectedPred.shap.contributions.length > 0 ? (
                  <div className="space-y-2.5 font-mono">
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>Feature</span>
                      <div className="flex items-center gap-4">
                        <span className="text-rose-400 flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-rose-500" /> Positive (+ Anomaly)
                        </span>
                        <span className="text-cyan-400 flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-cyan-500" /> Negative (- Normal)
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      {selectedPred.shap.contributions.map((c, i) => {
                        const isPushingAnomaly = c.direction === 'anomaly';
                        return (
                          <div
                            key={i}
                            className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050] flex items-center justify-between text-xs"
                          >
                            <div>
                              <div className="font-bold text-white text-[11px]">{c.feature}</div>
                              <div className="text-[10px] text-slate-500">Value: {String(c.feature_value)}</div>
                            </div>
                            <div className="text-right">
                              <span className={`font-bold text-xs ${isPushingAnomaly ? 'text-rose-400' : 'text-cyan-400'}`}>
                                {c.contribution > 0 ? `+${c.contribution}` : c.contribution}
                              </span>
                              <div className="text-[10px] text-slate-500">
                                {isPushingAnomaly ? 'Pushes toward ANOMALY' : 'Pushes toward NORMAL'}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-[#070D1A] text-center text-xs text-slate-400 font-mono">
                    SHAP explanation was not computed for this record.
                  </div>
                )}
              </div>
            )}
          </CyberCard>
        </div>
      )}
    </div>
  );
};
