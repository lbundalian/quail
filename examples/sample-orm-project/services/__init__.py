"""
Sample services package for QuailTrail example project

This demonstrates how to structure services following the dynamic-pricing-strategy pattern
when using QuailTrail for data quality pipelines.
"""

from .featurestore_service import FeatureStoreService
from .pricing_report_service import PricingReportService
from .property_service import PropertyService
from .user_service import UserService
from .quality_service import QualityService

__all__ = [
    'FeatureStoreService',
    'PricingReportService', 
    'PropertyService',
    'UserService',
    'QualityService'
]