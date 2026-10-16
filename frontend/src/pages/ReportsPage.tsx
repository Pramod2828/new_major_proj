import React, { useState, useEffect } from 'react';
import {
  Download,
  FileText,
  RefreshCw,
  Table,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardStats, Model } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';

export const ReportsPage: React.FC<{ onNavigate: (tab: string) => void }> = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activeModel, setActiveModel] = useState<Model | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [downloadingCsv, setDownloadingCsv] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const s = await api.getDashboardStats();
      setStats(s);
      const m = await api.getActiveModel();
      if (m.active) {
        setActiveModel(m.model);
      } else {
        setActiveModel(null);
      }
    } catch {
      setStats(null);
      setActiveModel(null);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      window.open(api.getPdfReportUrl(), '_blank');
    } finally {
      setTimeout(() => setDownloadingPdf(false), 1500);
    }
  };

  const handleDownloadCsv = async () => {
    setDownloadingCsv(true);
    try {
      window.open(api.getCsvReportUrl(), '_blank');
    } finally {
      setTimeout(() => setDownloadingCsv(false), 1500);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Security Audit Reports & Data Export"
        subtitle="Export genuine audit telemetry and model validation metrics to executive PDF or raw tabular CSV format"
        badge="Reporting Engine"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* PDF Executive Report Card */}
        <CyberCard className="p-6 md:p-8 flex flex-col justify-between space-y-6" glow="cyan">
          <div>
            <div className="w-12 h-12 rounded-2xl bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(6,182,212,0.3)]">
              <FileText className="w-6 h-6" />
            </div>

            <h3 className="font-extrabold text-base text-white tracking-wide">
              Executive Anomaly Audit (PDF)
            </h3>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Official cybersecurity audit report containing executive summary metrics, active classifier evaluation parameters (Accuracy, Precision, Recall, F1, FPR), confusion matrix verification, and full incident breakdowns of top flagged outliers.
            </p>

            <div className="mt-5 p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] text-xs font-mono space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Active Model:</span>
                <span className="text-cyan-300 font-bold">{activeModel ? activeModel.name : 'None Activated'}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Audited Scope:</span>
                <span className="text-white font-bold">{stats ? stats.total_logs : 0} syslogs</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Normal Events:</span>
                <span className="text-emerald-400 font-bold">{stats ? stats.normal_count : 0} ({stats ? stats.normal_percentage : 0}%)</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Medium-Risk Events:</span>
                <span className="text-amber-400 font-bold">{stats ? stats.medium_count : 0} ({stats ? stats.medium_percentage : 0}%)</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Anomalous Events:</span>
                <span className="text-rose-400 font-bold">{stats ? stats.anomalous_count : 0} ({stats ? stats.anomalous_percentage : 0}%)</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all cursor-pointer"
          >
            {downloadingPdf ? <RefreshCw className="w-4 h-4 animate-spin text-cyan-200" /> : <Download className="w-4 h-4" />}
            <span>Download Executive Report (PDF)</span>
          </button>
        </CyberCard>

        {/* CSV Telemetry Export Card */}
        <CyberCard className="p-6 md:p-8 flex flex-col justify-between space-y-6" glow="cyan">
          <div>
            <div className="w-12 h-12 rounded-2xl bg-blue-950/80 border border-blue-500/40 text-blue-400 flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
              <Table className="w-6 h-6" />
            </div>

            <h3 className="font-extrabold text-base text-white tracking-wide">
              Raw Prediction Telemetry (CSV)
            </h3>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Complete tabular export of all stored predictions. Includes unique prediction UUIDs, timestamps, classification labels (0=Normal, 1=Anomaly), anomaly probability scores, parsed hostnames, services, severity levels, and raw syslog text.
            </p>

            <div className="mt-5 p-4 rounded-xl bg-[#070D1A] border border-[#1E3050] text-xs font-mono space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Format Standard:</span>
                <span className="text-white font-bold">RFC 4180 CSV</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Database Source:</span>
                <span className="text-white font-bold">SQLite `predictions` table</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Row Limit:</span>
                <span className="text-white font-bold">Up to 1,000 records</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleDownloadCsv}
            disabled={downloadingCsv}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all cursor-pointer"
          >
            {downloadingCsv ? <RefreshCw className="w-4 h-4 animate-spin text-blue-200" /> : <Download className="w-4 h-4" />}
            <span>Export Raw Telemetry (CSV)</span>
          </button>
        </CyberCard>
      </div>
    </div>
  );
};
