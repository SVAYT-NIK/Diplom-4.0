"""
Regression models for heat consumption analysis.

Implements methods from section 1.2.1 of the diploma:
- Linear Regression (OLS)
- Robust Regression (Huber)
- Ridge/Lasso Regularization
- Quantile Regression
"""
import logging
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import Ridge, Lasso, HuberRegressor
from scipy import stats


logger = logging.getLogger(__name__)


def fit_ols_regression(
    X: pd.DataFrame,
    y: pd.Series,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """
    Fit Ordinary Least Squares (OLS) regression model.
    
    Args:
        X: Feature matrix
        y: Target vector
        confidence_level: Confidence level for intervals (default 0.95)
    
    Returns:
        Dictionary with coefficients, R², p-values, confidence intervals
    """
    logger.info("Fitting OLS regression model")
    
    # Add constant term
    X_const = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X_const)
    results = model.fit()
    
    # Extract results
    coef_names = ['intercept'] + list(X.columns)
    coefficients = results.params.values
    std_errors = results.bse.values
    p_values = results.pvalues.values
    
    # Confidence intervals
    alpha = 1 - confidence_level
    t_crit = results.tvalues.apply(lambda x: stats.t.ppf(1 - alpha/2, results.df_resid))
    ci_lower = results.params - t_crit * results.bse
    ci_upper = results.params + t_crit * results.bse
    
    return {
        'model_type': 'ols',
        'coefficients': dict(zip(coef_names, coefficients.tolist())),
        'std_errors': dict(zip(coef_names, std_errors.tolist())),
        'p_values': dict(zip(coef_names, p_values.tolist())),
        'r_squared': results.rsquared,
        'r_squared_adj': results.rsquared_adj,
        'confidence_intervals': {
            'lower': dict(zip(coef_names, ci_lower.tolist())),
            'upper': dict(zip(coef_names, ci_upper.tolist())),
        },
        'aic': results.aic,
        'bic': results.bic,
        'residuals': results.resid.tolist(),
        'fitted_values': results.fittedvalues.tolist(),
        'n_observations': int(results.nobs),
        'df_resid': int(results.df_resid),
    }


def fit_huber_regression(
    X: pd.DataFrame,
    y: pd.Series,
    epsilon: float = 1.35,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """
    Fit Huber Robust Regression model.
    
    Args:
        X: Feature matrix
        y: Target vector
        epsilon: Epsilon parameter for Huber loss
        max_iter: Maximum iterations
    
    Returns:
        Dictionary with coefficients, residuals, loss values
    """
    logger.info("Fitting Huber robust regression model")
    
    # Fit model
    model = HuberRegressor(epsilon=epsilon, max_iter=max_iter)
    model.fit(X, y)
    
    # Predictions and residuals
    y_pred = model.predict(X)
    residuals = y.values - y_pred
    
    # Coefficients
    coef_names = ['intercept'] + list(X.columns)
    coefficients = [model.intercept_] + model.coef_.tolist()
    
    # Calculate pseudo R²
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'model_type': 'huber',
        'coefficients': dict(zip(coef_names, coefficients)),
        'epsilon': epsilon,
        'max_iter': max_iter,
        'n_iter': int(model.n_iter_),
        'r_squared': r_squared,
        'residuals': residuals.tolist(),
        'fitted_values': y_pred.tolist(),
        'outlier_mask': model.outliers_.tolist() if hasattr(model, 'outliers_') else None,
    }


def fit_ridge_regression(
    X: pd.DataFrame,
    y: pd.Series,
    alpha: float = 1.0,
) -> Dict[str, Any]:
    """
    Fit Ridge Regression model.
    
    Args:
        X: Feature matrix
        y: Target vector
        alpha: Regularization strength
    
    Returns:
        Dictionary with coefficients, alpha used
    """
    logger.info(f"Fitting Ridge regression model (alpha={alpha})")
    
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    
    y_pred = model.predict(X)
    residuals = y.values - y_pred
    
    coef_names = ['intercept'] + list(X.columns)
    coefficients = [model.intercept_] + model.coef_.tolist()
    
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'model_type': 'ridge',
        'coefficients': dict(zip(coef_names, coefficients)),
        'alpha': alpha,
        'r_squared': r_squared,
        'residuals': residuals.tolist(),
        'fitted_values': y_pred.tolist(),
    }


def fit_lasso_regression(
    X: pd.DataFrame,
    y: pd.Series,
    alpha: float = 0.1,
) -> Dict[str, Any]:
    """
    Fit Lasso Regression model.
    
    Args:
        X: Feature matrix
        y: Target vector
        alpha: Regularization strength
    
    Returns:
        Dictionary with coefficients, alpha used, coefficient path info
    """
    logger.info(f"Fitting Lasso regression model (alpha={alpha})")
    
    model = Lasso(alpha=alpha, max_iter=10000)
    model.fit(X, y)
    
    y_pred = model.predict(X)
    residuals = y.values - y_pred
    
    coef_names = ['intercept'] + list(X.columns)
    coefficients = [model.intercept_] + model.coef_.tolist()
    
    # Count non-zero coefficients (feature selection)
    n_nonzero = sum(1 for c in model.coef_ if abs(c) > 1e-6)
    
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'model_type': 'lasso',
        'coefficients': dict(zip(coef_names, coefficients)),
        'alpha': alpha,
        'n_nonzero_coefs': n_nonzero,
        'r_squared': r_squared,
        'residuals': residuals.tolist(),
        'fitted_values': y_pred.tolist(),
    }


def fit_quantile_regression(
    X: pd.DataFrame,
    y: pd.Series,
    quantiles: List[float] = [0.25, 0.5, 0.75],
) -> Dict[str, Any]:
    """
    Fit Quantile Regression models for multiple quantiles.
    
    Args:
        X: Feature matrix
        y: Target vector
        quantiles: List of quantiles to estimate
    
    Returns:
        Dictionary with quantile estimates and interval widths
    """
    logger.info(f"Fitting quantile regression for quantiles: {quantiles}")
    
    X_const = sm.add_constant(X)
    
    results_dict = {}
    for q in quantiles:
        model = sm.QuantReg(y, X_const)
        result = model.fit(q=q)
        
        coef_names = ['intercept'] + list(X.columns)
        results_dict[f'q{q}'] = {
            'coefficients': dict(zip(coef_names, result.params.tolist())),
            'std_errors': dict(zip(coef_names, result.bse.tolist())),
        }
    
    # Calculate interval widths between quantiles
    if len(quantiles) >= 2:
        q_lower = f'q{quantiles[0]}'
        q_upper = f'q{quantiles[-1]}'
        
        interval_widths = {}
        for col in X.columns:
            width = results_dict[q_upper]['coefficients'].get(col, 0) - \
                    results_dict[q_lower]['coefficients'].get(col, 0)
            interval_widths[col] = abs(width)
        
        results_dict['interval_widths'] = interval_widths
    
    results_dict['model_type'] = 'quantile'
    results_dict['quantiles'] = quantiles
    
    return results_dict
