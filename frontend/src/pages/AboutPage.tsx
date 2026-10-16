import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  Info,
  Layers,
  Cpu,
  BarChart2,
  Sliders,
  Database,
  Search,
  Download,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  HelpCircle,
  FileText,
  Activity,
  ArrowRight,
  Server,
  Zap,
  Terminal,
  Code2,
  Lock,
  GitBranch,
  ShieldCheck,
  ShieldAlert,
  Binary,
  Radio,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import { CyberCard } from '../components/common/CyberCard';
import { CyberShield3D } from '../components/common/CyberShield3D';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';

export const AboutPage: React.FC<{ onNavigate?: (tab: string) => void }> = ({ onNavigate }) => {
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.getSystemStatus();
        setSystemStatus(data);
      } catch {
        setSystemStatus(null);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  const activeModel = systemStatus?.active_model;
  const totalPreds = systemStatus?.counts?.total_predictions ?? 0;
  const datasetsCount = systemStatus?.counts?.datasets ?? 0;

  const techBadges = [
    { name: 'React 19', role: 'Frontend UI', color: 'border-cyan-500/40 text-cyan-300 bg-cyan-950/60' },
    { name: 'TypeScript', role: 'Type Safety', color: 'border-blue-500/40 text-blue-300 bg-blue-950/60' },
    { name: 'Vite 8', role: 'Build Tool', color: 'border-purple-500/40 text-purple-300 bg-purple-950/60' },
    { name: 'Tailwind CSS v4', role: 'Styling', color: 'border-sky-500/40 text-sky-300 bg-sky-950/60' },
    { name: 'Framer Motion', role: 'Animations', color: 'border-pink-500/40 text-pink-300 bg-pink-950/60' },
    { name: 'Python 3.11', role: 'Runtime', color: 'border-amber-500/40 text-amber-300 bg-amber-950/60' },
    { name: 'Flask REST API', role: 'Backend Server', color: 'border-emerald-500/40 text-emerald-300 bg-emerald-950/60' },
    { name: 'scikit-learn', role: 'Random Forest', color: 'border-orange-500/40 text-orange-300 bg-orange-950/60' },
    { name: 'XGBoost', role: 'Gradient Boosting', color: 'border-teal-500/40 text-teal-300 bg-teal-950/60' },
    { name: 'SHAP', role: 'Explainability', color: 'border-indigo-500/40 text-indigo-300 bg-indigo-950/60' },
    { name: 'SQLite', role: 'Persistence', color: 'border-slate-500/40 text-slate-300 bg-slate-900/60' },
    { name: 'Recharts', role: 'Visualizations', color: 'border-cyan-500/40 text-cyan-300 bg-cyan-950/60' },
  ];

  const objectives = [
    {
      num: '01',
      title: 'Import & Parse Syslogs',
      desc: 'Ingest raw server logs in standard RFC 3164 (BSD), RFC 5424 (IETF), ISO timestamps, or structured JSON formats with automated message and header token extraction.',
      icon: Terminal,
      color: 'cyan'
    },
    {
      num: '02',
      title: 'Prepare ML Features',
      desc: 'Derive numerical entropy, token metrics, keyword flags, and categorical encoders fitted strictly on training splits to prevent data leakage.',
      icon: Binary,
      color: 'blue'
    },
    {
      num: '03',
      title: 'Detect Abnormal Behavior',
      desc: 'Deploy trained Random Forest and XGBoost supervised classifiers to detect statistical anomalies and calculate continuous anomaly probability scores.',
      icon: Zap,
      color: 'violet'
    },
    {
      num: '04',
      title: 'Three-Level Categorization',
      desc: 'Apply a transparent, configurable decision policy mapping model probabilities into Normal (green), Medium (amber), and Anomalous (red) risk categories.',
      icon: ShieldAlert,
      color: 'amber'
    },
    {
      num: '05',
      title: 'Explain Predictions with SHAP',
      desc: 'Compute mathematical feature attributions via TreeExplainer, isolating top anomaly drivers and baseline operational contributors without black-box opacity.',
      icon: Sliders,
      color: 'pink'
    },
    {
      num: '06',
      title: 'Telemetry & Audit Reporting',
      desc: 'Visualize rolling 24-hour timelines, category volume breakdowns, and export comprehensive executive PDF reports and RFC 4180 CSV audit records.',
      icon: BarChart2,
      color: 'emerald'
    },
    {
      num: '07',
      title: 'Filterable Investigation Trail',
      desc: 'Provide an interactive live inspection terminal and historical audit log filterable by category, date range, source host, and keywords.',
      icon: Search,
      color: 'sky'
    }
  ];

  const workflowSteps = [
    { step: 1, title: 'Log Input', sub: 'RFC 3164 / 5424 / JSON', icon: FileText, color: 'text-cyan-400 border-cyan-500/40 bg-cyan-950/50' },
    { step: 2, title: 'Parsing', sub: 'Header & payload regex', icon: Terminal, color: 'text-blue-400 border-blue-500/40 bg-blue-950/50' },
    { step: 3, title: 'Data Cleaning', sub: 'Imputation & sanitization', icon: Database, color: 'text-indigo-400 border-indigo-500/40 bg-indigo-950/50' },
    { step: 4, title: 'Feature Extraction', sub: 'Entropy, tokens, flags', icon: Binary, color: 'text-violet-400 border-violet-500/40 bg-violet-950/50' },
    { step: 5, title: 'RF / XGBoost', sub: 'Supervised inference', icon: Cpu, color: 'text-purple-400 border-purple-500/40 bg-purple-950/50' },
    { step: 6, title: 'Classification Policy', sub: 'Normal / Medium / Anom', icon: Shield, color: 'text-amber-400 border-amber-500/40 bg-amber-950/50' },
    { step: 7, title: 'SHAP Explanation', sub: 'TreeExplainer attributions', icon: Sliders, color: 'text-rose-400 border-rose-500/40 bg-rose-950/50' },
    { step: 8, title: 'Dashboard & Reports', sub: '24h Timeline, PDF, CSV', icon: Activity, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/50' }
  ];

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="About Project: SMART-LOG"
        subtitle="Architecture, methodology, machine learning algorithms, and operational scope of the Smart-Log anomaly detection platform"
        badge="Platform Documentation"
      />

      {/* A. Hero Section */}
      <CyberCard className="p-6 md:p-10 overflow-hidden relative" glow="cyan" hoverEffect={false}>
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8 relative z-10">
          <div className="space-y-4 text-center lg:text-left max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>PROJECT OVERVIEW & SPECIFICATION</span>
            </div>

            <div className="space-y-2">
              <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight font-sans">
                SMART-LOG
              </h1>
              <h2 className="text-base md:text-lg font-semibold text-cyan-300 font-mono">
                Automated Syslog Anomaly Detection for Server Security
              </h2>
            </div>

            <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans">
              An intelligent security monitoring system that uses machine learning to identify unusual patterns in system logs and explain its predictions through transparent mathematical attributions.
            </p>

            {/* Technology Badges Row */}
            <div className="pt-2">
              <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider mb-2">Core Technology Stack:</div>
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-2">
                {['React 19', 'Flask REST API', 'Python 3.11', 'Random Forest', 'XGBoost', 'SHAP', 'SQLite'].map((t) => (
                  <span
                    key={t}
                    className="px-2.5 py-1 rounded-lg text-xs font-mono bg-[#070D1A] border border-cyan-500/30 text-cyan-200 shadow-sm"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* 3D Holographic Cyber Shield */}
          <div className="shrink-0 py-2">
            <CyberShield3D />
          </div>
        </div>
      </CyberCard>

      {/* B & C: Project Overview and Problem Statement */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* B. Project Overview */}
        <CyberCard className="p-6 space-y-3" glow="cyan">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-500/40 text-cyan-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider">Project Overview</h3>
              <p className="text-[11px] text-slate-400">System Purpose & Operating Model</p>
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans pt-1">
            Smart-Log is an enterprise security operations dashboard built to analyze system and server logs, identify abnormal behavioral patterns, classify events by risk level, and help administrators investigate potentially suspicious activity.
          </p>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            By combining high-speed log parsing with dual supervised classifiers and a calibrated policy decision layer, the system processes raw text streams into actionable risk assessments accompanied by per-feature evidence.
          </p>
        </CyberCard>

        {/* C. Problem Statement */}
        <CyberCard className="p-6 space-y-3" glow="amber">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-950/80 border border-amber-500/40 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider">Problem Statement</h3>
              <p className="text-[11px] text-slate-400">Challenges in Modern Log Auditing</p>
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans pt-1">
            Modern enterprise servers and containerized clusters generate millions of syslog messages daily. Manual inspection is time-consuming, error-prone, and unsustainable for security response teams.
          </p>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Critical unusual events—such as brute-force authentication spikes, privilege escalation attempts, or kernel memory crashes—are frequently obscured within routine noise. Smart-Log aims to help analyze these events more efficiently by surfacing anomalous events with interpretable model rationale.
          </p>
        </CyberCard>
      </div>

      {/* D. Project Objectives */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-cyan-400" />
              Project Objectives
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">Functional goals achieved across the platform</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {objectives.map((obj) => {
            const Icon = obj.icon;
            return (
              <CyberCard key={obj.num} className="p-4 space-y-2 flex flex-col justify-between" glow="cyan">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-cyan-400">{obj.num}</span>
                    <div className="p-1.5 rounded-lg bg-[#070D1A] border border-[#1E3050] text-cyan-300">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <h4 className="text-xs font-bold text-white font-sans">{obj.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed mt-1">{obj.desc}</p>
                </div>
              </CyberCard>
            );
          })}
        </div>
      </div>

      {/* E. Algorithms and Techniques */}
      <div className="space-y-4">
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Algorithms & Techniques
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">Supervised learning models, explainability engines, and policy layers</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* 1. Random Forest */}
          <CyberCard className="p-5 space-y-2.5" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
                ENSEMBLE LEARNING
              </span>
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">Random Forest Classifier</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Uses an ensemble of decision trees to classify events based on patterns learned from labeled training data. By aggregating multiple randomized trees, Random Forest minimizes overfitting, stabilizes predictions across noisy logs, and provides natural feature importance measures.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Implementation: <code className="text-cyan-300">sklearn.ensemble.RandomForestClassifier</code>
            </div>
          </CyberCard>

          {/* 2. XGBoost */}
          <CyberCard className="p-5 space-y-2.5" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950/80 border border-teal-500/40 text-teal-300">
                GRADIENT BOOSTING
              </span>
              <Zap className="w-4 h-4 text-teal-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">XGBoost Classifier</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Uses gradient-boosted decision trees for supervised classification and benchmark comparison with Random Forest. Iteratively optimizes residual errors with second-order gradient approximations, providing high accuracy on tabular log features.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Implementation: <code className="text-teal-300">xgboost.XGBClassifier</code>
            </div>
          </CyberCard>

          {/* 3. SHAP Explainability */}
          <CyberCard className="p-5 space-y-2.5" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-950/80 border border-violet-500/40 text-violet-300">
                MODEL EXPLAINABILITY
              </span>
              <Sliders className="w-4 h-4 text-violet-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">SHAP (TreeExplainer)</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Explains the contribution of input features to a model prediction when a compatible explainer is available. Computes game-theoretic Shapley values to identify whether specific properties (e.g., failed auth flags, message entropy) pushed the probability toward Anomaly or toward Normal.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Implementation: <code className="text-violet-300">shap.TreeExplainer</code>
            </div>
          </CyberCard>

          {/* 4. Three-Level Classification Policy */}
          <CyberCard className="p-5 space-y-2.5" glow="amber">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500/40 text-amber-300">
                DECISION LAYER
              </span>
              <ShieldAlert className="w-4 h-4 text-amber-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">Three-Level Classification Policy</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Uses a documented, configurable decision policy to assign Normal, Medium, or Anomalous categories. <strong>Medium is an intermediate risk band derived from policy thresholds (default [0.30, 0.70))</strong>, capturing borderline predictions and model uncertainty rather than being a native third class predicted by binary trees.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Module: <code className="text-amber-300">RiskClassificationPolicy</code>
            </div>
          </CyberCard>

          {/* 5. Log Parsing & Feature Engineering */}
          <CyberCard className="p-5 space-y-2.5 md:col-span-2 lg:col-span-2" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/80 border border-blue-500/40 text-blue-300">
                DATA ENGINEERING
              </span>
              <Terminal className="w-4 h-4 text-blue-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">Log Parsing & Feature Engineering</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Extracts useful structured fields and model-compatible numerical and categorical features from supported log records. Computes Shannon entropy on message characters, extracts source IP addresses and usernames, counts token volumes, and tags high-severity indicators. Features are scaled and one-hot encoded using a leak-free ColumnTransformer fitted exclusively on training splits.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Module: <code className="text-cyan-300">LogParser & PreprocessingBundle</code>
            </div>
          </CyberCard>
        </div>
      </div>

      {/* F. System Workflow Diagram (Interactive/Responsive CSS/SVG Flow) */}
      <CyberCard className="p-6 md:p-8 space-y-6" glow="cyan" hoverEffect={false}>
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-cyan-400" />
            System End-to-End Workflow
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">
            Pipeline from raw syslog ingestion to mathematical attribution and dashboard telemetry
          </p>
        </div>

        {/* Responsive Flex Flow Diagram */}
        <div className="relative">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            {workflowSteps.map((s, idx) => {
              const Icon = s.icon;
              return (
                <div key={s.step} className="flex flex-col items-center text-center relative group">
                  <div className={`w-full p-3.5 rounded-xl border ${s.color} transition-all duration-300 hover:scale-[1.03] shadow-md flex flex-col items-center justify-center min-h-[110px]`}>
                    <div className="w-7 h-7 rounded-lg bg-[#070D1A] flex items-center justify-center mb-2 shadow-inner">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="text-[11px] font-bold text-white font-mono">{s.title}</div>
                    <div className="text-[9px] text-slate-400 font-sans mt-0.5">{s.sub}</div>
                  </div>

                  {/* Step Connector Arrow (visible on large screens) */}
                  {idx < workflowSteps.length - 1 && (
                    <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-cyan-400/60 pointer-events-none">
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-4 p-3 rounded-xl bg-[#070D1A] border border-[#1E3050] text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>Pipeline Status: Sequential, leak-free, validated pre-training schema isolation.</span>
            </span>
            <span className="text-cyan-300 font-bold hidden sm:inline">8 Active Stages</span>
          </div>
        </div>
      </CyberCard>

      {/* G. Key Features */}
      <div className="space-y-4">
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            Key Platform Features
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">Core functional capabilities available in Smart-Log</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { title: 'Dataset Import & Validation', desc: 'Inspect CSV, JSON, and JSONL schemas, map target labels, verify binary class balance, and detect target leakage prior to training.', icon: Database },
            { title: 'Model Training & Comparison', desc: 'Train Random Forest and XGBoost classifiers with custom hyperparameters; compare Accuracy, Precision, Recall, F1, ROC-AUC, and FPR on identical test splits.', icon: BarChart2 },
            { title: 'Live Log Ingestion Terminal', desc: 'Ingest raw single logs or batch files; parse timestamps, hostnames, and service tags in real time with instant risk classification.', icon: Terminal },
            { title: 'Rolling 24-Hour Timeline', desc: 'Interactive Recharts multi-area timeline displaying hourly event frequencies segmented by Normal, Medium, and Anomalous risk bands.', icon: Clock },
            { title: 'Normal, Medium, Anomalous & Unclassified', desc: 'Four distinct status pills with pulsing radar indicators. Unclassified state ensures zero fabricated outputs when models lack confidence.', icon: ShieldAlert },
            { title: 'Per-Event SHAP Visualization', desc: 'Detailed modal with Observed Facts, Model Rationale, and waterfall feature impact charts (+ Anomaly vs - Normal).', icon: Sliders },
            { title: 'Anomaly History & Audit Log', desc: 'Persistent SQLite storage of all analyzed events; filterable by risk level, date range, model version, and text search.', icon: Layers },
            { title: 'Executive PDF & CSV Reports', desc: 'One-click ReportLab PDF security audit generation with metrics and incident tables, alongside RFC 4180 CSV tabular exports.', icon: Download },
            { title: 'Telemetry & Model Status Monitoring', desc: 'Live host CPU/RAM telemetry, active production model indicators, and database storage counters.', icon: Activity }
          ].map((f, i) => {
            const Icon = f.icon;
            return (
              <CyberCard key={i} className="p-4 space-y-2" glow="cyan">
                <div className="flex items-center gap-2 text-cyan-300 font-mono text-xs font-bold">
                  <Icon className="w-4 h-4 text-cyan-400" />
                  <span>{f.title}</span>
                </div>
                <p className="text-[11px] text-slate-300 font-sans leading-relaxed">{f.desc}</p>
              </CyberCard>
            );
          })}
        </div>
      </div>

      {/* H. Technology Stack Table */}
      <CyberCard className="p-6 space-y-4" glow="cyan">
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <Code2 className="w-4 h-4 text-cyan-400" />
            Verified Technology Stack
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">Actual packages, frameworks, and libraries installed and active in Smart-Log</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 font-mono">
          {techBadges.map((t, idx) => (
            <div key={idx} className={`p-3 rounded-xl border ${t.color} flex flex-col justify-between`}>
              <div className="font-bold text-xs">{t.name}</div>
              <div className="text-[10px] text-slate-400 mt-1">{t.role}</div>
            </div>
          ))}
        </div>
      </CyberCard>

      {/* I & J: Classification Explanation & Scope / Limitations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* I. Classification Explanation */}
        <CyberCard className="p-6 space-y-4" glow="amber">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-amber-950/80 border border-amber-500/40 text-amber-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider">Classification Policy Explanation</h3>
              <p className="text-[11px] text-slate-400">Three Visible Categories & Safety Layer</p>
            </div>
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="p-3 rounded-xl bg-[#070D1A] border border-emerald-500/30 flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0 mt-1" />
              <div>
                <span className="font-bold text-emerald-300">Normal (Green):</span>
                <p className="text-[11px] text-slate-300 font-sans mt-0.5">
                  Lower estimated anomaly risk according to the configured policy (<code className="text-emerald-400">&lt; 30%</code> probability). Conforms to typical operational baseline patterns.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-amber-500/30 flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shrink-0 mt-1" />
              <div>
                <span className="font-bold text-amber-300">Medium Risk (Amber):</span>
                <p className="text-[11px] text-slate-300 font-sans mt-0.5">
                  Intermediate risk according to the configured policy (<code className="text-amber-400">30% - 70%</code> probability). Represents borderline confidence or conflicting feature contributions warranting operational review.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-rose-500/30 flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400 shrink-0 mt-1" />
              <div>
                <span className="font-bold text-rose-300">Anomalous (Red):</span>
                <p className="text-[11px] text-slate-300 font-sans mt-0.5">
                  High estimated anomaly risk according to the configured policy (<code className="text-rose-400">&ge; 70%</code> probability). High statistical divergence and elevated risk indicators.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-slate-700/60 flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500 shrink-0 mt-1" />
              <div>
                <span className="font-bold text-slate-400">Unclassified (Neutral Grey):</span>
                <p className="text-[11px] text-slate-300 font-sans mt-0.5">
                  No reliable model prediction is available (e.g. no active model, unsupported probabilities, or feature incompatibility). Prevents unsupported guesses.
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-[11px] text-amber-200 font-sans">
            <strong>Important Principle:</strong> A model-detected anomaly indicates statistical divergence from baseline patterns, not proof of a confirmed cyberattack.
          </div>
        </CyberCard>

        {/* J. Project Scope and Limitations */}
        <CyberCard className="p-6 space-y-4" glow="cyan">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-950/80 border border-cyan-500/40 text-cyan-400">
              <Info className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider">Scope & Honest Limitations</h3>
              <p className="text-[11px] text-slate-400">System Boundaries & Operating Constraints</p>
            </div>
          </div>

          <div className="space-y-2 text-xs text-slate-300 font-sans leading-relaxed">
            <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
              <strong className="text-white font-mono text-[11px] block mb-0.5">Dataset & Label Dependency</strong>
              Model quality and predictive precision depend directly on the selected dataset, label accuracy, feature compatibility, and validation protocol.
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
              <strong className="text-white font-mono text-[11px] block mb-0.5">Live Log Sources</strong>
              Live streaming monitoring requires a real log source, syslog socket, or external collector to be actively connected.
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
              <strong className="text-white font-mono text-[11px] block mb-0.5">SHAP Explainer Constraints</strong>
              SHAP feature explanations depend on model tree structure compatibility and feature dimension alignment.
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
              <strong className="text-white font-mono text-[11px] block mb-0.5">Authentic Empty States</strong>
              Empty dashboard charts do not indicate a system defect; Smart-Log presents honest empty states until authentic events are ingested.
            </div>

            <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050]">
              <strong className="text-white font-mono text-[11px] block mb-0.5">Investigative Support</strong>
              The application assists security analysts in investigation, but does not independently confirm malicious activity or execute unilateral host remediation.
            </div>
          </div>
        </CyberCard>
      </div>

      {/* K. Project Information (Dynamic System Status) */}
      <CyberCard className="p-6 space-y-4" glow="cyan">
        <div className="flex items-center justify-between border-b border-[#1E3050]/80 pb-3">
          <div>
            <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-cyan-400" />
              Project Information & Dynamic Runtime Status
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">Verified facts reflecting current platform state</p>
          </div>
          <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
            Smart-Log v1.0
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
            <div className="text-[10px] text-slate-400 uppercase">Project Name</div>
            <div className="text-sm font-bold text-white mt-1">Smart-Log</div>
            <div className="text-[10px] text-cyan-400 mt-0.5">Syslog SOC Platform</div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
            <div className="text-[10px] text-slate-400 uppercase">Domain & Focus</div>
            <div className="text-sm font-bold text-white mt-1">Cybersecurity & ML</div>
            <div className="text-[10px] text-cyan-400 mt-0.5">Anomaly Detection & Explainability</div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
            <div className="text-[10px] text-slate-400 uppercase">Active Production Model</div>
            <div className="text-sm font-bold text-cyan-300 mt-1 truncate">
              {activeModel ? activeModel.name : 'No Model Activated'}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {activeModel ? `${activeModel.algorithm.toUpperCase()} • v${activeModel.version}` : 'Awaiting Model Registry'}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050]">
            <div className="text-[10px] text-slate-400 uppercase">Audited Events in DB</div>
            <div className="text-sm font-bold text-white mt-1">{totalPreds} logs</div>
            <div className="text-[10px] text-emerald-400 mt-0.5">
              {datasetsCount} configured dataset(s)
            </div>
          </div>
        </div>

        {/* Dynamic Status Banner */}
        <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span className="text-slate-300">
              System Status:{' '}
              <span className="text-emerald-400 font-bold">
                {activeModel ? 'Model Active & Ready for Live Inference' : 'Operational (No Active Model Loaded)'}
              </span>
            </span>
          </div>

          {onNavigate && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold transition-all shadow-[0_0_10px_rgba(6,182,212,0.3)] cursor-pointer"
              >
                Go to SOC Dashboard
              </button>
            </div>
          )}
        </div>
      </CyberCard>

      {/* Compact Project Overview Footer */}
      <div className="pt-4 border-t border-[#1E3050]/60 text-center text-xs font-mono text-slate-500">
        <p>Smart-Log • Automated Syslog Anomaly Detection for Server Security • Enterprise SOC Edition</p>
      </div>
    </div>
  );
};
