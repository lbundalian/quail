"""
Property Service for querying MongoDB collections  
Following the pattern from dynamic-pricing-strategy/services/property_service.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from models import UserProperty
from quail.context import MongoDbContext

class PropertyService:
    
    def __init__(self, database):
        """Initialize with database context - matches dynamic-pricing-strategy pattern"""
        self.database = database
        
    def get_properties_by_user(self, user_id: str):
        """
        Get all properties for a user
        Similar to get_properties_by_user in PropertyService
        """
        with MongoDbContext(self.database) as db:
            properties = UserProperty.objects(user_id=user_id)
            return list(properties)
    
    def get_properties_by_id(self, listing_ids: list):
        """
        Get properties by listing IDs
        Similar to get_properties_by_id in PropertyService
        """
        with MongoDbContext(self.database) as db:
            properties = UserProperty.objects(listing_id__in=listing_ids)
            return [prop.to_mongo().to_dict() for prop in properties]
    
    def update_quality_metrics(self, property_id: str, quality_score: float, validation_errors: list):
        """
        Update quality metrics for a property
        """
        with MongoDbContext(self.database) as db:
            from datetime import datetime
            UserProperty.objects(property_id=property_id).update_one(
                set__quality_score=quality_score,
                set__validation_errors=validation_errors,
                set__last_quality_check=datetime.utcnow()
            )
    
    def get_quality_summary(self, user_id: str = None):
        """
        Get quality summary for properties
        """
        with MongoDbContext(self.database) as db:
            query = {}
            if user_id:
                query['user_id'] = user_id
                
            properties = UserProperty.objects(**query)
            
            total_count = properties.count()
            quality_enabled = properties.filter(quality_checks_enabled=True).count()
            avg_quality_score = 0
            
            if total_count > 0:
                scores = [p.quality_score for p in properties if p.quality_score is not None]
                avg_quality_score = sum(scores) / len(scores) if scores else 0
            
            return {
                'total_properties': total_count,
                'quality_enabled': quality_enabled,
                'avg_quality_score': avg_quality_score,
                'enabled_percentage': quality_enabled / total_count if total_count > 0 else 0
            }