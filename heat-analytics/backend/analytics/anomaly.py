"""
Anomaly detection algorithms for heat consumption data.

Implements methods from section 2.2.iii of the diploma:
- EWMA (Exponentially Weighted Moving Average)
- Isolation Forest
- Local Outlier Factor (LOF)
"""
import logging
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor


logger = logging.getLogger(__name__)


def detect_anomalies_ewma(
    df: pd.DataFrame,
    value_col: str = 'q',
    span: int = 14,
    threshold_multiplier: float = 3.0,
) -> Dict[str, Any]:
    """
    Detect anomalies using EWMA (Exponentially Weighted Moving Average).
    
    Args:
        df: DataFrame with date and value columns
        value_col: Name of value column
        span: Span parameter for EWMA
        threshold_multiplier: Number of standard deviations for threshold
    
    Returns:
        Dictionary with EWMA series, anomaly flags, and trigger days
    """
    logger.info(f"Running EWMA anomaly detection (span={span}, threshold={threshold_multiplier}σ)")
    
    df = df.copy()
    
    if value_col not in df.columns:
        return {
            'model_type': 'ewma',
            'error': f'Column {value_col} not found',
        }
    
    # Calculate EWMA
    ewma = df[value_col].ewm(span=span, adjust=False).mean()
    
    # Calculate rolling standard deviation
    rolling_std = df[value_col].rolling(window=span, min_periods=1).std()
    
    # Calculate residuals
    residuals = df[value_col] - ewma
    
    # Calculate threshold
    threshold = threshold_multiplier * rolling_std
    
    # Flag anomalies
    anomaly_flags = (np.abs(residuals) > threshold).astype(int)
    
    # Find trigger days (dates where anomalies occur)
    trigger_days = df.loc[anomaly_flags == 1, 'date'].tolist() if 'date' in df.columns else []
    
    return {
        'model_type': 'ewma',
        'ewma_values': ewma.tolist(),
        'residuals': residuals.tolist(),
        'thresholds': threshold.tolist(),
        'anomaly_flags': anomaly_flags.tolist(),
        'trigger_days': trigger_days,
        'n_anomalies': int(anomaly_flags.sum()),
        'anomaly_rate': float(anomaly_flags.mean()),
    }


