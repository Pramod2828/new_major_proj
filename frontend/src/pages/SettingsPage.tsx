import React, { useState, useEffect } from 'react';
import {
  Server,
  Database,
  Cpu,
  RefreshCw,
  BookOpen,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';

export const SettingsPage: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<any | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchStatus = async () => {
    try {
      setRefreshing(true);
      const data = await api.getSystemStatus();
      setSystemStatus(data);
    } catch {
      setSystemStatus(null);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Status & Integration Settings"
        subtitle="Host telemetry, SQLite persistent storage statistics, and dataset onboarding protocol"
        badge="Environment Status"
        actions={
          <button
            onClick={fetchStatus}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#070D1A] border border-[#1E3050] hover:border-cyan-500/40 text-xs font-mono text-slate-300 hover:text-white transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Refresh Telemetry</span>
          </button>
        }
      />

      {/* Hardware & Storage Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Host Hardware */}
        <CyberCard className="p-5 space-y-4" glow="cyan" hoverEffect={false}>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span className="font-bold uppercase tracking-wider text-white">Host Hardware Telemetry</span>
            <Server className="w-4 h-4 text-cyan-400" />
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>CPU Utilization:</span>
                <span className="text-cyan-400 font-bold">{systemStatus?.system_resources?.cpu_usage_percent ?? 0}%</span>
              </div>
              <div className="w-full bg-[#070D1A] h-2 rounded-full overflow-hidden border border-[#1E3050]">
                <div
                  className="bg-cyan-500 h-full rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                  style={{ width: `${Math.min(systemStatus?.system_resources?.cpu_usage_percent ?? 0, 100)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>RAM Utilization:</span>
                <span className="text-blue-400 font-bold">{systemStatus?.system_resources?.memory_usage_percent ?? 0}%</span>
              </div>
              <div className="w-full bg-[#070D1A] h-2 rounded-full overflow-hidden border border-[#1E3050]">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                  style={{ width: `${Math.min(systemStatus?.system_resources?.memory_usage_percent ?? 0, 100)}%` }}
                />
              </div>
            </div>

            <div className="flex justify-between pt-1 text-slate-400 border-t border-[#1E3050]/60">
              <span>RAM Available:</span>
              <span className="text-white font-bold">{systemStatus?.system_resources?.memory_available_mb ?? 'N/A'} MB</span>
            </div>
          </div>
        </CyberCard>

        {/* SQLite Storage */}
        <CyberCard className="p-5 space-y-4" glow="cyan" hoverEffect={false}>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span className="font-bold uppercase tracking-wider text-white">SQLite Storage Stats</span>
            <Database className="w-4 h-4 text-blue-400" />
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="flex justify-between p-2 rounded-lg bg-[#070D1A] border border-[#1E3050]">
              <span className="text-slate-400">Datasets Ingested:</span>
              <span className="text-white font-bold">{systemStatus?.counts?.datasets ?? 0}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-[#070D1A] border border-[#1E3050]">
              <span className="text-slate-400">Model Artifacts:</span>
              <span className="text-white font-bold">{systemStatus?.counts?.models ?? 0}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-[#070D1A] border border-[#1E3050]">
              <span className="text-slate-400">Audited Predictions:</span>
              <span className="text-cyan-400 font-bold">{systemStatus?.counts?.total_predictions ?? 0}</span>
            </div>
          </div>
        </CyberCard>

        {/* Active Production Classifier */}
        <CyberCard className="p-5 space-y-4" glow="emerald" hoverEffect={false}>
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span className="font-bold uppercase tracking-wider text-white">Active Production Model</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            {systemStatus?.active_model ? (
              <>
                <div className="p-2 rounded-lg bg-[#070D1A] border border-[#1E3050] flex justify-between">
                  <span className="text-slate-400">Model Name:</span>
                  <span className="text-cyan-300 font-bold">{systemStatus.active_model.name}</span>
                </div>
                <div className="p-2 rounded-lg bg-[#070D1A] border border-[#1E3050] flex justify-between">
                  <span className="text-slate-400">Algorithm:</span>
                  <span className="text-white font-bold">{systemStatus.active_model.algorithm.toUpperCase()}</span>
                </div>
                <div className="p-2 rounded-lg bg-[#070D1A] border border-[#1E3050] flex justify-between">
                  <span className="text-slate-400">Version:</span>
                  <span className="text-emerald-400 font-bold">v{systemStatus.active_model.version}</span>
                </div>
              </>
            ) : (
              <div className="p-6 rounded-lg bg-[#070D1A] border border-amber-500/30 text-amber-300 text-center font-mono text-xs">
                No Active Model Configured
              </div>
            )}
          </div>
        </CyberCard>
      </div>

      {/* Dataset Integration Protocol Guide */}
      <CyberCard className="p-6 md:p-8 space-y-4" glow="none" hoverEffect={false}>
        <div className="flex items-center gap-2.5 border-b border-[#1E3050]/60 pb-3">
          <BookOpen className="w-5 h-5 text-cyan-400" />
          <h3 className="font-extrabold text-sm text-white uppercase tracking-wider font-mono">
            Dataset Integration Protocol (When Final Dataset is Provided)
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-sans text-slate-300 leading-relaxed">
          <div className="p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
            <div className="font-bold text-cyan-400 flex items-center gap-1.5 font-mono">
              <span>1. Supported Formats</span>
            </div>
            <p className="text-slate-400 text-xs">
              Upload any security log dataset in CSV, JSON (records array or object), or JSONL (line-delimited JSON). Standard UTF-8 or Latin-1 encoding with header row included.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
            <div className="font-bold text-blue-400 flex items-center gap-1.5 font-mono">
              <span>2. Label & Feature Mapping</span>
            </div>
            <p className="text-slate-400 text-xs">
              In Dataset Manager, choose the ground-truth target column. Map which string value denotes "Normal" (0) and "Anomaly" (1). The target column is automatically excluded from features to prevent leakage.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
            <div className="font-bold text-emerald-400 flex items-center gap-1.5 font-mono">
              <span>3. Validation & Approval</span>
            </div>
            <p className="text-slate-400 text-xs">
              Run Schema Validation to mathematically verify class representation, missing values, and split bounds. Once validated, click "Approve for Training" to unlock the Training Center.
            </p>
          </div>
        </div>
      </CyberCard>
    </div>
  );
};
