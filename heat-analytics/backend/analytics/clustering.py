"""
Clustering algorithms for heat consumption analysis.

Implements methods from section 1.2.3 of the diploma:
- K-Means++
- DBSCAN
- Gaussian Mixture Models (GMM)
"""
import logging
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score


logger = logging.getLogger(__name__)


def cluster_kmeans(
    X: pd.DataFrame,
    n_clusters: int = 4,
    init: str = 'k-means++',
    n_init: int = 10,
    max_iter: int = 300,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Perform K-Means clustering with k-means++ initialization.
    
    Args:
        X: Feature matrix
        n_clusters: Number of clusters
        init: Initialization method ('k-means++' or 'random')
        n_init: Number of times to run algorithm with different centroids
        max_iter: Maximum iterations per run
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary with cluster labels, centroids, inertia, silhouette score
    """
    logger.info(f"Running K-Means clustering (k={n_clusters}, init={init})")
    
    # Handle NaN values
    X_clean = X.dropna()
    
    if len(X_clean) < n_clusters:
        return {
            'model_type': 'kmeans',
            'error': f'Insufficient data (need at least {n_clusters} samples)',
        }
    
    # Fit model
    model = KMeans(
        n_clusters=n_clusters,
        init=init,
        n_init=n_init,
        max_iter=max_iter,
        random_state=random_state,
        n_jobs=-1,
    )
    
    labels = model.fit_predict(X_clean)
    
    # Calculate silhouette score (requires at least 2 clusters and more samples than clusters)
    if n_clusters >= 2 and len(X_clean) > n_clusters:
        try:
            sil_score = silhouette_score(X_clean, labels)
        except Exception:
            sil_score = None
    else:
        sil_score = None
    
    return {
        'model_type': 'kmeans',
        'cluster_labels': labels.tolist(),
        'centroids': model.cluster_centers_.tolist(),
        'inertia': float(model.inertia_),
        'silhouette_score': sil_score,
        'n_clusters': n_clusters,
        'n_iterations': int(model.n_iter_),
        'feature_names': list(X_clean.columns),
        'cluster_sizes': [int((labels == i).sum()) for i in range(n_clusters)],
    }


def cluster_dbscan(
    X: pd.DataFrame,
    eps: float = 0.5,
    min_samples: int = 5,
    metric: str = 'euclidean',
) -> Dict[str, Any]:
    """
    Perform DBSCAN density-based clustering.
    
    Args:
        X: Feature matrix
        eps: Maximum distance between two samples to be considered neighbors
        min_samples: Minimum samples in a neighborhood to form a core point
        metric: Distance metric
    
    Returns:
        Dictionary with labels, core samples, noise mask
    """
    logger.info(f"Running DBSCAN clustering (eps={eps}, min_samples={min_samples})")
    
    # Handle NaN values
    X_clean = X.dropna()
    
    if len(X_clean) < min_samples:
        return {
            'model_type': 'dbscan',
            'error': f'Insufficient data (need at least {min_samples} samples)',
        }
    
    # Fit model
    model = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric=metric,
        n_jobs=-1,
    )
    
    labels = model.fit_predict(X_clean)
    
    # Identify core samples and noise
    core_mask = model.core_sample_indices_
    noise_mask = (labels == -1).astype(int)
    
    # Count clusters (excluding noise)
    unique_labels = set(labels)
    n_clusters = len([l for l in unique_labels if l >= 0])
    
    # Calculate silhouette score only if there are at least 2 clusters
    if n_clusters >= 2:
        try:
            non_noise_idx = labels != -1
            if non_noise_idx.sum() > 1:
                sil_score = silhouette_score(X_clean[non_noise_idx], labels[non_noise_idx])
            else:
                sil_score = None
        except Exception:
            sil_score = None
    else:
        sil_score = None
    
    return {
        'model_type': 'dbscan',
        'labels': labels.tolist(),
        'core_samples': core_mask.tolist() if len(core_mask) < 100 else core_mask[:100].tolist(),
        'noise_mask': noise_mask.tolist(),
        'eps': eps,
        'min_samples': min_samples,
        'silhouette_score': sil_score,
        'n_clusters': n_clusters,
        'n_noise_points': int(noise_mask.sum()),
        'feature_names': list(X_clean.columns),
    }


def cluster_gmm(
    X: pd.DataFrame,
    n_components: int = 4,
    covariance_type: str = 'full',
    max_iter: int = 100,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Perform Gaussian Mixture Model clustering.
    
    Args:
        X: Feature matrix
        n_components: Number of mixture components
        covariance_type: Type of covariance parameters ('full', 'tied', 'diag', 'spherical')
        max_iter: Maximum number of EM iterations
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary with soft assignments, log likelihood, BIC
    """
    logger.info(f"Running GMM clustering (n_components={n_components}, covariance={covariance_type})")
    
    # Handle NaN values
    X_clean = X.dropna()
    
    if len(X_clean) < n_components:
        return {
            'model_type': 'gmm',
            'error': f'Insufficient data (need at least {n_components} samples)',
        }
    
    # Fit model
    model = GaussianMixture(
        n_components=n_components,
        covariance_type=covariance_type,
        max_iter=max_iter,
        random_state=random_state,
        n_init=3,
    )
    
    labels = model.fit_predict(X_clean)
    
    # Get soft assignments (probabilities)
    soft_assignments = model.predict_proba(X_clean)
    
    # Calculate silhouette score
    if n_components >= 2 and len(X_clean) > n_components:
        try:
            sil_score = silhouette_score(X_clean, labels)
        except Exception:
            sil_score = None
    else:
        sil_score = None
    
    return {
        'model_type': 'gmm',
        'cluster_labels': labels.tolist(),
        'soft_assignments': soft_assignments.tolist(),
        'log_likelihood': float(model.score(X_clean) * len(X_clean)),
        'bic': float(model.bic(X_clean)),
        'aic': float(model.aic(X_clean)),
        'converged': model.converged_,
        'n_iter': int(model.n_iter_),
        'n_components': n_components,
        'covariance_type': covariance_type,
        'silhouette_score': sil_score,
        'feature_names': list(X_clean.columns),
        'cluster_sizes': [int((labels == i).sum()) for i in range(n_components)],
    }


def prepare_clustering_features(
    df: pd.DataFrame,
    readings_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Prepare feature vector for clustering buildings.
    
    Features include:
    - mean_Q: Average heat consumption
    - beta1: Slope from regression
    - intercept: Intercept from regression
    - R2: R-squared from regression
    - cv_Q: Coefficient of variation of Q
    - norm_deviation: Deviation from normative consumption
    
    Args:
        df: DataFrame with aggregated building statistics
        readings_df: Optional raw readings for additional features
    
    Returns:
        DataFrame with clustering features
    """
    logger.info("Preparing clustering features")
    
    features = {}
    
    # Basic statistics from aggregated data
    required_cols = ['mean_q', 'beta1', 'intercept', 'r_squared', 'cv_q', 'norm_deviation']
    
    for col in required_cols:
        if col in df.columns:
            features[col] = df[col].values
        else:
            logger.warning(f"Missing feature column: {col}")
    
    if not features:
        raise ValueError("No valid features found for clustering")
    
    # Create feature DataFrame
    feature_df = pd.DataFrame(features)
    
    # Drop rows with NaN
    feature_df = feature_df.dropna()
    
    return feature_df
