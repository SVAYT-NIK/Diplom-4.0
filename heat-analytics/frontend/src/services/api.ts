// API client for Heat Analytics backend
import axios from 'axios';
import type {
  Building,
  UploadResponse,
  AnalysisRequest,
  ResultsResponse,
  AnalysisStatus,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Buildings API
export const getBuildings = async (): Promise<Building[]> => {
  const response = await api.get<Building[]>('/buildings');
  return response.data;
};

export const getBuilding = async (id: number): Promise<Building> => {
  const response = await api.get<Building>(`/buildings/${id}`);
  return response.data;
};

// Upload API
export const uploadExcel = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Analysis API
export const runAnalysis = async (request: AnalysisRequest): Promise<{ run_id: string }> => {
  const response = await api.post<{ run_id: string }>('/analyze', request);
  return response.data;
};

export const getAnalysisResults = async (runId: string): Promise<ResultsResponse> => {
  const response = await api.get<ResultsResponse>(`/results/${runId}`);
  return response.data;
};

export const getAnalysisStatus = async (runId: string): Promise<AnalysisStatus> => {
  const response = await api.get<AnalysisStatus>(`/analyze/status/${runId}`);
  return response.data;
};

// Export API
export const exportReport = async (runId: string, format: 'pdf' | 'csv' = 'pdf'): Promise<Blob> => {
  const response = await api.post(
    '/export',
    { run_id: runId, format },
    {
      responseType: 'blob',
    }
  );
  return response.data;
};

export default api;
