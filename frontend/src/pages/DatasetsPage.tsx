import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Upload,
  Database,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  RefreshCw,
  Info,
  Tag,
  Check,
  X,
  Search,
  Filter,
  Trash2,
  Lock,
  Eye,
  ChevronRight,
  FileText,
  BarChart2,
  Layers,
  CloudUpload,
  Shield,
} from 'lucide-react';
import { api } from '../services/api';
import { Dataset, DatasetInspection } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { PageHeader } from '../components/common/PageHeader';

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmtNumber(n?: number | null): string {
  if (n == null) return '—';
  return n.toLocaleString();
}

function statusColor(status: string): string {
  switch (status) {
    case 'approved': return 'text-emerald-400';
    case 'validated': return 'text-cyan-400';
    case 'configured': return 'text-blue-400';
    case 'invalid': return 'text-rose-400';
    default: return 'text-amber-400';
  }
}

function dataTypeBadge(dtype: string): string {
  if (dtype.includes('int') || dtype.includes('float')) return 'bg-blue-950 text-blue-300 border-blue-500/30';
  if (dtype.includes('object') || dtype.includes('str')) return 'bg-violet-950 text-violet-300 border-violet-500/30';
  if (dtype.includes('bool')) return 'bg-amber-950 text-amber-300 border-amber-500/30';
  return 'bg-slate-800 text-slate-300 border-slate-600/30';
}

// ─── Upload Dialog ─────────────────────────────────────────────────────────────
interface UploadDialogProps {
  onClose: () => void;
  onSuccess: (datasetId: string) => void;
}

