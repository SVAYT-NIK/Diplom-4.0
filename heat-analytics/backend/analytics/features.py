"""
Feature engineering for heat consumption analysis.
"""
import logging
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


def create_features(
    df: pd.DataFrame,
    lag_days: List[int] = [1, 2, 3, 7],
    rolling_windows: List[int] = [7, 14, 30],
    hdd_base_temp: float = 18.0,
) -> pd.DataFrame:
    """
    Create features for heat consumption modeling.
    
    Args:
        df: DataFrame with columns ['date', 'q', 't_out'] (t_out is optional)
        lag_days: List of lag days to create
        rolling_windows: List of rolling window sizes
        hdd_base_temp: Base temperature for heating degree days
    
    Returns:
        DataFrame with additional feature columns
    """
    df = df.copy()
    
    # Ensure date is datetime and sorted
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Create Heating Degree Days (HDD) if t_out is available
    if 't_out' in df.columns:
        df['hdd'] = np.maximum(0, hdd_base_temp - df['t_out'])
    else:
        # Use placeholder HDD based on date (winter = higher HDD)
        df['day_of_year'] = df['date'].dt.dayofyear
        # Simplified HDD model: higher in winter months
        df['hdd'] = np.where(
            (df['day_of_year'] < 90) | (df['day_of_year'] > 330),  # Winter
            np.random.uniform(15, 25, len(df)),  # High HDD
            np.random.uniform(0, 10, len(df))     # Low HDD
        )
        logger.warning("Using synthetic HDD values - external weather data not available")
    
    # Lag features for Q
    if 'q' in df.columns:
        for lag in lag_days:
            df[f'q_lag_{lag}'] = df['q'].shift(lag)
        
        # Rolling statistics
        for window in rolling_windows:
            df[f'q_rolling_mean_{window}'] = df['q'].rolling(window=window, min_periods=1).mean()
            df[f'q_rolling_std_{window}'] = df['q'].rolling(window=window, min_periods=1).std()
        
        # Rate of change
        df['q_diff'] = df['q'].diff()
        df['q_pct_change'] = df['q'].pct_change()
    
    # Time-based features
    df['month'] = df['date'].dt.month
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['quarter'] = df['date'].dt.quarter
    
    # Seasonal encoding (cyclical)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    return df


def prepare_regression_data(
    df: pd.DataFrame,
    target_col: str = 'q',
    feature_cols: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Prepare data for regression modeling.
    
    Args:
        df: DataFrame with features
        target_col: Name of target column
        feature_cols: List of feature columns to use (None = auto-detect)
    
    Returns:
        Tuple of (X, y) DataFrames
    """
    df = df.copy()
    
    # Drop rows with NaN in target
    df = df.dropna(subset=[target_col])
    
    # Auto-detect feature columns if not specified
    if feature_cols is None:
        exclude_cols = ['date', target_col, 'q_diff', 'q_pct_change']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Select features
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # Drop rows with NaN in features
    valid_idx = ~(X.isna().any(axis=1))
    X = X[valid_idx].reset_index(drop=True)
    y = y[valid_idx].reset_index(drop=True)
    
    return X, y


def get_feature_importance_from_model(model, feature_names: List[str]) -> pd.DataFrame:
    """
    Extract feature importance from a trained model.
    
    Args:
        model: Trained sklearn model with coef_ or feature_importances_
        feature_names: List of feature names
    
    Returns:
        DataFrame with feature importances
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_)
        if len(importances.shape) > 1:
            importances = importances.flatten()
    else:
        logger.warning("Model does not have coef_ or feature_importances_")
        return pd.DataFrame({'feature': feature_names, 'importance': 0})
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    return importance_df
