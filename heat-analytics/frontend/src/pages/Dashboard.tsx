// Dashboard page - main application page
import React, { useState, useEffect } from 'react';
import { getBuildings, runAnalysis, getAnalysisResults, getAnalysisStatus } from '../services/api';
import type { Building, UploadResponse, ResultsResponse, AnalysisRequest } from '../services/types';
import { UploadZone } from '../components/UploadZone';
import { BuildingSelector } from '../components/BuildingSelector';
import { TimeSeriesChart, ResidualHistogram, ClusterScatterPlot, AnomalyTable } from '../components/Charts';
import { ReportPanel } from '../components/ReportPanel';

const Dashboard: React.FC = () => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState<number | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load buildings on mount
  useEffect(() => {
    loadBuildings();
  }, []);

  // Poll for analysis results
  useEffect(() => {
    if (!currentRunId) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getAnalysisStatus(currentRunId);
        
        if (status.status === 'completed') {
          const resultsData = await getAnalysisResults(currentRunId);
          setResults(resultsData);
          setAnalysisRunning(false);
          clearInterval(pollInterval);
        } else if (status.status === 'failed') {
          setError(status.error || 'Анализ завершился ошибкой');
          setAnalysisRunning(false);
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [currentRunId]);

  const loadBuildings = async () => {
    try {
      const data = await getBuildings();
      setBuildings(data);
      if (data.length > 0 && !selectedBuildingId) {
        setSelectedBuildingId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load buildings:', err);
    }
  };

  const handleUploadSuccess = (response: UploadResponse) => {
    setUploadResponse(response);
    setUploadError(null);
    setCurrentRunId(null);
    setResults(null);
    
    // Reload buildings list
    loadBuildings();
    
    // Auto-select the new building
    setSelectedBuildingId(response.building_id);
  };

  const handleUploadError = (errorMessage: string) => {
    setUploadError(errorMessage);
    setUploadResponse(null);
  };

  const handleRunAnalysis = async () => {
    if (!selectedBuildingId) {
      setError('Выберите здание для анализа');
      return;
    }

    setAnalysisRunning(true);
    setError(null);
    setResults(null);

    try {
      const request: AnalysisRequest = {
        building_id: selectedBuildingId,
        models: ['ols', 'huber', 'isolation_forest', 'kmeans'],
      };

      const response = await runAnalysis(request);
      setCurrentRunId(response.run_id);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Ошибка при запуске анализа');
      setAnalysisRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Система анализа теплопотребления МКД
          </h1>
          <p className="mt-2 text-gray-600">
            Магистерская диссертация - Прототип системы энергетической аналитики
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-6">
          {/* Upload Section */}
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Загрузка данных</h2>
            <UploadZone onUploadSuccess={handleUploadSuccess} onError={handleUploadError} />
            
            {uploadResponse && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
                <p className="text-green-800">
                  ✓ Файл успешно загружен. Обработано строк: {uploadResponse.rows_parsed}
                </p>
                <p className="text-green-600 text-sm mt-1">
                  ID здания: {uploadResponse.building_id}
                </p>
              </div>
            )}
            
            {uploadError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-800">✗ {uploadError}</p>
              </div>
            )}
          </section>

          {/* Building Selection & Analysis Controls */}
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Параметры анализа</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <BuildingSelector
                buildings={buildings}
                selectedBuildingId={selectedBuildingId}
                onSelectBuilding={setSelectedBuildingId}
                disabled={analysisRunning}
              />
              
              <div className="flex flex-col justify-end">
                <button
                  onClick={handleRunAnalysis}
                  disabled={!selectedBuildingId || analysisRunning}
                  className={`
                    w-full px-6 py-3 rounded-md font-medium text-white transition-colors
                    ${!selectedBuildingId || analysisRunning
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'}
                  `}
                >
                  {analysisRunning ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Анализ выполняется...
                    </span>
                  ) : (
                    'Запустить анализ'
                  )}
                </button>
                
                <p className="mt-3 text-sm text-gray-500">
                  Будут применены модели: OLS, Huber, Isolation Forest, K-Means
                </p>
              </div>
            </div>
            
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-800">✗ {error}</p>
              </div>
            )}
          </section>

          {/* Results Section */}
          {results && (
            <>
              <ReportPanel results={results} runId={currentRunId!} />
              
              {/* Charts Grid */}
              <div className="grid md:grid-cols-2 gap-6">
                <TimeSeriesChart 
                  data={results.charts.timeseries}
                  title="Фактическое vs Прогнозное теплопотребление"
                />
                <ResidualHistogram 
                  data={results.charts.residuals}
                  title="Распределение остатков модели"
                />
              </div>
              
              <ClusterScatterPlot 
                data={results.charts.clusters}
                title="Кластеризация зданий по характеристикам"
              />
              
              <AnomalyTable 
                data={results.charts.anomalies}
                title="Обнаруженные аномалии"
              />
            </>
          )}

          {/* Empty State */}
          {!results && !analysisRunning && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className="mt-2 text-lg font-medium text-gray-900">Нет результатов анализа</h3>
              <p className="mt-1 text-gray-500">
                Загрузите данные Excel и запустите анализ для просмотра результатов
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            © 2024 Система анализа теплопотребления МКД. Магистерская диссертация.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
