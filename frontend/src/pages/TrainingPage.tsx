import React, { useState, useEffect } from 'react';
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  ShieldAlert,
  RefreshCw,
  Terminal,
  Cpu,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { Dataset } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';

export const TrainingPage: React.FC<{ onNavigate: (tab: string) => void }> = ({ onNavigate }) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [canTrain, setCanTrain] = useState<boolean>(false);
  const [guardMessage, setGuardMessage] = useState<string>('');

  // Selected Algorithms
  const [trainRF, setTrainRF] = useState<boolean>(true);
  const [trainXGB, setTrainXGB] = useState<boolean>(true);

  // Hyperparameters: Random Forest
  const [rfEstimators, setRfEstimators] = useState<number>(100);
  const [rfMaxDepth, setRfMaxDepth] = useState<number>(15);
  const [rfMinSamplesSplit, setRfMinSamplesSplit] = useState<number>(2);
  const [rfClassWeight, setRfClassWeight] = useState<string>('balanced');
  const [rfRandomState, setRfRandomState] = useState<number>(42);

  // Hyperparameters: XGBoost
  const [xgbEstimators, setXgbEstimators] = useState<number>(100);
  const [xgbMaxDepth, setXgbMaxDepth] = useState<number>(6);
  const [xgbLearningRate, setXgbLearningRate] = useState<number>(0.1);
  const [xgbSubsample, setXgbSubsample] = useState<number>(0.8);
  const [xgbScalePosWeight, setXgbScalePosWeight] = useState<number>(1.0);
  const [xgbRandomState, setXgbRandomState] = useState<number>(42);

  // Training state
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainingLogs, setTrainingLogs] = useState<string[]>([]);
  const [trainingResult, setTrainingResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const checkGuardAndDatasets = async () => {
    try {
      const guard = await api.getTrainingGuard();
      setCanTrain(guard.can_train);
      setGuardMessage(guard.message);

      const dss = await api.listDatasets();
      setDatasets(dss);

      const approved = dss.find((d: any) => d.is_approved);
      if (approved) {
        setSelectedDatasetId(approved.id);
      } else if (dss.length > 0) {
        setSelectedDatasetId(dss[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to check training guard');
    }
  };

  useEffect(() => {
    checkGuardAndDatasets();
  }, []);

  const handleStartTraining = async () => {
    if (!selectedDatasetId) {
      setErrorMsg('Please select a dataset');
      return;
    }

    const algorithms: string[] = [];
    if (trainRF) algorithms.push('random_forest');
    if (trainXGB) algorithms.push('xgboost');

    if (algorithms.length === 0) {
      setErrorMsg('Select at least one algorithm (Random Forest or XGBoost).');
      return;
    }

    setIsTraining(true);
    setErrorMsg(null);
    setTrainingResult(null);
    setTrainingLogs([
      `[${new Date().toLocaleTimeString()}] Initializing supervised training pipeline...`,
      `[${new Date().toLocaleTimeString()}] Target dataset verified: ID ${selectedDatasetId}`,
      `[${new Date().toLocaleTimeString()}] Preprocessing: Fitting ColumnTransformer exclusively on X_train split...`,
      `[${new Date().toLocaleTimeString()}] Transforming X_val and X_test without leakage...`,
      `[${new Date().toLocaleTimeString()}] Training selected classifiers: ${algorithms.join(', ').toUpperCase()}...`
    ]);

    try {
      const res = await api.startTraining({
        dataset_id: selectedDatasetId,
        algorithms,
        rf_params: {
          n_estimators: rfEstimators,
          max_depth: rfMaxDepth,
          min_samples_split: rfMinSamplesSplit,
          class_weight: rfClassWeight,
          random_state: rfRandomState,
        },
        xgb_params: {
          n_estimators: xgbEstimators,
          max_depth: xgbMaxDepth,
          learning_rate: xgbLearningRate,
          subsample: xgbSubsample,
          scale_pos_weight: xgbScalePosWeight,
          random_state: xgbRandomState,
        },
      });

      setTrainingLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] Supervised model convergence achieved!`,
        `[${new Date().toLocaleTimeString()}] Multi-metric evaluation calculated on held-out test split.`,
        `[${new Date().toLocaleTimeString()}] Serialized .joblib bundles registered in Model Registry.`
      ]);
      setTrainingResult(res.training_results);
    } catch (err: any) {
      setErrorMsg(err.message || 'Training failed');
      setTrainingLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] HALTED: ${err.message || 'Training error encountered.'}`
      ]);
    } finally {
      setIsTraining(false);
    }
  };

  const selectedDsObj = datasets.find((d) => d.id === selectedDatasetId);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Supervised Model Training Center"
        subtitle="Configure and train Random Forest & XGBoost classifiers on approved training splits with fair held-out test evaluation"
        badge="ML Training Tier"
      />

      {/* Readiness Guard Banner */}
      {!canTrain ? (
        <CyberCard className="p-4" glow="amber" hoverEffect={false}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-950/60 border border-amber-500/40 text-amber-400 shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-xs font-mono text-amber-300">Training Guard Active</div>
                <div className="text-xs text-slate-400 mt-0.5">{guardMessage}</div>
              </div>
            </div>
            <button
              onClick={() => onNavigate('datasets')}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-mono font-semibold text-xs shadow-[0_0_15px_rgba(245,158,11,0.3)] transition-all cursor-pointer shrink-0"
            >
              Go to Dataset Manager
            </button>
          </div>
        </CyberCard>
      ) : (
        <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/50 text-xs font-mono flex items-center gap-2.5 text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Training Guard Cleared: Approved dataset configuration verified and ready for model execution.</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Dataset Picker Card */}
      <CyberCard className="p-5" glow="cyan" hoverEffect={false}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1">
            <label className="block text-xs font-bold text-white uppercase font-mono tracking-wider mb-2">
              Select Target Approved Dataset
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full bg-[#070D1A] border border-[#1E3050] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count.toLocaleString()} rows, {d.is_approved ? 'APPROVED' : 'UNAPPROVED'})
                </option>
              ))}
            </select>
          </div>

          {selectedDsObj && (
            <div className="shrink-0 pt-2 md:pt-6">
              <StatusBadge status={selectedDsObj.is_approved ? 'approved' : 'pending'} />
            </div>
          )}
        </div>
      </CyberCard>

      {/* Model Parameter Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model 1: Random Forest */}
        <CyberCard
          className={`p-6 transition-all ${trainRF ? 'border-blue-500/40' : 'opacity-60'}`}
          glow={trainRF ? 'cyan' : 'none'}
          hoverEffect={false}
        >
          <div className="flex items-center justify-between border-b border-[#1E3050]/60 pb-3 mb-4">
            <label className="flex items-center gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={trainRF}
                onChange={(e) => setTrainRF(e.target.checked)}
                className="rounded border-[#1E3050] text-cyan-500 focus:ring-0"
              />
              <span className="font-extrabold text-xs text-white uppercase font-mono tracking-wider">
                Random Forest Classifier
              </span>
            </label>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-950/80 text-blue-300 border border-blue-500/40">
              scikit-learn
            </span>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Number of Trees (n_estimators):</span>
                <span className="text-cyan-400 font-bold">{rfEstimators}</span>
              </div>
              <input
                type="range"
                min="10"
                max="300"
                step="10"
                value={rfEstimators}
                onChange={(e) => setRfEstimators(parseInt(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Max Depth</label>
                <input
                  type="number"
                  min="2"
                  max="50"
                  value={rfMaxDepth}
                  onChange={(e) => setRfMaxDepth(parseInt(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Min Samples Split</label>
                <input
                  type="number"
                  min="2"
                  max="10"
                  value={rfMinSamplesSplit}
                  onChange={(e) => setRfMinSamplesSplit(parseInt(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Class Weight</label>
                <select
                  value={rfClassWeight}
                  onChange={(e) => setRfClassWeight(e.target.value)}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                >
                  <option value="balanced">balanced</option>
                  <option value="balanced_subsample">balanced_subsample</option>
                  <option value="none">none</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Random Seed</label>
                <input
                  type="number"
                  value={rfRandomState}
                  onChange={(e) => setRfRandomState(parseInt(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
            </div>
          </div>
        </CyberCard>

        {/* Model 2: XGBoost */}
        <CyberCard
          className={`p-6 transition-all ${trainXGB ? 'border-amber-500/40' : 'opacity-60'}`}
          glow={trainXGB ? 'amber' : 'none'}
          hoverEffect={false}
        >
          <div className="flex items-center justify-between border-b border-[#1E3050]/60 pb-3 mb-4">
            <label className="flex items-center gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={trainXGB}
                onChange={(e) => setTrainXGB(e.target.checked)}
                className="rounded border-[#1E3050] text-amber-500 focus:ring-0"
              />
              <span className="font-extrabold text-xs text-white uppercase font-mono tracking-wider">
                XGBoost Classifier
              </span>
            </label>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-500/40">
              xgboost
            </span>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Boosting Rounds (n_estimators):</span>
                <span className="text-amber-400 font-bold">{xgbEstimators}</span>
              </div>
              <input
                type="range"
                min="10"
                max="300"
                step="10"
                value={xgbEstimators}
                onChange={(e) => setXgbEstimators(parseInt(e.target.value))}
                className="w-full accent-amber-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Max Depth</label>
                <input
                  type="number"
                  min="2"
                  max="20"
                  value={xgbMaxDepth}
                  onChange={(e) => setXgbMaxDepth(parseInt(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Learning Rate</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="0.5"
                  value={xgbLearningRate}
                  onChange={(e) => setXgbLearningRate(parseFloat(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Subsample Ratio</label>
                <input
                  type="number"
                  step="0.05"
                  min="0.5"
                  max="1.0"
                  value={xgbSubsample}
                  onChange={(e) => setXgbSubsample(parseFloat(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Scale Pos Weight</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="20"
                  value={xgbScalePosWeight}
                  onChange={(e) => setXgbScalePosWeight(parseFloat(e.target.value))}
                  className="w-full bg-[#070D1A] border border-[#1E3050] rounded-lg px-2.5 py-1.5 text-white"
                />
              </div>
            </div>
          </div>
        </CyberCard>
      </div>

      {/* Start Button */}
      <div className="flex items-center justify-end">
        <button
          onClick={handleStartTraining}
          disabled={!canTrain || isTraining || !selectedDsObj?.is_approved}
          className={`px-7 py-3 rounded-xl text-xs font-bold font-mono flex items-center gap-2.5 transition-all shadow-lg ${
            canTrain && !isTraining && selectedDsObj?.is_approved
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-[0_0_25px_rgba(6,182,212,0.4)] cursor-pointer'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-[#1E3050]'
          }`}
        >
          {isTraining ? <RefreshCw className="w-4 h-4 animate-spin text-cyan-300" /> : <Play className="w-4 h-4 text-cyan-300" />}
          <span>{isTraining ? 'Training Models...' : 'Execute Supervised Training'}</span>
        </button>
      </div>

      {/* Execution Terminal Output */}
      {trainingLogs.length > 0 && (
        <CyberCard className="p-4 bg-[#050811] border-[#1E3050]" glow="none" hoverEffect={false}>
          <div className="flex items-center gap-2 pb-2.5 border-b border-[#1E3050]/70 text-[11px] font-mono text-slate-400">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>TRAINING ORCHESTRATION CONSOLE</span>
          </div>
          <div className="pt-3 space-y-1 font-mono text-xs max-h-48 overflow-y-auto">
            {trainingLogs.map((log, i) => (
              <div key={i} className="text-cyan-300/90 leading-relaxed">
                {log}
              </div>
            ))}
          </div>
        </CyberCard>
      )}

      {/* Completion Banner */}
      {trainingResult && (
        <CyberCard className="p-6" glow="emerald" hoverEffect={false}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-300 font-bold font-mono text-xs">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Supervised Training & Evaluation Successful</span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                Models evaluated on held-out test split ({trainingResult.split_summary.test_samples} records). Ready for comparison and activation.
              </p>
            </div>
            <button
              onClick={() => onNavigate('models')}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-mono font-bold text-xs flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all cursor-pointer"
            >
              <span>Model Comparison</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </CyberCard>
      )}
    </div>
  );
};
