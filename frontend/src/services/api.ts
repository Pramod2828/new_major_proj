const API_BASE = '/api';

export const api = {
  // System & Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async getSystemStatus() {
    const res = await fetch(`${API_BASE}/system/status`);
    return res.json();
  },

  async getDashboardStats(timeRange: string = '24h') {
    const res = await fetch(`${API_BASE}/dashboard/stats?time_range=${encodeURIComponent(timeRange)}`);
    return res.json();
  },

  // Datasets
  async uploadDataset(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Failed to upload dataset');
    }
    return res.json();
  },

  async listDatasets() {
    const res = await fetch(`${API_BASE}/datasets`);
    return res.json();
  },

  async getDataset(id: string) {
    const res = await fetch(`${API_BASE}/datasets/${id}`);
    if (!res.ok) throw new Error('Dataset not found');
    return res.json();
  },

  async inspectDataset(id: string) {
    const res = await fetch(`${API_BASE}/datasets/${id}/inspect`);
    if (!res.ok) throw new Error('Inspection failed');
    return res.json();
  },

  async configureDataset(id: string, config: any) {
    const res = await fetch(`${API_BASE}/datasets/${id}/configure`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Failed to configure dataset');
    }
    return res.json();
  },

  async validateDataset(id: string) {
    const res = await fetch(`${API_BASE}/datasets/${id}/validate`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Validation request failed');
    }
    return res.json();
  },

  async approveDataset(id: string) {
    const res = await fetch(`${API_BASE}/datasets/${id}/approve`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Approval request failed');
    }
    return res.json();
  },

  async deleteDataset(id: string) {
    const res = await fetch(`${API_BASE}/datasets/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Failed to delete dataset');
    }
    return res.json();
  },

  // Training
  async getTrainingGuard() {
    const res = await fetch(`${API_BASE}/training/guard`);
    return res.json();
  },

  async startTraining(params: {
    dataset_id: string;
    algorithms?: string[];
    rf_params?: any;
    xgb_params?: any;
    split_config?: any;
  }) {
    const res = await fetch(`${API_BASE}/training/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Training failed');
    }
    return res.json();
  },

  // Models
  async listModels() {
    const res = await fetch(`${API_BASE}/models`);
    return res.json();
  },

  async getActiveModel() {
    const res = await fetch(`${API_BASE}/models/active`);
    return res.json();
  },

  async getModel(id: string) {
    const res = await fetch(`${API_BASE}/models/${id}`);
    if (!res.ok) throw new Error('Model not found');
    return res.json();
  },

  async activateModel(id: string) {
    const res = await fetch(`${API_BASE}/models/${id}/activate`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Failed to activate model');
    }
    return res.json();
  },

  async compareModels(ids?: string[]) {
    const query = ids ? `?ids=${ids.join(',')}` : '';
    const res = await fetch(`${API_BASE}/models/compare${query}`);
    return res.json();
  },

  async getModelPolicy(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/policy`);
    return res.json();
  },

  async updateModelPolicy(modelId: string, policy: { threshold_normal: number; threshold_anomaly: number }) {
    const res = await fetch(`${API_BASE}/models/${modelId}/policy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(policy),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Failed to update policy');
    }
    return res.json();
  },

  // Inference & SHAP
  async predictLogs(logs: string[], computeShap: boolean = true) {
    const res = await fetch(`${API_BASE}/inference/predict-logs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ logs, compute_shap: computeShap }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Inference failed');
    }
    return res.json();
  },

  async predictFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/inference/predict-file`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'File prediction failed');
    }
    return res.json();
  },

  async getHistory(params?: {
    category?: string;
    is_anomaly?: boolean;
    time_range?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.is_anomaly !== undefined) query.set('is_anomaly', String(params.is_anomaly));
    if (params?.time_range) query.set('time_range', params.time_range);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));

    const res = await fetch(`${API_BASE}/inference/history?${query.toString()}`);
    return res.json();
  },

  async getPredictionDetail(id: string) {
    const res = await fetch(`${API_BASE}/inference/${id}`);
    if (!res.ok) throw new Error('Prediction not found');
    return res.json();
  },

  async getModelGlobalShap(modelId: string) {
    const res = await fetch(`${API_BASE}/models/${modelId}/shap-global`);
    if (!res.ok) throw new Error('Global SHAP fetch failed');
    return res.json();
  },

  // Reports
  getPdfReportUrl() {
    return `${API_BASE}/reports/pdf`;
  },

  getCsvReportUrl() {
    return `${API_BASE}/reports/csv`;
  },

  // Windows Event Collector API
  async getCollectorStatus() {
    const res = await fetch(`${API_BASE}/collector/status`);
    if (!res.ok) throw new Error('Failed to fetch collector status');
    return res.json();
  },

  async pauseCollector() {
    const res = await fetch(`${API_BASE}/collector/pause`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to pause collector');
    return res.json();
  },

  async resumeCollector() {
    const res = await fetch(`${API_BASE}/collector/resume`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to resume collector');
    return res.json();
  },

  async pollCollectorNow() {
    const res = await fetch(`${API_BASE}/collector/poll-now`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger collector poll');
    return res.json();
  },

  async getCollectorEvents(params?: {
    time_range?: string;
    category?: string;
    channel?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = new URLSearchParams();
    if (params?.time_range) query.set('time_range', params.time_range);
    if (params?.category) query.set('category', params.category);
    if (params?.channel) query.set('channel', params.channel);
    if (params?.search) query.set('search', params.search);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));

    const res = await fetch(`${API_BASE}/collector/events?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch collector events');
    return res.json();
  },

  async getCollectorEventDetail(id: string) {
    const res = await fetch(`${API_BASE}/collector/events/${id}`);
    if (!res.ok) throw new Error('Failed to fetch event detail');
    return res.json();
  },
};
