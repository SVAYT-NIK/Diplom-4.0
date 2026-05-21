// API types and interfaces

export interface Building {
  id: number;
  address: string;
  area_m2: number;
  year_built: number;
  heating_type: string;
  norm_gcal_m2: number;
  created_at: string;
}

export interface DailyReading {
  id: number;
  building_id: number;
  date: string;
  t1: number | null;
  t2: number | null;
  p1: number | null;
  p2: number | null;
  v1: number | null;
  v2: number | null;
  m1: number | null;
  m2: number | null;
  q: number | null;
  dt: number | null;
  dv: number | null;
  dm: number | null;
  imbalance: number | null;
  ns_codes: string[];
  status: string;
  created_at: string;
}

export interface AnalysisRequest {
  building_id: number;
  models: string[];
}

export interface AnalysisResult {
  id: number;
  building_id: number;
  run_id: string;
  model_type: string;
  predicted_q: number | null;
  residual: number | null;
  anomaly_score: number | null;
  anomaly_flag: boolean;
  cluster_id: number | null;
  efficiency_class: string;
  norm_deviation_pct: number | null;
  params: Record<string, unknown>;
  created_at: string;
}

export interface UploadResponse {
  status: string;
  building_id: number;
  rows_parsed: number;
  message?: string;
}

export interface ResultsResponse {
  run_id: string;
  status: string;
  building_id: number;
  results: AnalysisResult[];
  charts: {
    timeseries: TimeSeriesPoint[];
    residuals: ResidualData[];
    clusters: ClusterPoint[];
    anomalies: AnomalyData[];
  };
  metrics: {
    r_squared: number | null;
    mae: number | null;
    rmse: number | null;
    anomaly_count: number;
    efficiency_class: string;
  };
  created_at: string;
}

export interface TimeSeriesPoint {
  date: string;
  actual: number | null;
  predicted: number | null;
  model?: string;
}

export interface ResidualData {
  date: string;
  residual: number;
  z_score: number;
}

export interface ClusterPoint {
  building_id: number;
  mean_q: number;
  beta1: number;
  intercept: number;
  r2: number;
  cv_q: number;
  norm_deviation: number;
  cluster_id: number;
}

export interface AnomalyData {
  date: string;
  actual_q: number;
  predicted_q: number;
  residual: number;
  anomaly_score: number;
  anomaly_flag: boolean;
  ns_codes: string[];
  detection_method: string;
}

export interface AnalysisStatus {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  error?: string;
}
