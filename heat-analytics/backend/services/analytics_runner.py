"""
Analytics runner service that orchestrates the complete analysis pipeline.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.models.schemas import DailyReading, AnalysisResult, Building
from backend.analytics.features import create_features, prepare_regression_data
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
    consensus_anomaly_detection,
)
from backend.analytics.clustering import cluster_kmeans, cluster_dbscan, cluster_gmm
from backend.config.settings import settings


logger = logging.getLogger(__name__)


def calculate_efficiency_class(norm_deviation_pct: float) -> str:
    """
    Determine efficiency class based on deviation from norm.
    
    Args:
        norm_deviation_pct: Percentage deviation from normative consumption
    
    Returns:
        Efficiency class string
    """
    if norm_deviation_pct < -15:  # More than 15% below norm
        return "excellent"
    elif norm_deviation_pct < -5:  # 5-15% below norm
        return "good"
    elif norm_deviation_pct <= 5:  # Within ±5% of norm
        return "normal"
    elif norm_deviation_pct <= 20:  # 5-20% above norm
        return "poor"
    else:  # More than 20% above norm
        return "critical"


async def run_analysis_pipeline(
    building_id: int,
    run_id: str,
    model_types: List[str],
    db_session_maker: async_sessionmaker,
):
    """
    Run complete analysis pipeline for a building.
    
    This is the main orchestrator function that:
    1. Loads data from database
    2. Creates features
    3. Runs requested models (regression, anomaly detection, clustering)
    4. Saves results to database
    
    Args:
        building_id: ID of building to analyze
        run_id: Unique identifier for this analysis run
        model_types: List of model types to run
        db_session_maker: Database session factory
    """
    logger.info(f"Starting analysis pipeline for building {building_id}, run {run_id}")
    logger.info(f"Models to run: {model_types}")
    
    try:
        # Load data from database
        async with db_session_maker() as db:
            result = await db.execute(
                select(DailyReading)
                .where(DailyReading.building_id == building_id)
                .order_by(DailyReading.date)
            )
            readings = result.scalars().all()
            
            # Get building info
            building_result = await db.execute(
                select(Building).where(Building.id == building_id)
            )
            building = building_result.scalar_one_or_none()
        
        if not readings:
            logger.error(f"No readings found for building {building_id}")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': r.date,
            't1': r.t1,
            't2': r.t2,
            'p1': r.p1,
            'p2': r.p2,
            'v1': r.v1,
            'v2': r.v2,
            'm1': r.m1,
            'm2': r.m2,
            'q': r.q,
            'dt': r.dt,
            'dv': r.dv,
            'dm': r.dm,
            'imbalance': r.imbalance,
            'ns_codes': r.ns_codes,
            'status': r.status,
        } for r in readings])
        
        logger.info(f"Loaded {len(df)} readings")
        
        # Create features
        df_features = create_features(df)
        
        # Prepare regression data
        feature_cols = ['hdd', 'month_sin', 'month_cos', 'day_sin', 'day_cos',
                       'q_lag_1', 'q_lag_7', 'q_rolling_mean_7']
        available_cols = [c for c in feature_cols if c in df_features.columns]
        
        X, y = prepare_regression_data(df_features, target_col='q', feature_cols=available_cols)
        
        logger.info(f"Prepared {len(X)} samples for regression with {len(available_cols)} features")
        
        # Store results to save
        results_to_save = []
        
        # Run regression models
        if 'ols' in model_types:
            try:
                ols_results = fit_ols_regression(X, y)
                for i, (residual, fitted) in enumerate(zip(ols_results['residuals'], ols_results['fitted_values'])):
                    results_to_save.append({
                        'run_id': run_id,
                        'model_type': 'ols',
                        'predicted_q': fitted,
                        'residual': residual,
                        'params': {'coefficients': ols_results['coefficients'], 'r_squared': ols_results['r_squared']},
                        'metrics': {'aic': ols_results.get('aic'), 'bic': ols_results.get('bic')},
                    })
                logger.info("OLS regression completed")
            except Exception as e:
                logger.error(f"OLS regression failed: {e}")
        
        if 'huber' in model_types:
            try:
                huber_results = fit_huber_regression(X, y)
                for i, (residual, fitted) in enumerate(zip(huber_results['residuals'], huber_results['fitted_values'])):
                    results_to_save.append({
                        'run_id': run_id,
                        'model_type': 'huber',
                        'predicted_q': fitted,
                        'residual': residual,
                        'params': {'coefficients': huber_results['coefficients'], 'epsilon': huber_results['epsilon']},
                        'metrics': {'r_squared': huber_results['r_squared']},
                    })
                logger.info("Huber regression completed")
            except Exception as e:
                logger.error(f"Huber regression failed: {e}")
        
        if 'ridge' in model_types:
            try:
                ridge_results = fit_ridge_regression(X, y)
                for i, (residual, fitted) in enumerate(zip(ridge_results['residuals'], ridge_results['fitted_values'])):
                    results_to_save.append({
                        'run_id': run_id,
                        'model_type': 'ridge',
                        'predicted_q': fitted,
                        'residual': residual,
                        'params': {'coefficients': ridge_results['coefficients'], 'alpha': ridge_results['alpha']},
                        'metrics': {'r_squared': ridge_results['r_squared']},
                    })
                logger.info("Ridge regression completed")
            except Exception as e:
                logger.error(f"Ridge regression failed: {e}")
        
        if 'lasso' in model_types:
            try:
                lasso_results = fit_lasso_regression(X, y)
                for i, (residual, fitted) in enumerate(zip(lasso_results['residuals'], lasso_results['fitted_values'])):
                    results_to_save.append({
                        'run_id': run_id,
                        'model_type': 'lasso',
                        'predicted_q': fitted,
                        'residual': residual,
                        'params': {'coefficients': lasso_results['coefficients'], 'alpha': lasso_results['alpha']},
                        'metrics': {'r_squared': lasso_results['r_squared'], 'n_nonzero': lasso_results['n_nonzero_coefs']},
                    })
                logger.info("Lasso regression completed")
            except Exception as e:
                logger.error(f"Lasso regression failed: {e}")
        
        # Run anomaly detection
        anomaly_results_list = []
        
        if 'ewma' in model_types:
            try:
                ewma_results = detect_anomalies_ewma(df_features)
                anomaly_results_list.append(ewma_results)
                for i, (flag, score) in enumerate(zip(ewma_results['anomaly_flags'], ewma_results.get('residuals', [0]*len(df_features)))):
                    if i < len(results_to_save):
                        results_to_save[i]['anomaly_score'] = abs(score) if score else 0
                        results_to_save[i]['anomaly_flag'] = flag
                logger.info("EWMA anomaly detection completed")
            except Exception as e:
                logger.error(f"EWMA anomaly detection failed: {e}")
        
        if 'isolation_forest' in model_types:
            try:
                iforest_results = detect_anomalies_isolation_forest(X)
                anomaly_results_list.append(iforest_results)
                # Update results with isolation forest scores
                for i, (label, score) in enumerate(zip(iforest_results['labels'], iforest_results['anomaly_scores'])):
                    if i < len(results_to_save):
                        results_to_save[i]['anomaly_score'] = max(results_to_save[i].get('anomaly_score', 0), score)
                        # Consensus: flag if EWMA also flagged or IF flags it
                        if label == 1:
                            results_to_save[i]['anomaly_flag'] = 1
                logger.info("Isolation Forest anomaly detection completed")
            except Exception as e:
                logger.error(f"Isolation Forest anomaly detection failed: {e}")
        
        if 'lof' in model_types:
            try:
                lof_results = detect_anomalies_lof(X)
                anomaly_results_list.append(lof_results)
                logger.info("LOF anomaly detection completed")
            except Exception as e:
                logger.error(f"LOF anomaly detection failed: {e}")
        
        # Run consensus anomaly detection if multiple methods were used
        if len(anomaly_results_list) >= 2:
            try:
                consensus_results = consensus_anomaly_detection(anomaly_results_list, min_agreement=2)
                logger.info(f"Consensus anomaly detection: {consensus_results['n_anomalies']} anomalies found")
            except Exception as e:
                logger.error(f"Consensus anomaly detection failed: {e}")
        
        # Run clustering
        if 'kmeans' in model_types:
            try:
                k = settings.cluster_k
                kmeans_results = cluster_kmeans(X, n_clusters=k)
                
                # Assign cluster IDs to results
                if 'cluster_labels' in kmeans_results:
                    for i, cluster_id in enumerate(kmeans_results['cluster_labels']):
                        if i < len(results_to_save):
                            results_to_save[i]['cluster_id'] = cluster_id
                
                logger.info(f"K-Means clustering completed with {k} clusters")
            except Exception as e:
                logger.error(f"K-Means clustering failed: {e}")
        
        if 'dbscan' in model_types:
            try:
                dbscan_results = cluster_dbscan(X)
                logger.info(f"DBSCAN clustering completed: {dbscan_results.get('n_clusters', 0)} clusters found")
            except Exception as e:
                logger.error(f"DBSCAN clustering failed: {e}")
        
        if 'gmm' in model_types:
            try:
                gmm_results = cluster_gmm(X, n_components=settings.cluster_k)
                logger.info(f"GMM clustering completed")
            except Exception as e:
                logger.error(f"GMM clustering failed: {e}")
        
        # Calculate efficiency metrics and save results
        async with db_session_maker() as db:
            # Calculate norm deviation for each reading
            if building and building.norm_gcal_m2:
                norm_q = building.norm_gcal_m2 * building.area_m2 / 30  # Daily norm
            else:
                norm_q = df['q'].mean() if df['q'].notna().any() else 1.0
            
            for result_data in results_to_save:
                # Calculate norm deviation
                if result_data['predicted_q']:
                    norm_deviation_pct = ((result_data['predicted_q'] - norm_q) / norm_q) * 100
                else:
                    norm_deviation_pct = 0
                
                result_data['norm_deviation_pct'] = norm_deviation_pct
                result_data['efficiency_class'] = calculate_efficiency_class(norm_deviation_pct)
                result_data['building_id'] = building_id
                
                # Create AnalysisResult record
                analysis_record = AnalysisResult(**result_data)
                db.add(analysis_record)
            
            await db.commit()
            logger.info(f"Saved {len(results_to_save)} analysis results to database")
        
        logger.info(f"Analysis pipeline completed successfully for run {run_id}")
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise
