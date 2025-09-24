"""
Sample models package for QuailTrail example project

This demonstrates how to structure models following the dynamic-pricing-strategy pattern
when using QuailTrail for data quality pipelines.
"""

from .featurestore import FeatureStore, FeatureStoreAlt
from .pricing_report import PricingReport  
from .quality_check import QualityCheckResult, QualityRun, QualityMetric
from .user_properties import UserProperty

__all__ = [
    'FeatureStore',
    'FeatureStoreAlt', 
    'PricingReport',
    'QualityCheckResult',
    'QualityRun',
    'QualityMetric',
    'UserProperty'
]