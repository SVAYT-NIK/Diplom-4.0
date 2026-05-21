"""
Unit tests for analytics modules.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.analytics.regression import (
    fit_ols_regression,
    fit_huber_regression,
    fit_ridge_regression,
    fit_lasso_regression,
)
from backend.analytics.anomaly import (
    detect_anomalies_ewma,
    detect_anomalies_isolation_forest,
    detect_anomalies_lof,
)
from backend.analytics.clustering import (
    cluster_kmeans,
    cluster_dbscan,
    cluster_gmm,
)
from backend.analytics.timeseries import (
    decompose_time_series,
    fit_holt_winters,
)
from backend.analytics.features import create_features


@pytest.fixture
def sample_regression_data():
    """Create sample data for regression tests."""
    np.random.seed(42)
    n = 100
    
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    t_out = np.random.normal(5, 10, n)  # Outdoor temperature
    q = 10 + 0.5 * np.maximum(0, 18 - t_out) + np.random.normal(0, 1, n)  # Heat consumption
    
    df = pd.DataFrame({
        'date': dates,
        'q': q,
        't_out': t_out,
    })
    
    return df


@pytest.fixture
def sample_feature_data():
    """Create sample data for feature engineering tests."""
    np.random.seed(42)
    n = 50
    
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    q = np.random.uniform(5, 15, n)
    
    df = pd.DataFrame({
        'date': dates,
        'q': q,
    })
    
    return df


class TestRegression:
    """Tests for regression models."""
    
    def test_ols_regression(self, sample_regression_data):
        """Test OLS regression fitting."""
        df = sample_regression_data
        
        # Create features
        df['hdd'] = np.maximum(0, 18 - df['t_out'])
        
        X = df[['hdd']]
        y = df['q']
        
        results = fit_ols_regression(X, y)
        
        assert results['model_type'] == 'ols'
        assert 'r_squared' in results
        assert 0 <= results['r_squared'] <= 1
        assert 'coefficients' in results
        assert 'intercept' in results['coefficients']
        assert 'hdd' in results['coefficients']
        assert len(results['residuals']) == len(y)
    
    def test_huber_regression(self, sample_regression_data):
        """Test Huber robust regression."""
        df = sample_regression_data
        df['hdd'] = np.maximum(0, 18 - df['t_out'])
        
        X = df[['hdd']]
        y = df['q']
        
        results = fit_huber_regression(X, y)
        
        assert results['model_type'] == 'huber'
        assert 'r_squared' in results
        assert 'coefficients' in results
        assert 'epsilon' in results
    
    def test_ridge_regression(self, sample_regression_data):
        """Test Ridge regression."""
        df = sample_regression_data
        df['hdd'] = np.maximum(0, 18 - df['t_out'])
        
        X = df[['hdd']]
        y = df['q']
        
        results = fit_ridge_regression(X, y, alpha=1.0)
        
        assert results['model_type'] == 'ridge'
        assert results['alpha'] == 1.0
        assert 'r_squared' in results
    
    def test_lasso_regression(self, sample_regression_data):
        """Test Lasso regression."""
        df = sample_regression_data
        df['hdd'] = np.maximum(0, 18 - df['t_out'])
        
        X = df[['hdd']]
        y = df['q']
        
        results = fit_lasso_regression(X, y, alpha=0.1)
        
        assert results['model_type'] == 'lasso'
        assert results['alpha'] == 0.1
        assert 'n_nonzero_coefs' in results


class TestAnomalyDetection:
    """Tests for anomaly detection algorithms."""
    
    def test_ewma_anomaly_detection(self, sample_feature_data):
        """Test EWMA anomaly detection."""
        df = sample_feature_data
        
        results = detect_anomalies_ewma(df, value_col='q', span=7)
        
        assert results['model_type'] == 'ewma'
        assert 'anomaly_flags' in results
        assert 'ewma_values' in results
        assert len(results['anomaly_flags']) == len(df)
        assert all(f in [0, 1] for f in results['anomaly_flags'])
    
    def test_isolation_forest(self, sample_feature_data):
        """Test Isolation Forest anomaly detection."""
        df = sample_feature_data
        X = df[['q']]
        
        results = detect_anomalies_isolation_forest(X, contamination=0.1)
        
        assert results['model_type'] == 'isolation_forest'
        assert 'labels' in results
        assert 'anomaly_scores' in results
        assert len(results['labels']) == len(df)
    
    def test_lof(self, sample_feature_data):
        """Test Local Outlier Factor."""
        df = sample_feature_data
        X = df[['q']]
        
        results = detect_anomalies_lof(X, n_neighbors=5)
        
        assert results['model_type'] == 'lof'
        assert 'outlier_mask' in results
        assert 'lof_scores' in results


class TestClustering:
    """Tests for clustering algorithms."""
    
    def test_kmeans(self, sample_feature_data):
        """Test K-Means clustering."""
        df = sample_feature_data
        X = df[['q']].copy()
        # Add more features for better clustering
        X['q_lag'] = X['q'].shift(1).fillna(X['q'].mean())
        X = X.dropna()
        
        results = cluster_kmeans(X, n_clusters=3)
        
        assert results['model_type'] == 'kmeans'
        assert 'cluster_labels' in results
        assert 'centroids' in results
        assert len(set(results['cluster_labels'])) == 3
        assert 'silhouette_score' in results
    
    def test_dbscan(self, sample_feature_data):
        """Test DBSCAN clustering."""
        df = sample_feature_data
        X = df[['q']].copy()
        X['q_std'] = (X['q'] - X['q'].mean()) / X['q'].std()
        
        results = cluster_dbscan(X, eps=2.0, min_samples=3)
        
        assert results['model_type'] == 'dbscan'
        assert 'labels' in results
        assert 'noise_mask' in results
    
    def test_gmm(self, sample_feature_data):
        """Test Gaussian Mixture Model clustering."""
        df = sample_feature_data
        X = df[['q']].copy()
        X['q_lag'] = X['q'].shift(1).fillna(X['q'].mean())
        X = X.dropna()
        
        results = cluster_gmm(X, n_components=3)
        
        assert results['model_type'] == 'gmm'
        assert 'cluster_labels' in results
        assert 'soft_assignments' in results
        assert 'bic' in results


class TestTimeSeries:
    """Tests for time series analysis."""
    
    def test_seasonal_decomposition(self, sample_feature_data):
        """Test seasonal decomposition."""
        df = sample_feature_data
        
        results = decompose_time_series(df, date_col='date', value_col='q', period=7)
        
        assert results['model_type'] == 'decomposition'
        if 'error' not in results:
            assert 'trend' in results
            assert 'seasonal' in results
            assert 'residual' in results
    
    def test_holt_winters(self, sample_feature_data):
        """Test Holt-Winters exponential smoothing."""
        df = sample_feature_data
        
        results = fit_holt_winters(df, date_col='date', value_col='q', seasonal_periods=7)
        
        assert results['model_type'] == 'holt_winters'
        if 'error' not in results:
            assert 'fitted_values' in results
            assert 'forecast' in results
            assert 'alpha' in results


class TestFeatures:
    """Tests for feature engineering."""
    
    def test_create_features(self, sample_feature_data):
        """Test feature creation."""
        df = sample_feature_data
        
        result = create_features(df, lag_days=[1, 7], rolling_windows=[7])
        
        assert 'date' in result.columns
        assert 'hdd' in result.columns
        assert 'month' in result.columns
        assert 'day_of_week' in result.columns
        assert 'month_sin' in result.columns
        assert 'month_cos' in result.columns
        assert 'q_lag_1' in result.columns
        assert 'q_lag_7' in result.columns
        assert 'q_rolling_mean_7' in result.columns
    
    def test_create_features_with_t_out(self):
        """Test feature creation with outdoor temperature."""
        np.random.seed(42)
        n = 30
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
        
        df = pd.DataFrame({
            'date': dates,
            'q': np.random.uniform(5, 15, n),
            't_out': np.random.normal(5, 10, n),
        })
        
        result = create_features(df)
        
        assert 'hdd' in result.columns
        # HDD should be calculated from t_out, not synthetic
        assert result['hdd'].notna().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
