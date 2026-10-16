export interface Dataset {
  id: string;
  name: string;
  filename: string;
  format: string;
  row_count: number;
  col_count: number;
  status: string;
  created_at: string;
  is_configured: boolean;
  is_approved: boolean;
  is_builtin: boolean;
  dataset_type: 'builtin' | 'uploaded';
  source: string;
  description: string;
  target_column?: string;
  columns: string[];
  model_ids: string[];
  train_rows?: number;
  val_rows?: number;
  duplicate_rows?: number;
}

export interface ColumnMeta {
  name: string;
  dtype: string;
  is_numeric: boolean;
  is_categorical: boolean;
  null_count: number;
  null_percent: number;
  unique_count: number;
  sample_values: any[];
  unique_values: any[];
}

export interface DatasetInspection {
  total_rows: number;
  total_columns: number;
  duplicate_rows: number;
  columns: ColumnMeta[];
  candidate_targets: Array<{
    column: string;
    unique_count: number;
    distribution: Record<string, number>;
    keyword_match: boolean;
  }>;
  candidate_timestamps: string[];
  candidate_messages: string[];
  preview_records: Record<string, any>[];
}

export interface ConfusionMatrix {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
  matrix: number[][];
}

export interface ModelMetrics {
  total_samples?: number;
  actual_anomalies?: number;
  actual_normals?: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  false_negative_rate?: number;
  specificity?: number;
  roc_auc: number | null;
  pr_auc: number | null;
  confusion_matrix: ConfusionMatrix;
  roc_curve: Array<{ fpr: number; tpr: number }>;
  pr_curve: Array<{ recall: number; precision: number }>;
  classification_policy?: {
    threshold_normal: number;
    threshold_anomaly: number;
    policy_name?: string;
    distribution?: {
      normal_count: number;
      normal_percent: number;
      medium_count: number;
      medium_percent: number;
      anomalous_count: number;
      anomalous_percent: number;
    };
  };
  training_duration_seconds?: number;
  test_samples?: number;
}

export interface Model {
  id: string;
  name: string;
  algorithm: 'random_forest' | 'xgboost';
  version: string;
  dataset_id?: string;
  dataset_name?: string;
  hyperparameters: Record<string, any>;
  metrics: ModelMetrics;
  feature_schema: {
    feature_columns: string[];
    transformed_feature_names: string[];
  };
  is_active: boolean;
  training_duration_seconds: number;
  created_at: string;
}

export interface ShapContribution {
  feature: string;
  contribution: number;
  abs_contribution: number;
  feature_value: any;
  direction: 'anomaly' | 'normal' | 'neutral';
}

export interface ShapData {
  available: boolean;
  base_value: number;
  contributions: ShapContribution[];
  top_anomaly_drivers: ShapContribution[];
  top_normal_drivers: ShapContribution[];
  error?: string | null;
}

export interface PredictionRecord {
  id: string;
  batch_id?: string;
  model_id?: string;
  model_name?: string;
  model_version?: string;
  raw_log: string;
  timestamp: string;
  hostname?: string;
  app_name?: string;
  service?: string;
  severity?: number;
  log_level?: string;
  prediction?: number | null;
  is_anomaly: boolean;
  category: 'Normal' | 'Medium' | 'Anomalous' | 'Unclassified';
  classification?: string;
  probability?: number | null;
  risk_score?: number | null;
  confidence?: number | null;
  explanation_summary?: string;
  observed_facts?: Record<string, any>;
  model_explanation?: Record<string, any>;
  security_interpretation?: string;
  parsed_fields?: Record<string, any>;
  features?: Record<string, any>;
  shap?: ShapData | null;
}

export interface DashboardStats {
  total_processed: number;
  total_logs: number;
  normal_count: number;
  normal_percentage: number;
  medium_count: number;
  medium_percentage: number;
  anomalous_count: number;
  anomalies_flagged: number;
  anomalous_percentage: number;
  unclassified_count: number;
  unclassified_percentage: number;
  classified_total: number;
  anomaly_rate?: number;
  time_range?: string;
  timeline_24h?: Array<{
    hour: string;
    normal: number;
    medium: number;
    anomalous: number;
    unclassified: number;
    total: number;
  }>;
  active_model: {
    id: string;
    name: string;
    algorithm: string;
    version: string;
  } | null;
  recent_activity: Array<{
    id: string;
    timestamp: string;
    category?: string;
    is_anomaly: boolean;
    probability?: number;
    risk_score?: number;
    confidence?: number;
    raw_log: string;
    model_name: string;
    explanation_summary?: string;
  }>;
  has_data: boolean;
}

export interface CollectorChannelStatus {
  status: 'Connected' | 'Permission Denied' | 'Error' | 'Initializing';
  last_record_id: number;
  last_poll_time: string | null;
  error: string | null;
}

export interface CollectorStatus {
  status: 'Connected' | 'Polling' | 'Paused' | 'Disconnected' | 'Error';
  is_running: boolean;
  is_paused: boolean;
  hostname: string;
  last_collection_time: string | null;
  poll_interval_seconds: number;
  channels: Record<string, CollectorChannelStatus>;
  diagnostic_message: string;
  counts_24h: {
    total: number;
    normal: number;
    medium: number;
    anomalous: number;
    unclassified: number;
  };
}

export interface CollectorEventRecord extends PredictionRecord {
  channel?: string;
  record_id?: number;
  event_id?: number;
  provider?: string;
  severity_label?: string;
  message?: string;
}

export interface CollectorEventsResponse {
  success: boolean;
  total: number;
  limit: number;
  offset: number;
  time_range: string;
  events: CollectorEventRecord[];
}
