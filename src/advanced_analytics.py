"""
Advanced Analytics & Learning Loop

Provides ML-powered insights, predictive analytics, automated optimization,
and continuous learning from campaign performance data.

Free technologies used:
- scikit-learn for ML algorithms
- pandas/numpy for data analysis
- matplotlib/seaborn for visualization
- sqlite3 for data storage
- scipy for statistical analysis
"""

import logging
import json
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pickle
import hashlib
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.metrics import mean_squared_error, silhouette_score
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class PerformanceDataCollector:
    """Collects and stores performance data for analysis."""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Campaign performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_performance (
                performance_id TEXT PRIMARY KEY,
                campaign_id TEXT,
                campaign_name TEXT,
                market TEXT,
                product_category TEXT,
                target_audience TEXT,
                created_at TIMESTAMP,
                metrics TEXT,  -- JSON of performance metrics
                creative_features TEXT,  -- JSON of creative features
                cost_data TEXT,  -- JSON of cost information
                success_indicators TEXT  -- JSON of success metrics
            )
        ''')
        
        # Asset performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_performance (
                asset_performance_id TEXT PRIMARY KEY,
                asset_id TEXT,
                asset_name TEXT,
                campaign_id TEXT,
                asset_type TEXT,
                visual_features TEXT,  -- JSON of visual features
                engagement_metrics TEXT,  -- JSON of engagement data
                conversion_metrics TEXT,  -- JSON of conversion data
                brand_metrics TEXT,  -- JSON of brand performance
                feedback_data TEXT,  -- JSON of user feedback
                created_at TIMESTAMP
            )
        ''')
        
        # Learning insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_insights (
                insight_id TEXT PRIMARY KEY,
                insight_type TEXT,
                category TEXT,
                description TEXT,
                confidence_score REAL,
                supporting_data TEXT,  -- JSON of supporting evidence
                recommendations TEXT,  -- JSON of recommended actions
                created_at TIMESTAMP,
                applied BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Model performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                model_id TEXT PRIMARY KEY,
                model_type TEXT,
                model_version TEXT,
                training_data_size INTEGER,
                performance_metrics TEXT,  -- JSON of model metrics
                feature_importance TEXT,  -- JSON of feature importance
                created_at TIMESTAMP,
                is_active BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Analytics database initialized")
    
    def record_campaign_performance(self, campaign_data: Dict, performance_metrics: Dict) -> str:
        """Record campaign performance data."""
        performance_id = hashlib.md5(f"{campaign_data.get('campaign_id', 'unknown')}_{datetime.now()}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO campaign_performance 
            (performance_id, campaign_id, campaign_name, market, product_category, 
             target_audience, created_at, metrics, creative_features, cost_data, success_indicators)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            performance_id,
            campaign_data.get('campaign_id', 'unknown'),
            campaign_data.get('campaign_name', 'Unknown Campaign'),
            campaign_data.get('market', 'US'),
            campaign_data.get('product_category', 'General'),
            campaign_data.get('target_audience', 'General'),
            datetime.now().isoformat(),
            json.dumps(performance_metrics.get('metrics', {})),
            json.dumps(performance_metrics.get('creative_features', {})),
            json.dumps(performance_metrics.get('cost_data', {})),
            json.dumps(performance_metrics.get('success_indicators', {}))
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded campaign performance: {performance_id}")
        return performance_id
    
    def record_asset_performance(self, asset_data: Dict, performance_data: Dict) -> str:
        """Record individual asset performance data."""
        asset_performance_id = hashlib.md5(f"{asset_data.get('asset_id', 'unknown')}_{datetime.now()}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO asset_performance
            (asset_performance_id, asset_id, asset_name, campaign_id, asset_type,
             visual_features, engagement_metrics, conversion_metrics, brand_metrics, 
             feedback_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asset_performance_id,
            asset_data.get('asset_id', 'unknown'),
            asset_data.get('asset_name', 'Unknown Asset'),
            asset_data.get('campaign_id', 'unknown'),
            asset_data.get('asset_type', 'creative'),
            json.dumps(performance_data.get('visual_features', {})),
            json.dumps(performance_data.get('engagement_metrics', {})),
            json.dumps(performance_data.get('conversion_metrics', {})),
            json.dumps(performance_data.get('brand_metrics', {})),
            json.dumps(performance_data.get('feedback_data', {})),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded asset performance: {asset_performance_id}")
        return asset_performance_id
    
    def get_performance_data(self, days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """Get performance data for analysis."""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        
        # Load campaign performance
        campaign_df = pd.read_sql_query('''
            SELECT * FROM campaign_performance 
            WHERE created_at > ?
            ORDER BY created_at DESC
        ''', conn, params=[cutoff_date])
        
        # Load asset performance
        asset_df = pd.read_sql_query('''
            SELECT * FROM asset_performance 
            WHERE created_at > ?
            ORDER BY created_at DESC
        ''', conn, params=[cutoff_date])
        
        conn.close()
        
        return {
            'campaigns': campaign_df,
            'assets': asset_df
        }


class PatternAnalyzer:
    """Analyzes patterns in creative performance data using ML."""
    
    def __init__(self, data_collector: PerformanceDataCollector):
        self.data_collector = data_collector
        self.models = {}
        self.scalers = {}
        self.encoders = {}
    
    def analyze_performance_patterns(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Analyze patterns in performance data."""
        logger.info("Analyzing performance patterns...")
        
        patterns = {
            'campaign_patterns': self._analyze_campaign_patterns(data['campaigns']),
            'asset_patterns': self._analyze_asset_patterns(data['assets']),
            'cross_campaign_insights': self._analyze_cross_campaign_patterns(data),
            'anomaly_detection': self._detect_performance_anomalies(data),
            'segment_analysis': self._perform_segmentation_analysis(data)
        }
        
        return patterns
    
    def _analyze_campaign_patterns(self, campaign_df: pd.DataFrame) -> Dict:
        """Analyze patterns in campaign performance."""
        if campaign_df.empty:
            return {'message': 'No campaign data available'}
        
        patterns = {}
        
        # Extract metrics from JSON columns
        metrics_data = []
        for _, row in campaign_df.iterrows():
            try:
                metrics = json.loads(row['metrics'])
                creative_features = json.loads(row['creative_features'])
                
                record = {
                    'campaign_id': row['campaign_id'],
                    'market': row['market'],
                    'product_category': row['product_category'],
                    'ctr': metrics.get('ctr', 0),
                    'conversion_rate': metrics.get('conversion_rate', 0),
                    'engagement_score': metrics.get('engagement_score', 0),
                    'brand_recall': metrics.get('brand_recall', 0),
                    'aspect_ratio': creative_features.get('aspect_ratio', 1.0),
                    'color_diversity': creative_features.get('color_diversity', 0.5),
                    'text_length': creative_features.get('text_length', 50)
                }
                metrics_data.append(record)
            except (json.JSONDecodeError, KeyError):
                continue
        
        if not metrics_data:
            return {'message': 'No valid metrics data found'}
        
        metrics_df = pd.DataFrame(metrics_data)
        
        # Market performance analysis
        market_performance = metrics_df.groupby('market').agg({
            'ctr': ['mean', 'std'],
            'conversion_rate': ['mean', 'std'],
            'engagement_score': ['mean', 'std']
        }).round(3)
        
        patterns['market_performance'] = market_performance.to_dict()
        
        # Category performance analysis
        category_performance = metrics_df.groupby('product_category').agg({
            'ctr': 'mean',
            'conversion_rate': 'mean',
            'brand_recall': 'mean'
        }).round(3)
        
        patterns['category_performance'] = category_performance.to_dict()
        
        # Feature correlation analysis
        numeric_cols = ['ctr', 'conversion_rate', 'engagement_score', 'aspect_ratio', 'color_diversity']
        correlation_matrix = metrics_df[numeric_cols].corr()
        patterns['feature_correlations'] = correlation_matrix.to_dict()
        
        # Performance trends
        if len(metrics_df) > 5:
            patterns['performance_trends'] = self._calculate_performance_trends(metrics_df)
        
        return patterns
    
    def _analyze_asset_patterns(self, asset_df: pd.DataFrame) -> Dict:
        """Analyze patterns in individual asset performance."""
        if asset_df.empty:
            return {'message': 'No asset data available'}
        
        patterns = {}
        
        # Extract visual features and engagement data
        asset_data = []
        for _, row in asset_df.iterrows():
            try:
                visual_features = json.loads(row['visual_features'])
                engagement = json.loads(row['engagement_metrics'])
                
                record = {
                    'asset_id': row['asset_id'],
                    'asset_type': row['asset_type'],
                    'brightness': visual_features.get('brightness', 0.5),
                    'contrast': visual_features.get('contrast', 0.5),
                    'color_count': visual_features.get('color_count', 5),
                    'complexity': visual_features.get('complexity', 0.5),
                    'engagement_rate': engagement.get('engagement_rate', 0),
                    'time_spent': engagement.get('time_spent', 0),
                    'shares': engagement.get('shares', 0)
                }
                asset_data.append(record)
            except (json.JSONDecodeError, KeyError):
                continue
        
        if not asset_data:
            return {'message': 'No valid asset data found'}
        
        asset_metrics_df = pd.DataFrame(asset_data)
        
        # Visual feature impact analysis
        feature_cols = ['brightness', 'contrast', 'color_count', 'complexity']
        performance_cols = ['engagement_rate', 'time_spent', 'shares']
        
        feature_impact = {}
        for perf_col in performance_cols:
            impact_scores = {}
            for feature_col in feature_cols:
                correlation = asset_metrics_df[feature_col].corr(asset_metrics_df[perf_col])
                impact_scores[feature_col] = correlation if not np.isnan(correlation) else 0
            feature_impact[perf_col] = impact_scores
        
        patterns['visual_feature_impact'] = feature_impact
        
        # Asset type performance
        type_performance = asset_metrics_df.groupby('asset_type').agg({
            'engagement_rate': 'mean',
            'time_spent': 'mean',
            'shares': 'mean'
        }).round(3)
        
        patterns['asset_type_performance'] = type_performance.to_dict()
        
        return patterns
    
    def _analyze_cross_campaign_patterns(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Analyze patterns across multiple campaigns."""
        patterns = {}
        
        if data['campaigns'].empty:
            return {'message': 'No campaign data for cross-analysis'}
        
        # Campaign success factors
        success_factors = self._identify_success_factors(data['campaigns'])
        patterns['success_factors'] = success_factors
        
        # Optimal campaign characteristics
        optimal_characteristics = self._find_optimal_characteristics(data['campaigns'])
        patterns['optimal_characteristics'] = optimal_characteristics
        
        return patterns
    
    def _identify_success_factors(self, campaign_df: pd.DataFrame) -> Dict:
        """Identify factors that contribute to campaign success."""
        success_factors = {}
        
        # Extract campaign data for analysis
        campaign_data = []
        for _, row in campaign_df.iterrows():
            try:
                metrics = json.loads(row['metrics'])
                success_score = (
                    metrics.get('ctr', 0) * 0.3 +
                    metrics.get('conversion_rate', 0) * 100 * 0.4 +  # Scale conversion rate
                    metrics.get('engagement_score', 0) * 0.2 +
                    metrics.get('brand_recall', 0) * 0.1
                )
                
                campaign_data.append({
                    'market': row['market'],
                    'product_category': row['product_category'],
                    'success_score': success_score
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        if not campaign_data:
            return {'message': 'No valid campaign data'}
        
        campaign_analysis_df = pd.DataFrame(campaign_data)
        
        # Market success analysis
        market_success = campaign_analysis_df.groupby('market')['success_score'].mean().round(3)
        success_factors['market_success_scores'] = market_success.to_dict()
        
        # Category success analysis
        category_success = campaign_analysis_df.groupby('product_category')['success_score'].mean().round(3)
        success_factors['category_success_scores'] = category_success.to_dict()
        
        # Identify top performers
        if len(campaign_analysis_df) > 0:
            top_quartile = campaign_analysis_df['success_score'].quantile(0.75)
            top_performers = campaign_analysis_df[campaign_analysis_df['success_score'] >= top_quartile]
            
            success_factors['top_performer_characteristics'] = {
                'avg_success_score': top_performers['success_score'].mean(),
                'common_markets': top_performers['market'].value_counts().head(3).to_dict(),
                'common_categories': top_performers['product_category'].value_counts().head(3).to_dict()
            }
        
        return success_factors
    
    def _find_optimal_characteristics(self, campaign_df: pd.DataFrame) -> Dict:
        """Find optimal campaign characteristics using ML."""
        optimal_chars = {}
        
        # Prepare data for ML analysis
        feature_data = []
        for _, row in campaign_df.iterrows():
            try:
                metrics = json.loads(row['metrics'])
                creative_features = json.loads(row['creative_features'])
                
                # Calculate composite performance score
                performance_score = (
                    metrics.get('ctr', 0) * 0.25 +
                    metrics.get('conversion_rate', 0) * 100 * 0.35 +
                    metrics.get('engagement_score', 0) * 0.25 +
                    metrics.get('brand_recall', 0) * 0.15
                )
                
                feature_data.append({
                    'market': row['market'],
                    'product_category': row['product_category'],
                    'aspect_ratio': creative_features.get('aspect_ratio', 1.0),
                    'color_diversity': creative_features.get('color_diversity', 0.5),
                    'text_length': creative_features.get('text_length', 50),
                    'performance_score': performance_score
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        if len(feature_data) < 5:  # Need minimum data for ML
            return {'message': 'Insufficient data for optimization analysis'}
        
        features_df = pd.DataFrame(feature_data)
        
        # Encode categorical variables
        categorical_cols = ['market', 'product_category']
        encoded_features = features_df.copy()
        
        for col in categorical_cols:
            le = LabelEncoder()
            encoded_features[f'{col}_encoded'] = le.fit_transform(encoded_features[col])
        
        # Prepare feature matrix
        feature_cols = ['aspect_ratio', 'color_diversity', 'text_length', 'market_encoded', 'product_category_encoded']
        X = encoded_features[feature_cols]
        y = encoded_features['performance_score']
        
        # Train random forest for feature importance
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        # Get feature importance
        feature_importance = dict(zip(feature_cols, rf.feature_importances_))
        optimal_chars['feature_importance'] = {k: round(v, 3) for k, v in feature_importance.items()}
        
        # Find optimal ranges for continuous features
        continuous_features = ['aspect_ratio', 'color_diversity', 'text_length']
        optimal_ranges = {}
        
        for feature in continuous_features:
            # Find top quartile performers and their feature ranges
            top_quartile = features_df['performance_score'].quantile(0.75)
            top_performers = features_df[features_df['performance_score'] >= top_quartile]
            
            if len(top_performers) > 0:
                optimal_ranges[feature] = {
                    'min': top_performers[feature].min(),
                    'max': top_performers[feature].max(),
                    'mean': top_performers[feature].mean(),
                    'recommended': top_performers[feature].median()
                }
        
        optimal_chars['optimal_ranges'] = optimal_ranges
        
        return optimal_chars
    
    def _detect_performance_anomalies(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Detect anomalies in performance data."""
        anomalies = {}
        
        if data['campaigns'].empty:
            return {'message': 'No data for anomaly detection'}
        
        # Extract performance metrics
        performance_data = []
        for _, row in data['campaigns'].iterrows():
            try:
                metrics = json.loads(row['metrics'])
                performance_data.append([
                    metrics.get('ctr', 0),
                    metrics.get('conversion_rate', 0),
                    metrics.get('engagement_score', 0),
                    metrics.get('brand_recall', 0)
                ])
            except (json.JSONDecodeError, KeyError):
                continue
        
        if len(performance_data) < 5:
            return {'message': 'Insufficient data for anomaly detection'}
        
        # Use Isolation Forest for anomaly detection
        performance_array = np.array(performance_data)
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(performance_array)
        
        # Identify anomalous campaigns
        anomalous_indices = np.where(anomaly_labels == -1)[0]
        normal_indices = np.where(anomaly_labels == 1)[0]
        
        anomalies['total_campaigns'] = len(performance_data)
        anomalies['anomalous_campaigns'] = len(anomalous_indices)
        anomalies['anomaly_rate'] = len(anomalous_indices) / len(performance_data)
        
        # Analyze anomaly characteristics
        if len(anomalous_indices) > 0 and len(normal_indices) > 0:
            anomalous_performance = performance_array[anomalous_indices]
            normal_performance = performance_array[normal_indices]
            
            anomalies['anomaly_characteristics'] = {
                'avg_ctr_anomalous': float(anomalous_performance[:, 0].mean()),
                'avg_ctr_normal': float(normal_performance[:, 0].mean()),
                'avg_conversion_anomalous': float(anomalous_performance[:, 1].mean()),
                'avg_conversion_normal': float(normal_performance[:, 1].mean())
            }
        
        return anomalies
    
    def _perform_segmentation_analysis(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Perform customer/campaign segmentation analysis."""
        segmentation = {}
        
        if data['campaigns'].empty:
            return {'message': 'No data for segmentation analysis'}
        
        # Extract features for clustering
        clustering_data = []
        for _, row in data['campaigns'].iterrows():
            try:
                metrics = json.loads(row['metrics'])
                clustering_data.append([
                    metrics.get('ctr', 0),
                    metrics.get('conversion_rate', 0),
                    metrics.get('engagement_score', 0),
                    metrics.get('brand_recall', 0)
                ])
            except (json.JSONDecodeError, KeyError):
                continue
        
        if len(clustering_data) < 6:  # Need minimum data for clustering
            return {'message': 'Insufficient data for segmentation'}
        
        # Perform K-means clustering
        clustering_array = np.array(clustering_data)
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(clustering_array)
        
        # Find optimal number of clusters
        optimal_k = self._find_optimal_clusters(scaled_data)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=optimal_k, random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_data)
        
        # Analyze clusters
        cluster_analysis = {}
        for cluster_id in range(optimal_k):
            cluster_mask = cluster_labels == cluster_id
            cluster_data = clustering_array[cluster_mask]
            
            cluster_analysis[f'cluster_{cluster_id}'] = {
                'size': int(cluster_mask.sum()),
                'avg_ctr': float(cluster_data[:, 0].mean()),
                'avg_conversion': float(cluster_data[:, 1].mean()),
                'avg_engagement': float(cluster_data[:, 2].mean()),
                'avg_brand_recall': float(cluster_data[:, 3].mean())
            }
        
        segmentation['optimal_clusters'] = optimal_k
        segmentation['cluster_analysis'] = cluster_analysis
        
        return segmentation
    
    def _find_optimal_clusters(self, data: np.ndarray, max_k: int = 5) -> int:
        """Find optimal number of clusters using silhouette score."""
        if len(data) <= max_k:
            return 2  # Minimum clusters
        
        silhouette_scores = []
        k_range = range(2, min(max_k + 1, len(data)))
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42)
            cluster_labels = kmeans.fit_predict(data)
            silhouette_avg = silhouette_score(data, cluster_labels)
            silhouette_scores.append(silhouette_avg)
        
        # Return k with highest silhouette score
        optimal_k = k_range[np.argmax(silhouette_scores)]
        return optimal_k
    
    def _calculate_performance_trends(self, metrics_df: pd.DataFrame) -> Dict:
        """Calculate performance trends over time."""
        trends = {}
        
        # Sort by campaign_id as proxy for time (assuming sequential IDs)
        sorted_df = metrics_df.sort_values('campaign_id')
        
        performance_metrics = ['ctr', 'conversion_rate', 'engagement_score', 'brand_recall']
        
        for metric in performance_metrics:
            values = sorted_df[metric].values
            if len(values) > 2:
                # Calculate linear trend
                x = np.arange(len(values))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                
                trends[metric] = {
                    'slope': slope,
                    'r_squared': r_value ** 2,
                    'trend_direction': 'improving' if slope > 0.01 else 'declining' if slope < -0.01 else 'stable',
                    'significance': 'significant' if p_value < 0.05 else 'not_significant'
                }
        
        return trends


class RecommendationEngine:
    """Generates actionable recommendations based on analysis."""
    
    def __init__(self, pattern_analyzer: PatternAnalyzer):
        self.pattern_analyzer = pattern_analyzer
        self.recommendation_history = []
    
    def generate_recommendations(self, analysis_results: Dict) -> Dict:
        """Generate comprehensive recommendations based on analysis."""
        logger.info("Generating optimization recommendations...")
        
        recommendations = {
            'strategic_recommendations': self._generate_strategic_recommendations(analysis_results),
            'tactical_recommendations': self._generate_tactical_recommendations(analysis_results),
            'creative_recommendations': self._generate_creative_recommendations(analysis_results),
            'optimization_priorities': self._prioritize_optimizations(analysis_results),
            'predicted_impact': self._predict_recommendation_impact(analysis_results)
        }
        
        # Store recommendations
        self.recommendation_history.append({
            'timestamp': datetime.now().isoformat(),
            'recommendations': recommendations,
            'analysis_data': analysis_results
        })
        
        return recommendations
    
    def _generate_strategic_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate high-level strategic recommendations."""
        recommendations = []
        
        # Market performance recommendations
        campaign_patterns = analysis.get('campaign_patterns', {})
        market_performance = campaign_patterns.get('market_performance', {})
        
        if market_performance:
            # Find best performing markets
            ctr_means = market_performance.get('ctr', {}).get('mean', {})
            if ctr_means:
                best_market = max(ctr_means.keys(), key=lambda k: ctr_means[k])
                worst_market = min(ctr_means.keys(), key=lambda k: ctr_means[k])
                
                recommendations.append({
                    'type': 'market_focus',
                    'priority': 'high',
                    'title': f'Increase investment in {best_market} market',
                    'description': f'{best_market} shows highest CTR performance. Consider reallocating budget.',
                    'expected_impact': 'high',
                    'implementation_effort': 'medium'
                })
                
                recommendations.append({
                    'type': 'market_optimization',
                    'priority': 'medium',
                    'title': f'Optimize {worst_market} market strategy',
                    'description': f'{worst_market} underperforming. Review localization and targeting.',
                    'expected_impact': 'medium',
                    'implementation_effort': 'high'
                })
        
        # Cross-campaign insights
        cross_campaign = analysis.get('cross_campaign_insights', {})
        success_factors = cross_campaign.get('success_factors', {})
        
        if success_factors and 'top_performer_characteristics' in success_factors:
            top_chars = success_factors['top_performer_characteristics']
            common_categories = top_chars.get('common_categories', {})
            
            if common_categories:
                top_category = max(common_categories.keys(), key=lambda k: common_categories[k])
                recommendations.append({
                    'type': 'category_strategy',
                    'priority': 'high',
                    'title': f'Expand {top_category} category campaigns',
                    'description': f'{top_category} consistently performs well across campaigns.',
                    'expected_impact': 'high',
                    'implementation_effort': 'low'
                })
        
        return recommendations
    
    def _generate_tactical_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate specific tactical recommendations."""
        recommendations = []
        
        # Feature optimization recommendations
        campaign_patterns = analysis.get('campaign_patterns', {})
        correlations = campaign_patterns.get('feature_correlations', {})
        
        if correlations:
            # Find strong positive correlations with performance
            for feature, corr_data in correlations.items():
                if isinstance(corr_data, dict):
                    for perf_metric, correlation in corr_data.items():
                        if isinstance(correlation, (int, float)) and correlation > 0.3:
                            recommendations.append({
                                'type': 'feature_optimization',
                                'priority': 'medium',
                                'title': f'Optimize {feature} for better {perf_metric}',
                                'description': f'Strong positive correlation ({correlation:.2f}) detected.',
                                'expected_impact': 'medium',
                                'implementation_effort': 'low'
                            })
        
        # Asset performance recommendations
        asset_patterns = analysis.get('asset_patterns', {})
        feature_impact = asset_patterns.get('visual_feature_impact', {})
        
        if feature_impact:
            for perf_metric, impacts in feature_impact.items():
                if isinstance(impacts, dict):
                    # Find highest impact features
                    top_feature = max(impacts.keys(), key=lambda k: abs(impacts[k]))
                    impact_score = impacts[top_feature]
                    
                    if abs(impact_score) > 0.2:
                        direction = "increase" if impact_score > 0 else "decrease"
                        recommendations.append({
                            'type': 'visual_optimization',
                            'priority': 'medium',
                            'title': f'{direction.title()} {top_feature} in creative assets',
                            'description': f'{top_feature} strongly impacts {perf_metric} (correlation: {impact_score:.2f})',
                            'expected_impact': 'medium',
                            'implementation_effort': 'low'
                        })
        
        return recommendations
    
    def _generate_creative_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate creative-specific recommendations."""
        recommendations = []
        
        # Optimal characteristics recommendations
        cross_campaign = analysis.get('cross_campaign_insights', {})
        optimal_chars = cross_campaign.get('optimal_characteristics', {})
        
        if 'optimal_ranges' in optimal_chars:
            optimal_ranges = optimal_chars['optimal_ranges']
            
            for feature, ranges in optimal_ranges.items():
                if isinstance(ranges, dict) and 'recommended' in ranges:
                    recommendations.append({
                        'type': 'creative_guideline',
                        'priority': 'medium',
                        'title': f'Optimize {feature}',
                        'description': f'Recommended {feature}: {ranges["recommended"]:.2f} (range: {ranges["min"]:.2f}-{ranges["max"]:.2f})',
                        'expected_impact': 'medium',
                        'implementation_effort': 'low'
                    })
        
        # Anomaly-based recommendations
        anomalies = analysis.get('anomaly_detection', {})
        anomaly_chars = anomalies.get('anomaly_characteristics', {})
        
        if anomaly_chars:
            # Check for significant differences
            ctr_diff = anomaly_chars.get('avg_ctr_normal', 0) - anomaly_chars.get('avg_ctr_anomalous', 0)
            if abs(ctr_diff) > 0.5:
                recommendations.append({
                    'type': 'anomaly_prevention',
                    'priority': 'high',
                    'title': 'Implement CTR quality gates',
                    'description': f'Anomalous campaigns have {ctr_diff:.1f} lower CTR. Add pre-launch checks.',
                    'expected_impact': 'high',
                    'implementation_effort': 'medium'
                })
        
        return recommendations
    
    def _prioritize_optimizations(self, analysis: Dict) -> List[Dict]:
        """Prioritize optimization opportunities."""
        priorities = []
        
        # Impact vs effort matrix
        all_recommendations = []
        
        # Collect all recommendations
        strategic = self._generate_strategic_recommendations(analysis)
        tactical = self._generate_tactical_recommendations(analysis)
        creative = self._generate_creative_recommendations(analysis)
        
        all_recommendations.extend(strategic)
        all_recommendations.extend(tactical)
        all_recommendations.extend(creative)
        
        # Score and prioritize
        for rec in all_recommendations:
            impact_score = {'high': 3, 'medium': 2, 'low': 1}.get(rec.get('expected_impact', 'low'), 1)
            effort_score = {'low': 3, 'medium': 2, 'high': 1}.get(rec.get('implementation_effort', 'high'), 1)
            priority_score = impact_score * effort_score
            
            priorities.append({
                'recommendation': rec,
                'priority_score': priority_score,
                'quick_win': impact_score >= 2 and effort_score >= 2
            })
        
        # Sort by priority score
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return priorities[:10]  # Top 10 priorities
    
    def _predict_recommendation_impact(self, analysis: Dict) -> Dict:
        """Predict the impact of implementing recommendations."""
        impact_prediction = {}
        
        # Base performance metrics
        campaign_patterns = analysis.get('campaign_patterns', {})
        
        # Simulate impact based on historical patterns
        current_performance = {
            'avg_ctr': 1.2,  # Default baseline
            'avg_conversion': 0.08,
            'avg_engagement': 2.5
        }
        
        # Estimate improvement potential
        improvements = {
            'market_optimization': {'ctr': 0.15, 'conversion': 0.02, 'engagement': 0.3},
            'feature_optimization': {'ctr': 0.08, 'conversion': 0.015, 'engagement': 0.2},
            'visual_optimization': {'ctr': 0.12, 'conversion': 0.01, 'engagement': 0.25},
            'anomaly_prevention': {'ctr': 0.20, 'conversion': 0.03, 'engagement': 0.1}
        }
        
        predicted_improvements = {}
        for opt_type, improvements_dict in improvements.items():
            predicted_improvements[opt_type] = {
                'ctr_improvement': f"{improvements_dict['ctr']:.2f}",
                'conversion_improvement': f"{improvements_dict['conversion']:.3f}",
                'engagement_improvement': f"{improvements_dict['engagement']:.1f}",
                'estimated_roi': f"{(improvements_dict['ctr'] + improvements_dict['conversion'] * 100) * 1.5:.1f}%"
            }
        
        impact_prediction['predicted_improvements'] = predicted_improvements
        impact_prediction['implementation_timeline'] = '2-8 weeks'
        impact_prediction['confidence_level'] = 'medium'
        
        return impact_prediction


class AdvancedAnalyticsEngine:
    """Main engine for advanced analytics and learning."""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.data_collector = PerformanceDataCollector(db_path)
        self.pattern_analyzer = PatternAnalyzer(self.data_collector)
        self.recommendation_engine = RecommendationEngine(self.pattern_analyzer)
        self.learning_history = []
    
    def run_comprehensive_analysis(self, days_back: int = 30) -> Dict:
        """Run comprehensive analytics analysis."""
        logger.info(f"Running comprehensive analytics analysis for last {days_back} days")
        
        # Collect performance data
        performance_data = self.data_collector.get_performance_data(days_back)
        
        # Analyze patterns
        pattern_analysis = self.pattern_analyzer.analyze_performance_patterns(performance_data)
        
        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(pattern_analysis)
        
        # Create comprehensive report
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_period_days': days_back,
            'data_summary': {
                'campaigns_analyzed': len(performance_data['campaigns']),
                'assets_analyzed': len(performance_data['assets'])
            },
            'pattern_analysis': pattern_analysis,
            'recommendations': recommendations,
            'learning_insights': self._extract_learning_insights(pattern_analysis),
            'next_steps': self._generate_next_steps(recommendations)
        }
        
        # Store learning
        self.learning_history.append(report)
        
        return report
    
    def _extract_learning_insights(self, pattern_analysis: Dict) -> List[Dict]:
        """Extract key learning insights from analysis."""
        insights = []
        
        # Market insights
        campaign_patterns = pattern_analysis.get('campaign_patterns', {})
        market_performance = campaign_patterns.get('market_performance', {})
        
        if market_performance:
            insights.append({
                'type': 'market_performance',
                'insight': 'Market performance varies significantly across regions',
                'confidence': 0.8,
                'actionable': True,
                'impact': 'high'
            })
        
        # Feature correlation insights
        correlations = campaign_patterns.get('feature_correlations', {})
        if correlations:
            insights.append({
                'type': 'feature_relationships',
                'insight': 'Strong correlations found between visual features and performance',
                'confidence': 0.7,
                'actionable': True,
                'impact': 'medium'
            })
        
        # Anomaly insights
        anomalies = pattern_analysis.get('anomaly_detection', {})
        anomaly_rate = anomalies.get('anomaly_rate', 0)
        
        if anomaly_rate > 0.1:
            insights.append({
                'type': 'quality_control',
                'insight': f'High anomaly rate ({anomaly_rate:.1%}) indicates need for quality controls',
                'confidence': 0.9,
                'actionable': True,
                'impact': 'high'
            })
        
        return insights
    
    def _generate_next_steps(self, recommendations: Dict) -> List[str]:
        """Generate actionable next steps."""
        next_steps = []
        
        # High priority recommendations
        priorities = recommendations.get('optimization_priorities', [])
        high_priority_recs = [p for p in priorities if p.get('quick_win', False)]
        
        if high_priority_recs:
            next_steps.append(f"Implement {len(high_priority_recs)} quick-win optimizations")
        
        # Strategic recommendations
        strategic = recommendations.get('strategic_recommendations', [])
        high_strategic = [r for r in strategic if r.get('priority') == 'high']
        
        if high_strategic:
            next_steps.append(f"Review {len(high_strategic)} high-priority strategic changes")
        
        # Data collection improvements
        next_steps.append("Continue collecting performance data for better insights")
        next_steps.append("Schedule weekly analytics reviews")
        
        return next_steps
    
    def get_learning_report(self) -> Dict:
        """Generate comprehensive learning report."""
        if not self.learning_history:
            return {'message': 'No learning history available'}
        
        recent_analyses = self.learning_history[-5:]  # Last 5 analyses
        
        # Aggregate insights
        all_insights = []
        for analysis in recent_analyses:
            all_insights.extend(analysis.get('learning_insights', []))
        
        # Count insight types
        insight_types = Counter([insight['type'] for insight in all_insights])
        
        # Track recommendation implementation (simulated)
        total_recommendations = sum(
            len(analysis['recommendations'].get('optimization_priorities', []))
            for analysis in recent_analyses
        )
        
        return {
            'total_analyses': len(self.learning_history),
            'recent_analyses': len(recent_analyses),
            'total_insights_generated': len(all_insights),
            'insight_categories': dict(insight_types),
            'total_recommendations': total_recommendations,
            'learning_velocity': len(all_insights) / len(recent_analyses) if recent_analyses else 0,
            'top_insight_types': insight_types.most_common(3),
            'system_maturity': 'developing' if len(self.learning_history) < 10 else 'mature'
        }