def detect_anomalies_isolation_forest(
    X: pd.DataFrame,
    contamination: float = 0.1,
    n_estimators: int = 100,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Detect anomalies using Isolation Forest algorithm.
    
    Args:
        X: Feature matrix
        contamination: Expected proportion of outliers
        n_estimators: Number of base estimators
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary with anomaly scores, labels, and contamination
    """
    logger.info(f"Running Isolation Forest (contamination={contamination}, n_estimators={n_estimators})")
    
    # Handle NaN values
    X_clean = X.dropna()
    
    if len(X_clean) < 10:
        return {
            'model_type': 'isolation_forest',
            'error': 'Insufficient data (need at least 10 samples)',
        }
    
    # Fit model
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    
    # Fit and predict
    model.fit(X_clean)
    predictions = model.predict(X_clean)
    scores = model.decision_function(X_clean)
    
    # Convert predictions to binary (1 = anomaly, -1 = normal in sklearn)
    labels = (predictions == -1).astype(int)
    
    # Normalize scores to [0, 1] range where higher = more anomalous
    scores_normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    anomaly_scores = 1 - scores_normalized  # Invert so higher = more anomalous
    
    return {
        'model_type': 'isolation_forest',
        'anomaly_scores': anomaly_scores.tolist(),
        'labels': labels.tolist(),
        'contamination': contamination,
        'n_estimators': n_estimators,
        'n_anomalies': int(labels.sum()),
        'anomaly_rate': float(labels.mean()),
        'feature_names': list(X_clean.columns),
    }


def detect_anomalies_lof(
    X: pd.DataFrame,
    n_neighbors: int = 20,
    contamination: float = 0.1,
) -> Dict[str, Any]:
    """
    Detect anomalies using Local Outlier Factor algorithm.
    
    Args:
        X: Feature matrix
        n_neighbors: Number of neighbors for LOF
        contamination: Expected proportion of outliers
    
    Returns:
        Dictionary with LOF scores, neighbor info, and outlier mask
    """
    logger.info(f"Running LOF (n_neighbors={n_neighbors}, contamination={contamination})")
    
    # Handle NaN values
    X_clean = X.dropna()
    
    if len(X_clean) < n_neighbors + 1:
        return {
            'model_type': 'lof',
            'error': f'Insufficient data (need at least {n_neighbors+1} samples)',
        }
    
    # Fit model
    model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        novelty=False,  # For outlier detection
        n_jobs=-1,
    )
    
    # Fit and predict
    predictions = model.fit_predict(X_clean)
    lof_scores = -model.negative_outlier_factor_  # Negate to make higher = more anomalous
    
    # Convert predictions to binary (1 = anomaly, -1 = normal in sklearn)
    outlier_mask = (predictions == -1).astype(int)
    
    # Normalize LOF scores
    lof_scores_normalized = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min() + 1e-10)
    
    return {
        'model_type': 'lof',
        'lof_scores': lof_scores_normalized.tolist(),
        'outlier_mask': outlier_mask.tolist(),
        'n_neighbors': n_neighbors,
        'contamination': contamination,
        'n_anomalies': int(outlier_mask.sum()),
        'anomaly_rate': float(outlier_mask.mean()),
        'feature_names': list(X_clean.columns),
    }


def consensus_anomaly_detection(
    results_list: List[Dict[str, Any]],
    min_agreement: int = 2,
) -> Dict[str, Any]:
    """
    Combine anomaly detection results using consensus voting.
    
    An anomaly is flagged only if at least min_agreement detectors agree.
    
    Args:
        results_list: List of anomaly detection result dictionaries
        min_agreement: Minimum number of detectors that must agree
    
    Returns:
        Dictionary with consensus anomaly flags and scores
    """
    logger.info(f"Computing consensus anomaly detection (min_agreement={min_agreement})")
    
    if not results_list:
        return {
            'model_type': 'consensus',
            'error': 'No results provided',
        }
    
    # Extract anomaly flags from each method
    all_flags = []
    all_scores = []
    
    for result in results_list:
        if 'anomaly_flags' in result:
            all_flags.append(np.array(result['anomaly_flags']))
        elif 'labels' in result:
            all_flags.append(np.array(result['labels']))
        elif 'outlier_mask' in result:
            all_flags.append(np.array(result['outlier_mask']))
        
        if 'anomaly_scores' in result:
            all_scores.append(np.array(result['anomaly_scores']))
        elif 'lof_scores' in result:
            all_scores.append(np.array(result['lof_scores']))
    
    if not all_flags:
        return {
            'model_type': 'consensus',
            'error': 'No anomaly flags found in results',
        }
    
    # Stack arrays
    flags_matrix = np.stack(all_flags)
    n_detectors = flags_matrix.shape[0]
    n_samples = flags_matrix.shape[1]
    
    # Count votes for each sample
    vote_counts = flags_matrix.sum(axis=0)
    
    # Consensus flags (samples with >= min_agreement votes)
    consensus_flags = (vote_counts >= min_agreement).astype(int)
    
    # Average anomaly scores
    if all_scores:
        scores_matrix = np.stack(all_scores)
        avg_scores = scores_matrix.mean(axis=0)
    else:
        avg_scores = vote_counts / n_detectors  # Use vote fraction as score
    
    return {
        'model_type': 'consensus',
        'consensus_flags': consensus_flags.tolist(),
        'avg_anomaly_scores': avg_scores.tolist(),
        'vote_counts': vote_counts.tolist(),
        'n_detectors': n_detectors,
        'min_agreement': min_agreement,
        'n_anomalies': int(consensus_flags.sum()),
        'anomaly_rate': float(consensus_flags.mean()),
    }
