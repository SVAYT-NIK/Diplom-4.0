// Charts component with Recharts visualizations
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';
import type { TimeSeriesPoint, ResidualData, ClusterPoint, AnomalyData } from '../services/types';

interface TimeSeriesChartProps {
  data: TimeSeriesPoint[];
  title?: string;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ data, title = 'Фактическое vs Прогнозное теплопотребление' }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={(value) => new Date(value).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
            />
            <YAxis label={{ value: 'Гкал', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              labelFormatter={(value) => new Date(value).toLocaleDateString('ru-RU')}
              formatter={(value: number) => [value.toFixed(3), '']}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="actual" 
              name="Фактическое Q" 
              stroke="#2563eb" 
              strokeWidth={2}
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="predicted" 
              name="Прогноз Q" 
              stroke="#dc2626" 
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

interface ResidualHistogramProps {
  data: ResidualData[];
  title?: string;
}

export const ResidualHistogram: React.FC<ResidualHistogramProps> = ({ data, title = 'Распределение остатков' }) => {
  // Bin the residuals for histogram
  const binSize = 0.5;
  const bins = new Map<number, number>();
  
  data.forEach((point) => {
    const bin = Math.floor(point.residual / binSize) * binSize;
    bins.set(bin, (bins.get(bin) || 0) + 1);
  });

  const histogramData = Array.from(bins.entries())
    .map(([residual, count]) => ({
      residual: residual.toFixed(2),
      count,
      z_score: residual / binSize,
    }))
    .sort((a, b) => parseFloat(a.residual) - parseFloat(b.residual));

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={histogramData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="residual" label={{ value: 'Остаток (Гкал)', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Частота', angle: 90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" name="Частота" fill="#6366f1" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

interface ClusterScatterPlotProps {
  data: ClusterPoint[];
  title?: string;
}

export const ClusterScatterPlot: React.FC<ClusterScatterPlotProps> = ({ data, title = 'Кластеризация МКД' }) => {
  const colors = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed', '#db2777'];

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="mean_q" 
              name="Среднее Q" 
              label={{ value: 'Среднее Q (Гкал)', position: 'insideBottom', offset: -5 }} 
            />
            <YAxis 
              type="number" 
              dataKey="beta1" 
              name="Бета-коэф." 
              label={{ value: 'β₁ (температурная чувствительность)', angle: 90, position: 'insideLeft' }} 
            />
            <ZAxis type="number" range={[100, 500]} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            {Array.from(new Set(data.map(d => d.cluster_id))).map((clusterId, index) => (
              <Scatter
                key={clusterId}
                name={`Кластер ${clusterId}`}
                data={data.filter(d => d.cluster_id === clusterId)}
                fill={colors[index % colors.length]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

interface AnomalyTableProps {
  data: AnomalyData[];
  title?: string;
}

export const AnomalyTable: React.FC<AnomalyTableProps> = ({ data, title = 'Обнаруженные аномалии' }) => {
  if (data.length === 0) {
    return (
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
        <p className="text-gray-500 text-center py-8">Аномалии не обнаружены</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow overflow-hidden">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Дата</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Факт Q (Гкал)</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Прогноз Q (Гкал)</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Остаток</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Метод</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">НС коды</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((anomaly, index) => (
              <tr key={index} className={anomaly.anomaly_flag ? 'bg-red-50' : ''}>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {new Date(anomaly.date).toLocaleDateString('ru-RU')}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {anomaly.actual_q?.toFixed(3)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {anomaly.predicted_q?.toFixed(3)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {anomaly.residual?.toFixed(3)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {anomaly.anomaly_score?.toFixed(3)}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {anomaly.detection_method}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                  {anomaly.ns_codes?.join(', ') || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default {
  TimeSeriesChart,
  ResidualHistogram,
  ClusterScatterPlot,
  AnomalyTable,
};
