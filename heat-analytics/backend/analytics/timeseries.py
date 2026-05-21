"""
Time series analysis for heat consumption data.

Implements methods from section 1.2.2 of the diploma:
- Seasonal Decomposition
- Holt-Winters Exponential Smoothing
- Prophet Forecasting
"""
import logging
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing


logger = logging.getLogger(__name__)


def decompose_time_series(
    df: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'q',
    period: int = 7,
    model: str = 'additive',
) -> Dict[str, Any]:
    """
    Perform seasonal decomposition of time series.
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column to decompose
        period: Period of seasonal component (e.g., 7 for weekly)
        model: Type of model ('additive' or 'multiplicative')
    
    Returns:
        Dictionary with trend, seasonal, residual components
    """
    logger.info(f"Performing seasonal decomposition (period={period}, model={model})")
    
    # Prepare data
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)[value_col]
    
    # Remove NaN values
    df = df.dropna()
    
    if len(df) < period * 2:
        logger.warning(f"Not enough data for decomposition (need at least {period*2} points)")
        return {
            'model_type': 'decomposition',
            'error': f'Insufficient data: {len(df)} < {period*2}',
        }
    
    # Perform decomposition
    try:
        result = seasonal_decompose(df, model=model, period=period, extrapolate_trend='freq')
        
        return {
            'model_type': 'decomposition',
            'period': period,
            'model': model,
            'observed': result.observed.dropna().tolist(),
            'trend': result.trend.dropna().tolist(),
            'seasonal': result.seasonal.dropna().tolist(),
            'residual': result.resid.dropna().tolist(),
            'dates': result.observed.dropna().index.strftime('%Y-%m-%d').tolist(),
        }
    except Exception as e:
        logger.error(f"Decomposition failed: {e}")
        return {
            'model_type': 'decomposition',
            'error': str(e),
        }


def fit_holt_winters(
    df: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'q',
    seasonal_periods: int = 7,
    forecast_steps: int = 7,
) -> Dict[str, Any]:
    """
    Fit Holt-Winters exponential smoothing model.
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column
        seasonal_periods: Number of periods in seasonal component
        forecast_steps: Number of steps to forecast
    
    Returns:
        Dictionary with fitted values, forecasts, and model parameters
    """
    logger.info(f"Fitting Holt-Winters model (seasonal_periods={seasonal_periods})")
    
    # Prepare data
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)[value_col]
    
    # Remove NaN values
    df = df.dropna()
    
    if len(df) < seasonal_periods * 2:
        logger.warning(f"Not enough data for Holt-Winters (need at least {seasonal_periods*2} points)")
        return {
            'model_type': 'holt_winters',
            'error': f'Insufficient data: {len(df)} < {seasonal_periods*2}',
        }
    
    try:
        # Fit model with additive seasonal component
        model = ExponentialSmoothing(
            df,
            trend='add',
            seasonal='add',
            seasonal_periods=seasonal_periods,
        )
        fitted = model.fit()
        
        # Forecast
        forecast = fitted.forecast(forecast_steps)
        
        # Get model parameters
        params = fitted.params
        
        return {
            'model_type': 'holt_winters',
            'fitted_values': fitted.fittedvalues.dropna().tolist(),
            'forecast': forecast.tolist(),
            'forecast_dates': forecast.index.strftime('%Y-%m-%d').tolist(),
            'alpha': float(params.smoothing_level),
            'beta': float(params.smoothing_trend),
            'gamma': float(params.smoothing_seasonal),
            'aic': float(fitted.aic),
            'bic': float(fitted.bic),
            'rmse': float(np.sqrt(fitted.mse)),
            'dates': fitted.fittedvalues.dropna().index.strftime('%Y-%m-%d').tolist(),
        }
        
    except Exception as e:
        logger.error(f"Holt-Winters fitting failed: {e}")
        return {
            'model_type': 'holt_winters',
            'error': str(e),
        }


def fit_prophet_model(
    df: pd.DataFrame,
    date_col: str = 'date',
    value_col: str = 'q',
    forecast_steps: int = 7,
    changepoint_prior_scale: float = 0.05,
    seasonality_prior_scale: float = 10.0,
) -> Dict[str, Any]:
    """
    Fit Facebook Prophet forecasting model.
    
    Args:
        df: DataFrame with date and value columns
        date_col: Name of date column
        value_col: Name of value column
        forecast_steps: Number of days to forecast
        changepoint_prior_scale: Regularization parameter for trend changes
        seasonality_prior_scale: Regularization parameter for seasonality
    
    Returns:
        Dictionary with forecasts and uncertainty intervals
    """
    logger.info("Fitting Prophet model")
    
    try:
        from prophet import Prophet
    except ImportError:
        logger.warning("Prophet not installed, skipping")
        return {
            'model_type': 'prophet',
            'error': 'Prophet library not available',
        }
    
    # Prepare data for Prophet (requires 'ds' and 'y' columns)
    df = df.copy()
    df = df[[date_col, value_col]].copy()
    df.columns = ['ds', 'y']
    df['ds'] = pd.to_datetime(df['ds'])
    df = df.dropna()
    
    if len(df) < 30:
        logger.warning("Not enough data for Prophet (need at least 30 points)")
        return {
            'model_type': 'prophet',
            'error': 'Insufficient data: need at least 30 points',
        }
    
    try:
        # Initialize and fit model
        model = Prophet(
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
        )
        model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=forecast_steps)
        forecast = model.predict(future)
        
        # Extract components
        forecast_dict = {
            'model_type': 'prophet',
            'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_steps).to_dict('records'),
            'fitted_values': forecast[['ds', 'yhat']].head(len(df)).to_dict('records'),
            'changepoints': model.changepoints.strftime('%Y-%m-%d').tolist()[:10],  # First 10
        }
        
        # Add component effects if available
        if 'trend' in forecast.columns:
            forecast_dict['trend'] = forecast[['ds', 'trend']].tail(forecast_steps).to_dict('records')
        if 'weekly' in forecast.columns:
            forecast_dict['weekly_effect'] = forecast[['ds', 'weekly']].tail(forecast_steps).to_dict('records')
        if 'yearly' in forecast.columns:
            forecast_dict['yearly_effect'] = forecast[['ds', 'yearly']].tail(forecast_steps).to_dict('records')
        
        return forecast_dict
        
    except Exception as e:
        logger.error(f"Prophet fitting failed: {e}")
        return {
            'model_type': 'prophet',
            'error': str(e),
        }
