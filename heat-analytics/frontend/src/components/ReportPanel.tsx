// ReportPanel component for displaying analysis results and exporting reports
import React from 'react';
import { exportReport } from '../services/api';
import type { ResultsResponse, Metrics } from '../services/types';

interface ReportPanelProps {
  results: ResultsResponse | null;
  runId: string;
}

export const ReportPanel: React.FC<ReportPanelProps> = ({ results, runId }) => {
  const [exporting, setExporting] = React.useState(false);

  const handleExport = async (format: 'pdf' | 'csv') => {
    setExporting(true);
    try {
      const blob = await exportReport(runId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${runId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export error:', error);
      alert('Ошибка при экспорте отчёта');
    } finally {
      setExporting(false);
    }
  };

  if (!results) {
    return null;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-gray-800">Результаты анализа</h3>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {exporting ? 'Экспорт...' : 'Скачать PDF'}
          </button>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {exporting ? 'Экспорт...' : 'Скачать CSV'}
          </button>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <span className={`
          inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
          ${results.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
          ${results.status === 'running' ? 'bg-blue-100 text-blue-800' : ''}
          ${results.status === 'failed' ? 'bg-red-100 text-red-800' : ''}
          ${results.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : ''}
        `}>
          Статус: {results.status === 'completed' ? 'Завершено' : 
                   results.status === 'running' ? 'Выполняется' :
                   results.status === 'failed' ? 'Ошибка' : 'Ожидание'}
        </span>
        <span className="ml-3 text-sm text-gray-500">
          Run ID: {runId}
        </span>
      </div>

      {/* Metrics Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">R²</p>
          <p className="text-2xl font-bold text-blue-900">
            {results.metrics.r_squared?.toFixed(3) ?? '-'}
          </p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg">
          <p className="text-sm text-gray-600">MAE (Гкал)</p>
          <p className="text-2xl font-bold text-purple-900">
            {results.metrics.mae?.toFixed(3) ?? '-'}
          </p>
        </div>
        <div className="p-4 bg-indigo-50 rounded-lg">
          <p className="text-sm text-gray-600">RMSE (Гкал)</p>
          <p className="text-2xl font-bold text-indigo-900">
            {results.metrics.rmse?.toFixed(3) ?? '-'}
          </p>
        </div>
        <div className="p-4 bg-orange-50 rounded-lg">
          <p className="text-sm text-gray-600">Аномалий</p>
          <p className="text-2xl font-bold text-orange-900">
            {results.metrics.anomaly_count}
          </p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-gray-600">Класс эффективности</p>
          <p className="text-lg font-bold text-green-900">
            {results.metrics.efficiency_class}
          </p>
        </div>
      </div>

      {/* Additional Info */}
      <div className="border-t pt-4">
        <p className="text-sm text-gray-500">
          Дата создания: {new Date(results.created_at).toLocaleString('ru-RU')}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Количество записей: {results.results.length}
        </p>
      </div>
    </div>
  );
};

export default ReportPanel;
