"""
User Properties models for MongoDB collections
Following the pattern from dynamic-pricing-strategy/models/property.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from mongoengine import *
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class PropertyQualityConfig:
    """Configuration for property quality checks"""
    quality_checks_enabled: bool = True
    min_quality_score: float = 0.8
    max_validation_errors: int = 0
    notification_threshold: float = 0.5
    

class UserProperty(DynamicDocument):
    """
    User property data - equivalent to Property in dynamic-pricing-strategy
    Maps to MongoDB property collection
    """
    property_id = StringField(required=True, unique=True)
    user_id = StringField(required=True)
    listing_id = StringField()
    
    # Property details
    name = StringField()
    address = StringField()
    bedrooms = IntField()
    bathrooms = IntField()
    property_type = StringField()
    
    # Quality tracking
    quality_score = FloatField()
    quality_checks_enabled = BooleanField(default=True)
    last_quality_check = DateTimeField()
    validation_errors = ListField(StringField())
    
    # Metadata
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    status = StringField(choices=['active', 'inactive', 'pending'])
    
    meta = {
        'collection': 'user_properties',
        'strict': False
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)