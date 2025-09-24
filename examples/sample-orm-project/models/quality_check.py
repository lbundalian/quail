"""
Quality Check models for MongoDB collections
Following the pattern from dynamic-pricing-strategy/models/pricing.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from mongoengine import *
from datetime import datetime

class QualityMetric(EmbeddedDocument):
    """
    Embedded document for individual quality metrics
    Similar to IntelCompOption in dynamic-pricing-strategy
    """
    metric_name = StringField(required=True)
    metric_value = FloatField()
    threshold = FloatField()
    status = StringField(choices=['pass', 'fail', 'warning', 'skip'])
    severity = StringField(choices=['error', 'warning', 'info'])
    description = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'strict': False
    }


class QualityCheckResult(DynamicDocument):
    """
    Individual quality check results
    Similar to Pricing in dynamic-pricing-strategy
    """
    check_id = StringField(required=True)
    run_id = StringField(required=True)
    table_name = StringField()
    listing_id = StringField()
    user_id = StringField()
    status = StringField(choices=['pass', 'fail', 'error', 'skip'])
    severity = StringField(choices=['error', 'warning', 'info'])
    
    # Metrics and details
    metrics = ListField(EmbeddedDocumentField(QualityMetric))
    error_message = StringField()
    description = StringField()
    
    # Timing and metadata
    execution_time_ms = IntField()
    timestamp = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'quality_check_results',
        'strict': False
    }


class QualityRun(DynamicDocument):
    """
    Quality check run metadata
    Similar to PricingRun/TrendRun in dynamic-pricing-strategy
    """
    run_id = StringField(required=True, unique=True)
    pipeline_name = StringField()
    target_name = StringField()
    
    # Status and timing
    status = StringField(choices=['running', 'completed', 'failed'])
    start_time = DateTimeField(default=datetime.utcnow)
    end_time = DateTimeField()
    total_checks = IntField()
    passed_checks = IntField()
    failed_checks = IntField()
    
    # Configuration
    environment = StringField()
    user = StringField()
    version = StringField()
    
    meta = {
        'collection': 'quality_runs',
        'strict': False
    }