const UploadDialog: React.FC<UploadDialogProps> = ({ onClose, onSuccess }) => {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const ALLOWED = ['.csv', '.json', '.jsonl'];
  const MAX_SIZE_MB = 100;

  const validateFile = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return `Unsupported format. Allowed: ${ALLOWED.join(', ')}`;
    if (f.size === 0) return 'File is empty (0 bytes).';
    if (f.size > MAX_SIZE_MB * 1024 * 1024) return `File exceeds ${MAX_SIZE_MB} MB limit.`;
    return null;
  };

  const pickFile = (f: File) => {
    const err = validateFile(f);
    if (err) { setError(err); setFile(null); return; }
    setError(null);
    setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    // Simulate progress ticks
    const progressInterval = setInterval(() => setProgress(p => Math.min(p + 12, 88)), 200);
    try {
      const res = await api.uploadDataset(file);
      clearInterval(progressInterval);
      setProgress(100);
      setTimeout(() => { onSuccess(res.dataset_id); onClose(); }, 400);
    } catch (err: any) {
      clearInterval(progressInterval);
      setProgress(0);
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-lg mx-4 rounded-2xl bg-[#0B1628] border border-[#1E3050] shadow-2xl shadow-black/50"
           onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E3050]">
          <div className="flex items-center gap-2">
            <CloudUpload className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-sm text-white font-mono">Import Dataset File</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors"><X className="w-4 h-4" /></button>
        </div>

        <div className="p-6 space-y-4">
          {/* Drag-drop zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => !uploading && inputRef.current?.click()}
            className={`rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
              dragOver ? 'border-cyan-400 bg-cyan-950/20' :
              file ? 'border-emerald-500/60 bg-emerald-950/10' :
              'border-[#1E3050] hover:border-slate-500 bg-[#070D1A]'
            }`}
          >
            <input ref={inputRef} type="file" accept=".csv,.json,.jsonl" className="hidden"
                   onChange={e => { const f = e.target.files?.[0]; if (f) pickFile(f); }} />
            {file ? (
              <>
                <FileText className="w-8 h-8 mx-auto text-emerald-400 mb-2" />
                <p className="text-sm font-mono text-white font-semibold">{file.name}</p>
                <p className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
              </>
            ) : (
              <>
                <CloudUpload className="w-8 h-8 mx-auto text-slate-500 mb-2" />
                <p className="text-sm font-mono text-white">Drag &amp; drop or click to browse</p>
                <p className="text-xs text-slate-400 mt-1">CSV, JSON, JSONL · max {MAX_SIZE_MB} MB</p>
              </>
            )}
          </div>

          {/* Progress */}
          {uploading && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono text-slate-400">
                <span>Uploading &amp; parsing…</span>
                <span>{progress}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-[#1E3050] overflow-hidden">
                <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-200 rounded-full"
                     style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}

          {/* Constraints info */}
          <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050] text-[11px] font-mono text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 text-amber-400 font-semibold mb-1">
              <Shield className="w-3.5 h-3.5" /> Schema &amp; Safety Rules
            </div>
            <div>• CSV must have a header row; JSON must be an array or records object.</div>
            <div>• Duplicate filenames are rejected — delete the existing dataset first.</div>
            <div>• Uploaded datasets do not trigger retraining automatically.</div>
            <div>• A schema incompatibility warning is shown when features don't match the active model.</div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button onClick={onClose} disabled={uploading}
                    className="px-4 py-2 rounded-xl text-xs font-mono text-slate-400 border border-[#1E3050] hover:border-slate-500 transition-colors">
              Cancel
            </button>
            <button onClick={handleUpload} disabled={!file || uploading}
                    className={`px-5 py-2 rounded-xl text-xs font-mono font-semibold flex items-center gap-2 transition-all ${
                      file && !uploading
                        ? 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)]'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    }`}>
              <Upload className="w-3.5 h-3.5" />
              {uploading ? 'Uploading…' : 'Import Dataset'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Column Schema Table ───────────────────────────────────────────────────────
interface ColumnTableProps {
  columns: any[];
  targetColumn?: string;
}
const ColumnTable: React.FC<ColumnTableProps> = ({ columns, targetColumn }) => (
  <div className="overflow-x-auto rounded-xl border border-[#1E3050]">
    <table className="w-full text-[11px] font-mono">
      <thead>
        <tr className="border-b border-[#1E3050] bg-[#070D1A]">
          {['Column', 'Type', 'Null %', 'Unique', 'Role'].map(h => (
            <th key={h} className="text-left px-3 py-2 text-slate-400 font-semibold">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {columns.map((c: any) => {
          const isTarget = c.name === targetColumn;
          return (
            <tr key={c.name} className={`border-b border-[#1E3050]/50 ${isTarget ? 'bg-cyan-950/10' : 'hover:bg-white/[0.02]'}`}>
              <td className="px-3 py-2 text-white font-semibold">{c.name}</td>
              <td className="px-3 py-2">
                <span className={`px-1.5 py-0.5 rounded border text-[10px] ${dataTypeBadge(c.dtype || '')}`}>{c.dtype || '—'}</span>
              </td>
              <td className={`px-3 py-2 ${(c.null_percent || 0) > 10 ? 'text-amber-400' : 'text-slate-400'}`}>
                {(c.null_percent ?? 0).toFixed(1)}%
              </td>
              <td className="px-3 py-2 text-slate-300">{c.unique_count ?? '—'}</td>
              <td className="px-3 py-2">
                {isTarget
                  ? <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30 text-[10px]">Target</span>
                  : c.is_categorical
                  ? <span className="px-1.5 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-500/30 text-[10px]">Categorical</span>
                  : <span className="px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-500/30 text-[10px]">Numeric</span>
                }
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
);

// ─── Main Page ─────────────────────────────────────────────────────────────────
export const DatasetsPage: React.FC<{ onNavigate: (tab: string) => void }> = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [inspection, setInspection] = useState<DatasetInspection | null>(null);
  const [selectedDatasetDetail, setSelectedDatasetDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [inspecting, setInspecting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'builtin' | 'uploaded'>('all');
  const [activeTab, setActiveTab] = useState<'overview' | 'schema' | 'preview' | 'configure'>('overview');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  // Configuration form
  const [targetColumn, setTargetColumn] = useState('');
  const [normalValue, setNormalValue] = useState('');
  const [anomalyValue, setAnomalyValue] = useState('');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [trainRatio, setTrainRatio] = useState(0.70);
  const [valRatio, setValRatio] = useState(0.15);
  const [testRatio, setTestRatio] = useState(0.15);
  const [stratified, setStratified] = useState(true);
  const [validationResult, setValidationResult] = useState<{ is_valid: boolean; errors: string[]; warnings: string[] } | null>(null);
  const [validating, setValidating] = useState(false);

  const loadDatasets = useCallback(async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await api.listDatasets();
      setDatasets(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch datasets');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDatasets(); }, [loadDatasets]);

  // Auto-select first dataset when list loads
  useEffect(() => {
    if (datasets.length > 0 && !selectedDatasetId) {
      selectDataset(datasets[0].id);
    }
  }, [datasets]);

  const selectDataset = async (id: string) => {
    setSelectedDatasetId(id);
    setValidationResult(null);
    setErrorMsg(null);
    setSuccessMsg(null);
    setActiveTab('overview');
    setInspection(null);
    setSelectedDatasetDetail(null);
    try {
      setInspecting(true);
      const [ds, insp] = await Promise.all([api.getDataset(id), api.inspectDataset(id)]);
      setSelectedDatasetDetail(ds);
      setInspection(insp.inspection);

      if (ds.config) {
        setTargetColumn(ds.config.target_column || '');
        setNormalValue(ds.config.normal_value || '');
        setAnomalyValue(ds.config.anomaly_value || '');
        setSelectedFeatures(ds.config.feature_columns || []);
        setTrainRatio(ds.config.train_ratio ?? 0.70);
        setValRatio(ds.config.val_ratio ?? 0.15);
        setTestRatio(ds.config.test_ratio ?? 0.15);
        setStratified(ds.config.stratified ?? true);
      } else {
        setTargetColumn('');
        setNormalValue('');
        setAnomalyValue('');
        const defaultFeats = (insp.inspection?.columns || [])
          .filter((c: any) => !insp.inspection.candidate_timestamps?.includes(c.name))
          .map((c: any) => c.name);
        setSelectedFeatures(defaultFeats);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load dataset details');
    } finally {
      setInspecting(false);
    }
  };

  const handleUploadSuccess = async (datasetId: string) => {
    await loadDatasets();
    setSuccessMsg('Dataset imported successfully.');
    selectDataset(datasetId);
  };

  const handleTargetChange = (colName: string) => {
    setTargetColumn(colName);
    setSelectedFeatures(prev => prev.filter(f => f !== colName));
    const colMeta = inspection?.columns.find(c => c.name === colName);
    if (colMeta && colMeta.unique_values.length >= 2) {
      setNormalValue(String(colMeta.unique_values[0]));
      setAnomalyValue(String(colMeta.unique_values[1]));
    }
  };

  const toggleFeature = (colName: string) => {
    if (colName === targetColumn) return;
    setSelectedFeatures(prev => prev.includes(colName) ? prev.filter(f => f !== colName) : [...prev, colName]);
  };

  const handleSaveAndValidate = async () => {
    if (!selectedDatasetId) return;
    setValidating(true); setErrorMsg(null); setSuccessMsg(null);
    try {
      await api.configureDataset(selectedDatasetId, {
        target_column: targetColumn, normal_value: normalValue,
        anomaly_value: anomalyValue, feature_columns: selectedFeatures,
        train_ratio: trainRatio, val_ratio: valRatio, test_ratio: testRatio, stratified
      });
      const val = await api.validateDataset(selectedDatasetId);
      setValidationResult(val);
      if (val.is_valid) setSuccessMsg('Schema validated! You can now approve this dataset for training.');
      else setErrorMsg('Validation failed — resolve errors shown below.');
      loadDatasets();
    } catch (err: any) {
      setErrorMsg(err.message || 'Validation request failed');
    } finally { setValidating(false); }
  };

  const handleApprove = async () => {
    if (!selectedDatasetId) return;
    try {
      await api.approveDataset(selectedDatasetId);
      setSuccessMsg('Dataset approved! Training is now unlocked.');
      await loadDatasets();
    } catch (err: any) { setErrorMsg(err.message || 'Approval failed'); }
  };

  const handleDelete = async (id: string) => {
    setConfirmDeleteId(null);
    try {
      await api.deleteDataset(id);
      setSuccessMsg('Dataset deleted.');
      if (selectedDatasetId === id) { setSelectedDatasetId(null); setInspection(null); setSelectedDatasetDetail(null); }
      await loadDatasets();
    } catch (err: any) { setErrorMsg(err.message || 'Delete failed'); }
  };

  // Filtered & searched list
  const filteredDatasets = datasets.filter(d => {
    const matchesType = filterType === 'all' || d.dataset_type === filterType;
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || d.name.toLowerCase().includes(q) || d.source?.toLowerCase().includes(q) || d.format?.toLowerCase().includes(q);
    return matchesType && matchesSearch;
  });

  const currentDataset = datasets.find(d => d.id === selectedDatasetId);

  // Schema compatibility check vs active model
  const modelFeatures = ['message_length', 'token_count', 'digit_ratio', 'entropy',
    'has_error', 'has_warning', 'has_auth', 'has_failed_auth', 'has_denied', 'has_ip', 'service'];
  const uploadedColumns = inspection?.columns.map(c => c.name) || [];
  const isSchemaCompatible = currentDataset?.is_builtin
    ? true
    : modelFeatures.every(f => uploadedColumns.includes(f));
  const missingFeatures = currentDataset?.is_builtin
    ? []
    : modelFeatures.filter(f => !uploadedColumns.includes(f));

  return (
    <div className="space-y-5">
      <PageHeader
        title="Dataset Manager & Schema Configuration"
        subtitle="Universal, dataset-independent ingestion supporting CSV, JSON, and JSONL with strict leakage validation"
        badge="Ingestion Layer"
        actions={
          <button
            onClick={() => setShowUploadDialog(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold font-mono cursor-pointer transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)]"
          >
            <Upload className="w-4 h-4" />
            Import Dataset File
          </button>
        }
      />

      {/* Notifications */}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />{errorMsg}
          <button className="ml-auto" onClick={() => setErrorMsg(null)}><X className="w-3.5 h-3.5" /></button>
        </div>
      )}
      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />{successMsg}
          <button className="ml-auto" onClick={() => setSuccessMsg(null)}><X className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {/* Summary bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Datasets', value: datasets.length, icon: <Database className="w-4 h-4 text-cyan-400" />, color: 'text-cyan-400' },
          { label: 'Built-in', value: datasets.filter(d => d.is_builtin).length, icon: <Lock className="w-4 h-4 text-violet-400" />, color: 'text-violet-400' },
          { label: 'User Uploaded', value: datasets.filter(d => !d.is_builtin).length, icon: <CloudUpload className="w-4 h-4 text-blue-400" />, color: 'text-blue-400' },
          { label: 'Approved', value: datasets.filter(d => d.is_approved).length, icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />, color: 'text-emerald-400' },
        ].map(stat => (
          <CyberCard key={stat.label} className="p-3 flex items-center gap-3" hoverEffect={false}>
            <div className="p-2 rounded-lg bg-white/5">{stat.icon}</div>
            <div>
              <div className={`text-lg font-bold font-mono ${stat.color}`}>{stat.value}</div>
              <div className="text-[11px] text-slate-400">{stat.label}</div>
            </div>
          </CyberCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: Dataset List */}
        <div className="space-y-3">
          {/* Search & Filter */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search datasets…"
                className="w-full pl-8 pr-3 py-2 bg-[#070D1A] border border-[#1E3050] rounded-xl text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400"
              />
              {searchQuery && <button onClick={() => setSearchQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2"><X className="w-3 h-3 text-slate-500 hover:text-white" /></button>}
            </div>
            <div className="flex gap-1.5">
              {(['all', 'builtin', 'uploaded'] as const).map(t => (
                <button key={t} onClick={() => setFilterType(t)}
                        className={`flex-1 py-1.5 rounded-lg text-[10px] font-mono font-semibold uppercase tracking-wider transition-all ${
                          filterType === t ? 'bg-cyan-950 border border-cyan-500/50 text-cyan-300' : 'bg-[#070D1A] border border-[#1E3050] text-slate-400 hover:text-slate-200'
                        }`}>
                  {t === 'all' ? 'All' : t === 'builtin' ? 'Built-in' : 'Uploaded'}
                </button>
              ))}
            </div>
          </div>

          {/* List header */}
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 uppercase tracking-wider px-1">
            <span>Available Datasets ({filteredDatasets.length})</span>
            <button onClick={loadDatasets} title="Refresh" className="hover:text-cyan-400 transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Dataset cards */}
          {loading && datasets.length === 0 ? (
            <CyberCard className="p-8 text-center" hoverEffect={false}>
              <RefreshCw className="w-6 h-6 mx-auto text-cyan-400 animate-spin mb-2" />
              <p className="text-xs text-slate-400 font-mono">Loading datasets…</p>
            </CyberCard>
          ) : filteredDatasets.length === 0 ? (
            <CyberCard className="p-8 text-center" hoverEffect={false}>
              <Database className="w-8 h-8 mx-auto text-slate-500 mb-2" />
              <p className="font-semibold text-xs text-white">
                {datasets.length === 0 ? 'No Datasets Found' : 'No matching datasets'}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                {datasets.length === 0
                  ? 'Upload a CSV, JSON, or JSONL file above to begin.'
                  : 'Try adjusting your search or filter.'}
              </p>
            </CyberCard>
          ) : (
            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {filteredDatasets.map(d => {
                const isSelected = d.id === selectedDatasetId;
                return (
                  <CyberCard
                    key={d.id}
                    onClick={() => selectDataset(d.id)}
                    className={`p-3.5 cursor-pointer ${isSelected ? 'border-cyan-400/80 bg-[#101D38] shadow-[0_0_20px_rgba(6,182,212,0.2)]' : ''}`}
                    glow={isSelected ? 'cyan' : 'none'}
                  >
                    <div className="flex items-start justify-between mb-1.5">
                      <div className="flex items-center gap-1.5">
                        {d.is_builtin
                          ? <Lock className="w-3 h-3 text-violet-400 shrink-0" />
                          : <CloudUpload className="w-3 h-3 text-blue-400 shrink-0" />
                        }
                        <span className="font-bold text-xs text-white truncate max-w-[150px]">{d.name}</span>
                      </div>
                      <span className={`text-[10px] font-mono uppercase font-semibold ${statusColor(d.status)}`}>
                        {d.status}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mb-1.5 truncate">
                      {d.source || d.filename}
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                      <span>{fmtNumber(d.row_count)} rows · {d.col_count} cols</span>
                      <div className="flex items-center gap-1">
                        {d.is_builtin && <span className="px-1.5 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-500/30 text-[9px]">BUILT-IN</span>}
                        {d.is_approved && <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 text-[9px]">✓</span>}
                      </div>
                    </div>
                    {isSelected && <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-400 opacity-80" />}
                  </CyberCard>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Detail Panel */}
        <div className="lg:col-span-2 space-y-5">
          {!currentDataset ? (
            <CyberCard className="p-16 text-center" hoverEffect={false}>
              <Info className="w-10 h-10 mx-auto text-slate-500 mb-3" />
              <h3 className="font-bold text-sm text-white">Select a Dataset to Inspect</h3>
              <p className="text-[11px] text-slate-400 mt-1">Structural inspection metrics, schema details, and feature configuration will appear here.</p>
            </CyberCard>
          ) : (
            <div className="space-y-5">
              {/* Dataset header card */}
              <CyberCard className="p-4" glow="cyan" hoverEffect={false}>
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      {currentDataset.is_builtin
                        ? <Lock className="w-4 h-4 text-violet-400" />
                        : <Database className="w-4 h-4 text-blue-400" />
                      }
                      <h3 className="font-extrabold text-sm text-white">{currentDataset.name}</h3>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase border ${
                        currentDataset.is_builtin ? 'bg-violet-950 text-violet-300 border-violet-500/30' : 'bg-blue-950 text-blue-300 border-blue-500/30'
                      }`}>
                        {currentDataset.is_builtin ? 'Built-in' : currentDataset.format}
                      </span>
                    </div>
                    {currentDataset.description && (
                      <p className="text-[11px] text-slate-400 mb-2 max-w-lg">{currentDataset.description}</p>
                    )}
                    <div className="flex flex-wrap gap-4 text-[11px] font-mono text-slate-400">
                      <span>Rows: <span className="text-white font-bold">{fmtNumber(currentDataset.row_count)}</span></span>
                      <span>Cols: <span className="text-white font-bold">{currentDataset.col_count}</span></span>
                      {currentDataset.train_rows != null && <span>Train: <span className="text-emerald-300 font-bold">{fmtNumber(currentDataset.train_rows)}</span></span>}
                      {currentDataset.val_rows != null && <span>Val: <span className="text-blue-300 font-bold">{fmtNumber(currentDataset.val_rows)}</span></span>}
                      {currentDataset.duplicate_rows != null && <span>Dupes: <span className={currentDataset.duplicate_rows > 0 ? 'text-amber-300 font-bold' : 'text-slate-300 font-bold'}>{fmtNumber(currentDataset.duplicate_rows)}</span></span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {currentDataset.is_approved ? (
                      <span className="px-3 py-1.5 rounded-xl bg-emerald-950 border border-emerald-500/50 text-emerald-300 text-xs font-mono font-semibold flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" /> APPROVED
                      </span>
                    ) : (
                      <button onClick={handleApprove} disabled={!validationResult?.is_valid}
                              className={`px-4 py-1.5 rounded-xl text-xs font-mono font-semibold flex items-center gap-1.5 transition-all ${
                                validationResult?.is_valid
                                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.4)]'
                                  : 'bg-slate-800/80 text-slate-500 cursor-not-allowed border border-[#1E3050]'
                              }`}>
                        <CheckCircle2 className="w-3.5 h-3.5" /> Approve for Training
                      </button>
                    )}
                    {!currentDataset.is_builtin && (
                      confirmDeleteId === currentDataset.id ? (
                        <div className="flex gap-2">
                          <button onClick={() => handleDelete(currentDataset.id)}
                                  className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> Confirm Delete
                          </button>
                          <button onClick={() => setConfirmDeleteId(null)}
                                  className="px-3 py-1.5 rounded-xl border border-[#1E3050] text-slate-400 text-xs font-mono">
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button onClick={() => setConfirmDeleteId(currentDataset.id)}
                                className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition-all">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )
                    )}
                  </div>
                </div>

                {/* Linked models */}
                {currentDataset.model_ids?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#1E3050]/60 flex flex-wrap gap-2 items-center">
                    <span className="text-[11px] font-mono text-slate-400">Linked Models:</span>
                    {currentDataset.model_ids.map(mid => (
                      <span key={mid} className="px-2 py-0.5 rounded bg-[#070D1A] border border-[#1E3050] text-[10px] font-mono text-slate-300">
                        {mid.includes('random_forest') ? '🌲 RF' : '⚡ XGB'} · {mid.split('_').slice(-2).join('_')}
                      </span>
                    ))}
                  </div>
                )}
              </CyberCard>

              {/* Schema compatibility warning for uploaded datasets */}
              {!currentDataset.is_builtin && inspection && (
                isSchemaCompatible ? (
                  <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
                    Schema is compatible with the active model's 11 expected features.
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-300 text-xs font-mono space-y-1">
                    <div className="flex items-center gap-2 font-semibold">
                      <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                      Feature schema incompatible with active model. Missing features:
                    </div>
                    <div className="flex flex-wrap gap-1.5 pl-6">
                      {missingFeatures.map(f => (
                        <span key={f} className="px-1.5 py-0.5 rounded bg-amber-950 border border-amber-500/30 text-[10px]">{f}</span>
                      ))}
                    </div>
                    <div className="text-[10px] pl-6 text-amber-400/80">Uploading this dataset will not trigger retraining automatically.</div>
                  </div>
                )
              )}

              {/* Tabs */}
              <div className="flex gap-1 border-b border-[#1E3050]">
                {([
                  { id: 'overview', label: 'Overview', icon: <Eye className="w-3.5 h-3.5" /> },
                  { id: 'schema', label: 'Schema', icon: <Layers className="w-3.5 h-3.5" /> },
                  { id: 'preview', label: 'Preview', icon: <BarChart2 className="w-3.5 h-3.5" /> },
                  ...(!currentDataset.is_builtin ? [{ id: 'configure', label: 'Configure', icon: <Tag className="w-3.5 h-3.5" /> }] : []),
                ] as { id: string; label: string; icon: React.ReactNode }[]).map(tab => (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id as any)}
                          className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-mono font-semibold transition-all border-b-2 -mb-px ${
                            activeTab === tab.id
                              ? 'border-cyan-400 text-cyan-300'
                              : 'border-transparent text-slate-400 hover:text-slate-200'
                          }`}>
                    {tab.icon}{tab.label}
                  </button>
                ))}
              </div>

              {/* Loading state for inspection */}
              {inspecting ? (
                <CyberCard className="p-10 text-center" hoverEffect={false}>
                  <RefreshCw className="w-6 h-6 mx-auto text-cyan-400 animate-spin mb-2" />
                  <p className="text-xs text-slate-400 font-mono">Inspecting dataset…</p>
                </CyberCard>
              ) : (
                <>
                  {/* Overview Tab */}
                  {activeTab === 'overview' && inspection && (
                    <div className="space-y-4">
                      {/* Stats grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {[
                          { label: 'Total Rows', value: fmtNumber(inspection.total_rows), color: 'text-white' },
                          { label: 'Columns', value: inspection.total_columns, color: 'text-cyan-300' },
                          { label: 'Duplicates', value: fmtNumber(inspection.duplicate_rows), color: (inspection.duplicate_rows || 0) > 0 ? 'text-amber-300' : 'text-emerald-300' },
                          { label: 'Target Col', value: currentDataset.target_column || (inspection.candidate_targets[0]?.column) || '—', color: 'text-violet-300' },
                        ].map(s => (
                          <CyberCard key={s.label} className="p-3 text-center" hoverEffect={false}>
                            <div className={`text-base font-bold font-mono ${s.color}`}>{s.value}</div>
                            <div className="text-[10px] text-slate-400 mt-0.5">{s.label}</div>
                          </CyberCard>
                        ))}
                      </div>

                      {/* Candidate targets */}
                      {inspection.candidate_targets.length > 0 && (
                        <CyberCard className="p-4" hoverEffect={false}>
                          <h4 className="text-xs font-bold text-white font-mono mb-3 flex items-center gap-2">
                            <Tag className="w-3.5 h-3.5 text-cyan-400" /> Candidate Target Columns
                          </h4>
                          <div className="space-y-3">
                            {inspection.candidate_targets.slice(0, 3).map(t => (
                              <div key={t.column} className="space-y-1.5">
                                <div className="flex items-center gap-2">
                                  <span className="text-[11px] font-mono text-white font-semibold">{t.column}</span>
                                  <span className="text-[10px] text-slate-400">({t.unique_count} unique)</span>
                                  {t.keyword_match && <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30 text-[9px]">KEYWORD MATCH</span>}
                                </div>
                                <div className="flex flex-wrap gap-1.5">
                                  {Object.entries(t.distribution).map(([val, count]) => (
                                    <span key={val} className="px-2 py-0.5 rounded bg-[#070D1A] border border-[#1E3050] text-[10px] font-mono text-slate-300">
                                      {val}: <span className="text-white font-semibold">{fmtNumber(count as number)}</span>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </CyberCard>
                      )}

                      {/* Built-in extra info */}
                      {currentDataset.is_builtin && (inspection as any).builtin_info && (
                        <CyberCard className="p-4" hoverEffect={false}>
                          <h4 className="text-xs font-bold text-white font-mono mb-3 flex items-center gap-2">
                            <Info className="w-3.5 h-3.5 text-cyan-400" /> Training Dataset Details
                          </h4>
                          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                            <div><span className="text-slate-400">Source:</span> <span className="text-white">{currentDataset.source}</span></div>
                            <div><span className="text-slate-400">Feature Count:</span> <span className="text-white">{(inspection as any).builtin_info?.feature_columns?.length}</span></div>
                            <div><span className="text-slate-400">Train Split:</span> <span className="text-emerald-300">{fmtNumber(currentDataset.train_rows)} rows (80%)</span></div>
                            <div><span className="text-slate-400">Val Split:</span> <span className="text-blue-300">{fmtNumber(currentDataset.val_rows)} rows (20%)</span></div>
                          </div>
                        </CyberCard>
                      )}
                    </div>
                  )}

                  {/* Schema Tab */}
                  {activeTab === 'schema' && inspection && (
                    <CyberCard className="p-4" hoverEffect={false}>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-xs font-bold text-white font-mono flex items-center gap-2">
                          <Layers className="w-3.5 h-3.5 text-cyan-400" /> Column Schema ({inspection.columns.length} columns)
                        </h4>
                        <div className="flex gap-2 text-[10px] font-mono text-slate-400">
                          <span className="text-blue-300">■ Numeric</span>
                          <span className="text-violet-300">■ Categorical</span>
                          <span className="text-amber-300">■ Boolean</span>
                        </div>
                      </div>
                      {inspection.columns.length > 0 ? (
                        <ColumnTable columns={inspection.columns} targetColumn={currentDataset.target_column || inspection.candidate_targets[0]?.column} />
                      ) : (
                        <p className="text-xs text-slate-400 font-mono text-center py-4">No column schema available.</p>
                      )}
                    </CyberCard>
                  )}

                  {/* Preview Tab */}
                  {activeTab === 'preview' && (
                    <CyberCard className="p-4" hoverEffect={false}>
                      <h4 className="text-xs font-bold text-white font-mono mb-3 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-cyan-400" /> Data Preview
                      </h4>
                      {currentDataset.is_builtin ? (
                        <div className="p-6 text-center rounded-xl bg-[#070D1A] border border-[#1E3050]">
                          <Lock className="w-6 h-6 mx-auto text-violet-400 mb-2" />
                          <p className="text-xs font-mono text-white">Row preview not available for built-in datasets.</p>
                          <p className="text-[11px] font-mono text-slate-400 mt-1">
                            Raw log files are stored on disk and not exposed for preview. Inspect the Schema tab for column definitions.
                          </p>
                        </div>
                      ) : inspection?.preview_records && inspection.preview_records.length > 0 ? (
                        <div className="overflow-x-auto rounded-xl border border-[#1E3050]">
                          <table className="w-full text-[10px] font-mono whitespace-nowrap">
                            <thead>
                              <tr className="border-b border-[#1E3050] bg-[#070D1A]">
                                <th className="px-2 py-1.5 text-slate-400 text-left">#</th>
                                {Object.keys(inspection.preview_records[0]).map(col => (
                                  <th key={col} className="px-2 py-1.5 text-slate-300 text-left">{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {inspection.preview_records.map((rec, i) => (
                                <tr key={i} className="border-b border-[#1E3050]/50 hover:bg-white/[0.02]">
                                  <td className="px-2 py-1.5 text-slate-500">{i + 1}</td>
                                  {Object.values(rec).map((val: any, j) => (
                                    <td key={j} className="px-2 py-1.5 text-white max-w-[180px] truncate">
                                      {val == null ? <span className="text-slate-600">null</span> : String(val)}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-xs text-slate-400 font-mono text-center py-4">No preview records available.</p>
                      )}
                    </CyberCard>
                  )}

                  {/* Configure Tab (uploaded only) */}
                  {activeTab === 'configure' && !currentDataset.is_builtin && inspection && (
                    <div className="space-y-5">
                      {/* Step 1: Target label */}
                      <CyberCard className="p-5 space-y-4" hoverEffect={false}>
                        <div className="flex items-center justify-between border-b border-[#1E3050]/60 pb-3">
                          <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 flex items-center justify-center text-[10px]">1</span>
                            Ground-Truth Target Label Mapping
                          </h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-[11px] font-mono text-slate-300 mb-1">Target Column</label>
                            <select value={targetColumn} onChange={e => handleTargetChange(e.target.value)}
                                    className="w-full bg-[#070D1A] border border-[#1E3050] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono">
                              <option value="">-- Select Target Column --</option>
                              {inspection.columns.map(c => (
                                <option key={c.name} value={c.name}>{c.name} ({c.unique_count} unique)</option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-[11px] font-mono text-slate-300 mb-1">Normal Value → 0</label>
                            <input type="text" placeholder="e.g. 0, Normal, Benign" value={normalValue} onChange={e => setNormalValue(e.target.value)}
                                   className="w-full bg-[#070D1A] border border-[#1E3050] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono" />
                          </div>
                          <div>
                            <label className="block text-[11px] font-mono text-slate-300 mb-1">Anomaly Value → 1</label>
                            <input type="text" placeholder="e.g. 1, Anomaly, Attack" value={anomalyValue} onChange={e => setAnomalyValue(e.target.value)}
                                   className="w-full bg-[#070D1A] border border-[#1E3050] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono" />
                          </div>
                        </div>
                        {targetColumn && (
                          <div className="p-3 rounded-xl bg-[#070D1A] border border-[#1E3050] text-xs font-mono">
                            <span className="text-slate-400 text-[11px] block mb-1.5">Distribution for "{targetColumn}":</span>
                            {(() => {
                              const cand = inspection.candidate_targets.find(t => t.column === targetColumn);
                              if (cand?.distribution) {
                                return (
                                  <div className="flex flex-wrap gap-2">
                                    {Object.entries(cand.distribution).map(([val, count]) => (
                                      <span key={val} className={`px-2 py-0.5 rounded text-[11px] ${
                                        val === normalValue ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50' :
                                        val === anomalyValue ? 'bg-rose-950 text-rose-300 border border-rose-500/50' :
                                        'bg-[#121E36] text-slate-400 border border-[#1E3050]'
                                      }`}>
                                        {val}: {fmtNumber(count as number)}
                                      </span>
                                    ))}
                                  </div>
                                );
                              }
                              return <span className="text-slate-500">Distribution unavailable.</span>;
                            })()}
                          </div>
                        )}
                      </CyberCard>

                      {/* Step 2: Feature selection */}
                      <CyberCard className="p-5 space-y-4" hoverEffect={false}>
                        <div className="flex items-center justify-between border-b border-[#1E3050]/60 pb-3">
                          <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 flex items-center justify-center text-[10px]">2</span>
                            Input Feature Selection ({selectedFeatures.length} selected)
                          </h4>
                          <span className="text-[11px] text-rose-400 font-mono">Target excluded to prevent leakage</span>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 max-h-52 overflow-y-auto pr-1">
                          {inspection.columns.map(c => {
                            const isTarget = c.name === targetColumn;
                            const isChecked = selectedFeatures.includes(c.name);
                            return (
                              <label key={c.name} className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                                isTarget ? 'bg-rose-950/20 border-rose-900/40 text-slate-500 cursor-not-allowed opacity-50' :
                                isChecked ? 'bg-cyan-950/40 border-cyan-500/50 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.1)]' :
                                'bg-[#070D1A] border-[#1E3050] text-slate-400 hover:border-slate-700'
                              }`}>
                                <input type="checkbox" checked={isChecked && !isTarget} disabled={isTarget} onChange={() => toggleFeature(c.name)}
                                       className="rounded border-[#1E3050] text-cyan-500 focus:ring-0" />
                                <div className="truncate">
                                  <div className="font-mono text-white text-[11px] truncate">{c.name}</div>
                                  <div className="text-[10px] text-slate-500 font-mono">{c.dtype} · {c.null_percent}% null</div>
                                </div>
                              </label>
                            );
                          })}
                        </div>
                      </CyberCard>

                      {/* Step 3: Split & validate */}
                      <CyberCard className="p-5 space-y-4" hoverEffect={false}>
                        <div className="flex items-center justify-between border-b border-[#1E3050]/60 pb-3">
                          <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 flex items-center justify-center text-[10px]">3</span>
                            Split Ratios & Validation
                          </h4>
                          <label className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                            <input type="checkbox" checked={stratified} onChange={e => setStratified(e.target.checked)} className="rounded text-cyan-500" />
                            Stratified
                          </label>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-xs font-mono">
                          {[
                            { label: 'Train', value: trainRatio, set: setTrainRatio, min: 0.5, max: 0.85 },
                            { label: 'Validation', value: valRatio, set: setValRatio, min: 0.05, max: 0.25 },
                            { label: 'Test', value: testRatio, set: setTestRatio, min: 0.05, max: 0.30 },
                          ].map(s => (
                            <div key={s.label}>
                              <label className="block text-slate-400 mb-1">{s.label}: {(s.value * 100).toFixed(0)}%</label>
                              <input type="range" min={s.min} max={s.max} step={0.05} value={s.value}
                                     onChange={e => s.set(parseFloat(e.target.value))} className="w-full accent-cyan-500" />
                            </div>
                          ))}
                        </div>

                        {validationResult && (
                          <div className={`p-4 rounded-xl border text-xs font-mono space-y-2 ${
                            validationResult.is_valid ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300' : 'bg-rose-950/40 border-rose-500/50 text-rose-300'
                          }`}>
                            <div className="font-bold flex items-center gap-2">
                              {validationResult.is_valid ? <Check className="w-4 h-4 text-emerald-400" /> : <X className="w-4 h-4 text-rose-400" />}
                              {validationResult.is_valid ? 'Validation Passed' : 'Validation Failed'}
                            </div>
                            {validationResult.errors.map((e, i) => <div key={i}>• {e}</div>)}
                            {validationResult.warnings.map((w, i) => <div key={i} className="text-amber-300">⚠ {w}</div>)}
                          </div>
                        )}

                        <div className="flex justify-end pt-1">
                          <button onClick={handleSaveAndValidate} disabled={validating}
                                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-semibold font-mono flex items-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all">
                            <CheckCircle2 className="w-4 h-4" />
                            {validating ? 'Validating…' : 'Save Configuration & Validate'}
                          </button>
                        </div>
                      </CyberCard>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Upload dialog */}
      {showUploadDialog && (
        <UploadDialog onClose={() => setShowUploadDialog(false)} onSuccess={handleUploadSuccess} />
      )}
    </div>
  );
};
