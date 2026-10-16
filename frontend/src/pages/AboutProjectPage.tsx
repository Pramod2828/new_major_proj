import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  Activity,
  Cpu,
  Zap,
  Sliders,
  GitBranch,
  Database,
  Terminal,
  Binary,
  Layers,
  Download,
  Search,
  Server,
  Clock,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  FileText,
  ShieldCheck,
  ShieldAlert,
  Code2,
  Info,
  Radio,
  FileCheck
} from 'lucide-react';
import { api } from '../services/api';
import { CyberCard } from '../components/common/CyberCard';
import { CyberShield3D } from '../components/common/CyberShield3D';
import { PageHeader } from '../components/common/PageHeader';

interface AboutProjectPageProps {
  onNavigate?: (tab: string) => void;
}

export const AboutProjectPage: React.FC<AboutProjectPageProps> = ({ onNavigate }) => {
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchStatus = async () => {
      try {
        const data = await api.getSystemStatus();
        if (isMounted) {
          setSystemStatus(data);
        }
      } catch {
        if (isMounted) {
          setSystemStatus(null);
        }
      }
    };
    fetchStatus();
    return () => {
      isMounted = false;
    };
  }, []);

  const activeModel = systemStatus?.active_model;
  const totalPreds = systemStatus?.counts?.total_predictions ?? 0;
  const datasetsCount = systemStatus?.counts?.datasets ?? 0;

  // 1. Objectives (Compact 6-stage core goals)
  const objectives = [
    {
      num: '01',
      title: 'Log Parsing',
      desc: 'Ingest and normalize raw syslog strings across RFC 3164, RFC 5424, ISO timestamps, and structured JSON.',
      icon: Terminal,
      color: 'cyan'
    },
    {
      num: '02',
      title: 'Feature Extraction',
      desc: 'Derive leak-free numerical entropy, token ratios, digit densities, and high-severity security keyword flags.',
      icon: Binary,
      color: 'blue'
    },
    {
      num: '03',
      title: 'Anomaly Detection',
      desc: 'Deploy supervised Random Forest and XGBoost classifiers to compute continuous anomaly probability scores.',
      icon: Zap,
      color: 'violet'
    },
    {
      num: '04',
      title: 'Risk Classification',
      desc: 'Apply a transparent 3-level policy mapping probabilities into Normal, Medium Risk, and Anomalous tiers.',
      icon: ShieldAlert,
      color: 'amber'
    },
    {
      num: '05',
      title: 'Explainability',
      desc: 'Calculate exact game-theoretic SHAP feature attributions via TreeExplainer to explain individual predictions.',
      icon: Sliders,
      color: 'rose'
    },
    {
      num: '06',
      title: 'Reporting & Auditing',
      desc: 'Generate executive ReportLab PDF security audit summaries and RFC 4180 CSV logs with rolling 24h timelines.',
      icon: FileCheck,
      color: 'emerald'
    }
  ];

  // 2. Sequential Pipeline Workflow (8 stages)
  const workflowSteps = [
    { step: 1, title: 'Log Input', sub: 'Syslog / JSON / Text', icon: FileText, color: 'text-cyan-400 border-cyan-500/40 bg-cyan-950/40' },
    { step: 2, title: 'Parsing', sub: 'Regex & Header Extract', icon: Terminal, color: 'text-blue-400 border-blue-500/40 bg-blue-950/40' },
    { step: 3, title: 'Cleaning', sub: 'Sanitization & Defaults', icon: Database, color: 'text-indigo-400 border-indigo-500/40 bg-indigo-950/40' },
    { step: 4, title: 'Feature Extraction', sub: 'Entropy & Token Metrics', icon: Binary, color: 'text-violet-400 border-violet-500/40 bg-violet-950/40' },
    { step: 5, title: 'ML Prediction', sub: 'Random Forest / XGBoost', icon: Cpu, color: 'text-purple-400 border-purple-500/40 bg-purple-950/40' },
    { step: 6, title: 'Classification', sub: 'Normal / Medium / Anom', icon: Shield, color: 'text-amber-400 border-amber-500/40 bg-amber-950/40' },
    { step: 7, title: 'SHAP Explanation', sub: 'TreeExplainer Values', icon: Sliders, color: 'text-rose-400 border-rose-500/40 bg-rose-950/40' },
    { step: 8, title: 'Dashboard & Reports', sub: '24h Charts, PDF, CSV', icon: Activity, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/40' }
  ];

  // 3. Platform Features
  const platformFeatures = [
    {
      title: 'Dataset Management',
      desc: 'Inspect CSV, JSON, and JSONL schemas, configure candidate targets, and prevent data leakage before model training.',
      icon: Database
    },
    {
      title: 'Model Training & Tuning',
      desc: 'Train Random Forest and XGBoost classifiers with custom tree depth, estimator counts, and balanced class weights.',
      icon: Cpu
    },
    {
      title: 'Model Comparison',
      desc: 'Evaluate side-by-side Accuracy, Precision, Recall, F1-Score, ROC-AUC, PR-AUC, and False Positive Rates on identical splits.',
      icon: Activity
    },
    {
      title: 'Live Monitoring',
      desc: 'Real-time telemetry streaming and inference when connected to an active log stream or local collector.',
      icon: Radio
    },
    {
      title: '24-Hour Analysis',
      desc: 'Interactive Recharts timeline displaying rolling hourly distributions across Normal, Medium, and Anomalous categories.',
      icon: Clock
    },
    {
      title: 'History & Audit Trail',
      desc: 'Persistent SQLite storage of all analyzed events; filterable by risk level, date range, model version, and text search.',
      icon: Layers
    },
    {
      title: 'Executive PDF & CSV Reports',
      desc: 'One-click ReportLab PDF security audit generation with metrics and incident tables, alongside RFC 4180 CSV exports.',
      icon: Download
    }
  ];

  // 4. Technology Stack (Only technologies actually present in the project)
  const techStack = [
    { name: 'React 19 & TypeScript', role: 'Frontend UI & Type Safety', group: 'Frontend', color: 'border-cyan-500/40 text-cyan-300 bg-cyan-950/50' },
    { name: 'Vite 8 & Tailwind CSS', role: 'Build Tool & Dark Theme Styling', group: 'Frontend', color: 'border-sky-500/40 text-sky-300 bg-sky-950/50' },
    { name: 'Framer Motion', role: 'Glass Card & Transition Animations', group: 'Frontend', color: 'border-purple-500/40 text-purple-300 bg-purple-950/50' },
    { name: 'Recharts & Lucide React', role: 'SOC Visualizations & Cyber Icons', group: 'Frontend', color: 'border-teal-500/40 text-teal-300 bg-teal-950/50' },
    { name: 'Python 3.11 & Flask', role: 'REST API & Application Engine', group: 'Backend', color: 'border-emerald-500/40 text-emerald-300 bg-emerald-950/50' },
    { name: 'scikit-learn', role: 'Random Forest Supervised Classifier', group: 'ML & Data', color: 'border-orange-500/40 text-orange-300 bg-orange-950/50' },
    { name: 'XGBoost', role: 'Gradient-Boosted Decision Trees', group: 'ML & Data', color: 'border-amber-500/40 text-amber-300 bg-amber-950/50' },
    { name: 'SHAP (TreeExplainer)', role: 'Additive Game-Theoretic Attributions', group: 'ML & Data', color: 'border-rose-500/40 text-rose-300 bg-rose-950/50' },
    { name: 'pandas & NumPy', role: 'Feature Transformation & Preprocessing', group: 'ML & Data', color: 'border-blue-500/40 text-blue-300 bg-blue-950/50' },
    { name: 'SQLite with WAL Mode', role: 'Transactional Audit Persistence', group: 'Storage', color: 'border-slate-500/40 text-slate-300 bg-slate-900/50' },
    { name: 'ReportLab', role: 'Executive PDF Audit Generation', group: 'Reporting', color: 'border-indigo-500/40 text-indigo-300 bg-indigo-950/50' },
    { name: 'joblib', role: 'Artifact Serialization & Versioning', group: 'Storage', color: 'border-violet-500/40 text-violet-300 bg-violet-950/50' }
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Page Title & Breadcrumb Header */}
      <PageHeader
        title="About Project"
        subtitle="System architecture, supervised ML algorithms, explainability engine, and operational boundaries"
        badge="SOC Specification"
      />

      {/* 1. Hero Section */}
      <CyberCard className="p-6 md:p-8 overflow-hidden relative" glow="cyan" hoverEffect={false}>
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8 relative z-10">
          <div className="space-y-3.5 text-center lg:text-left max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>PLATFORM ARCHITECTURE & METHODOLOGY</span>
            </div>

            <div className="space-y-1.5">
              <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight font-sans">
                SMART-LOG
              </h1>
              <h2 className="text-sm md:text-base font-semibold text-cyan-300 font-mono">
                Automated Syslog Anomaly Detection for Server Security
              </h2>
            </div>

            <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans">
              Smart-Log provides machine-learning-based analysis of system logs to identify unusual behavior,
              classify operational risks into a calibrated three-level policy, and deliver transparent mathematical
              SHAP explanations for actionable SOC investigations.
            </p>

            {/* Quick Pill Stats */}
            <div className="pt-2 flex flex-wrap items-center justify-center lg:justify-start gap-2 text-xs font-mono">
              <span className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-cyan-500/30 text-cyan-200">
                Random Forest & XGBoost
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-cyan-500/30 text-cyan-200">
                SHAP TreeExplainer
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-cyan-500/30 text-cyan-200">
                Normal • Medium • Anomalous
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-cyan-500/30 text-cyan-200">
                Executive PDF/CSV Reporting
              </span>
            </div>
          </div>

          {/* 3D Holographic Cyber Emblem */}
          <div className="shrink-0 py-2">
            <CyberShield3D />
          </div>
        </div>
      </CyberCard>

      {/* 2. Overview Section */}
      <CyberCard className="p-6 space-y-3" glow="cyan">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-500/40 text-cyan-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider">Project Overview</h3>
            <p className="text-[11px] text-slate-400">Machine-learning-based analysis of system logs to identify unusual behavior</p>
          </div>
        </div>
        <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans pt-1">
          Modern enterprise operating systems and network infrastructure produce immense volumes of syslog messages daily.
          Traditional signature matching and static regex rules struggle to scale against zero-day anomalies, evolving intrusion tactics,
          and subtle behavioral deviations buried in routine system telemetry.
        </p>
        <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans">
          Smart-Log automates log analysis by combining standardized multi-format parsing with statistical feature engineering,
          supervised machine learning classifiers (Random Forest and XGBoost), and game-theoretic explainability. By establishing
          data-driven baselines, the platform surfaces anomalous activity and provides security engineers with transparent,
          feature-level justifications for every flag.
        </p>
      </CyberCard>

      {/* 3. Objectives */}
      <div className="space-y-4">
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            Project Objectives
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">End-to-end capabilities fulfilled across the platform</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {objectives.map((obj) => {
            const Icon = obj.icon;
            return (
              <CyberCard key={obj.num} className="p-4 space-y-2 flex flex-col justify-between" glow="cyan">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-cyan-400">{obj.num}</span>
                    <div className="p-1.5 rounded-lg bg-[#070D1A] border border-[#1E3050] text-cyan-300">
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <h4 className="text-xs font-bold text-white font-mono">{obj.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed mt-1">{obj.desc}</p>
                </div>
              </CyberCard>
            );
          })}
        </div>
      </div>

      {/* 4. Algorithms & Techniques */}
      <div className="space-y-4">
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Algorithms & Classification Policy
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">Supervised classifiers, explainability mechanics, and three-level decision tiers</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Random Forest */}
          <CyberCard className="p-5 space-y-2.5" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-300">
                ENSEMBLE MODEL
              </span>
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">Random Forest Classifier</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Combines an ensemble of randomized decision trees to model complex feature interactions.
              Averages tree votes to prevent overfitting on noisy logs and provides robust baseline generalization across varied server workloads.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Module: <code className="text-cyan-300">sklearn.ensemble.RandomForestClassifier</code>
            </div>
          </CyberCard>

          {/* XGBoost */}
          <CyberCard className="p-5 space-y-2.5" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950/80 border border-teal-500/40 text-teal-300">
                GRADIENT BOOSTING
              </span>
              <Zap className="w-4 h-4 text-teal-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">XGBoost Classifier</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Utilizes gradient-boosted decision trees that sequentially minimize residual errors through second-order Taylor approximations.
              Serves as a high-precision benchmark classifier for comparative model evaluations.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Module: <code className="text-teal-300">xgboost.XGBClassifier</code>
            </div>
          </CyberCard>

          {/* SHAP */}
          <CyberCard className="p-5 space-y-2.5" glow="cyan">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-950/80 border border-violet-500/40 text-violet-300">
                EXPLAINABILITY
              </span>
              <Sliders className="w-4 h-4 text-violet-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">SHAP (TreeExplainer)</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Computes exact game-theoretic Shapley values to isolate the contribution of each log feature.
              Identifies whether specific indicators (e.g. high message entropy, auth failures) pushed the prediction toward Anomaly or Normal.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Module: <code className="text-violet-300">shap.TreeExplainer</code>
            </div>
          </CyberCard>

          {/* Three-Level Classification Policy */}
          <CyberCard className="p-5 space-y-2.5" glow="amber">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500/40 text-amber-300">
                DECISION LAYER
              </span>
              <ShieldAlert className="w-4 h-4 text-amber-400" />
            </div>
            <h4 className="text-xs font-bold text-white font-mono">Three-Level Risk Policy</h4>
            <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
              Maps continuous model probabilities into <strong>Normal (&lt; 0.30)</strong>, <strong>Medium ([0.30, 0.70))</strong>, and <strong>Anomalous (&ge; 0.70)</strong> tiers.
              Medium captures borderline model uncertainty and mixed indicators rather than treating predictions as a naive binary threshold.
            </p>
            <div className="pt-1 text-[10px] font-mono text-slate-400 border-t border-[#1E3050]/60">
              Module: <code className="text-amber-300">RiskClassificationPolicy</code>
            </div>
          </CyberCard>
        </div>
      </div>

      {/* 5. End-to-End Workflow */}
      <CyberCard className="p-6 md:p-8 space-y-6" glow="cyan" hoverEffect={false}>
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-cyan-400" />
            System End-to-End Workflow
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">
            Sequential pipeline: Log Input → Parsing → Cleaning → Feature Extraction → ML Prediction → Classification → SHAP Explanation → Dashboard & Reports
          </p>
        </div>

        {/* Visual Workflow Steps */}
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

          <div className="mt-4 p-3 rounded-xl bg-[#070D1A] border border-[#1E3050] text-[11px] font-mono text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>Leak-free processing: Preprocessors fitted strictly on training splits; unclassified fallback when models are unverified.</span>
            </span>
            <span className="text-cyan-300 font-bold">8 Sequential Stages</span>
          </div>
        </div>
      </CyberCard>

      {/* 6. Features Grid */}
      <div className="space-y-4">
        <div>
          <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            Key Platform Features
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">Integrated capabilities for security operations and model governance</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {platformFeatures.map((f, i) => {
            const Icon = f.icon;
            return (
              <CyberCard key={i} className="p-4 space-y-2 flex flex-col justify-between" glow="cyan">
                <div>
                  <div className="flex items-center gap-2 text-cyan-300 font-mono text-xs font-bold mb-1.5">
                    <div className="p-1 rounded bg-[#070D1A] border border-cyan-500/30">
                      <Icon className="w-3.5 h-3.5 text-cyan-400" />
                    </div>
                    <span className="truncate">{f.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-sans leading-relaxed">{f.desc}</p>
                </div>
              </CyberCard>
            );
          })}
        </div>
      </div>

      {/* 7. Technology Stack */}
      <CyberCard className="p-6 space-y-4" glow="cyan">
        <div className="flex items-center justify-between border-b border-[#1E3050]/80 pb-3">
          <div>
            <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider flex items-center gap-2">
              <Code2 className="w-4 h-4 text-cyan-400" />
              Technology Stack
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">Verified frameworks and libraries active in the Smart-Log project</p>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-500/40">
            100% Present in Codebase
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 font-mono">
          {techStack.map((t, idx) => (
            <div key={idx} className={`p-3 rounded-xl border ${t.color} flex flex-col justify-between`}>
              <div>
                <div className="text-[9px] uppercase tracking-wider text-slate-400 mb-0.5">{t.group}</div>
                <div className="font-bold text-xs text-white">{t.name}</div>
              </div>
              <div className="text-[10px] text-slate-300 mt-2 font-sans">{t.role}</div>
            </div>
          ))}
        </div>
      </CyberCard>

      {/* 8. Limitations & Operating Scope */}
      <CyberCard className="p-6 space-y-4" glow="amber">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-950/80 border border-amber-500/40 text-amber-400">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white uppercase font-mono tracking-wider">Operational Boundaries & Honest Limitations</h3>
            <p className="text-[11px] text-slate-400 font-mono">Guidelines for responsible interpretation of model telemetry</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-sans">
          <div className="p-4 rounded-xl bg-[#070D1A] border border-amber-500/30 space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-mono font-bold text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Dataset & Model Dependency</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Model accuracy and predictive quality depend directly on the representativeness, label accuracy, and balance of the training dataset.
              Models trained on specific schemas cannot reliably generalize to unaligned log formats.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#070D1A] border border-amber-500/30 space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-mono font-bold text-xs">
              <Radio className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Live Monitoring Source Requirement</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Live continuous monitoring requires an active, connected system log source, socket, or collector.
              Smart-Log does not fabricate synthetic event streams to simulate false activity when disconnected.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#070D1A] border border-amber-500/30 space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-mono font-bold text-xs">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Statistical Anomaly ≠ Attack Proof</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              A model-detected anomaly indicates statistical divergence from normal operational baseline behavior—it does not constitute proof of a confirmed cyberattack.
              Alerts assist analyst investigations rather than executing automatic unilateral actions.
            </p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Active Model: <strong className="text-cyan-300">{activeModel ? `${activeModel.name} (v${activeModel.version})` : 'No Model Currently Active'}</strong></span>
            <span className="text-slate-600">|</span>
            <span>Audited Records: <strong className="text-white">{totalPreds}</strong></span>
          </div>

          {onNavigate && (
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold transition-all shadow-[0_0_10px_rgba(6,182,212,0.3)] cursor-pointer"
            >
              Back to SOC Dashboard
            </button>
          )}
        </div>
      </CyberCard>

      {/* Footer Note */}
      <div className="pt-2 text-center text-xs font-mono text-slate-500">
        <p>Smart-Log • Automated Syslog Anomaly Detection for Server Security • Enterprise SOC Edition</p>
      </div>
    </div>
  );
};

export default AboutProjectPage;
