"""
FeatureStore Service for querying SQL/Redshift tables
Following the pattern from dynamic-pricing-strategy/services/market_feature_service.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from models import FeatureStore, FeatureStoreAlt
from quail.context import RedshiftDbContext

class FeatureStoreService:
    
    def __init__(self, database):
        """Initialize with database context - matches dynamic-pricing-strategy pattern"""
        self.database = database
       
    def get_feature_store(self, listing_ids: list):
        """
        Get featurestore data for given listing IDs
        Similar to get_feature_store in MarketFeatureService
        """
        with RedshiftDbContext(self.database) as session:
            results = session.query(FeatureStore).filter(
                FeatureStore.listing_id.in_(listing_ids)
            ).all()
            return results
    
    def get_feature_store_filtered(self, listing_ids: list, min_nights_filter: int = 10):
        """
        Get featurestore data with additional filters
        """
        with RedshiftDbContext(self.database) as session:
            results = session.query(FeatureStore).filter(
                FeatureStore.listing_id.in_(listing_ids),
                FeatureStore.min_nights <= min_nights_filter
            ).all()
            return results
    
    def get_processed_store(self, listing_ids: list):
        """
        Get processed featurestore data (model_data table)
        Similar to get_dummy_store in MarketFeatureService
        """
        with RedshiftDbContext(self.database) as session:
            results = session.query(FeatureStoreAlt).filter(
                FeatureStoreAlt.listing_id.in_(listing_ids)
            ).all()
            return results
    
    def check_data_completeness(self, listing_ids: list):
        """
        Check data completeness for given listings
        Returns a report with completeness scores
        """
        with RedshiftDbContext(self.database) as session:
            results = session.query(FeatureStore).filter(
                FeatureStore.listing_id.in_(listing_ids)
            ).all()
            
            completeness_report = []
            for result in results:
                # Calculate completeness score based on non-null fields
                total_fields = 12  # Total important fields
                null_count = sum([
                    1 if result.price is None else 0,
                    1 if result.review_count is None else 0,
                    1 if result.img_score is None else 0,
                    1 if result.bedrooms is None else 0,
                    1 if result.rating_value is None else 0,
                    1 if result.min_nights is None else 0,
                    # Add other important fields...
                ])
                
                completeness_score = (total_fields - null_count) / total_fields
                
                completeness_report.append({
                    'listing_id': result.listing_id,
                    'completeness_score': completeness_score,
                    'null_fields': null_count,
                    'calendar_date': result.calendar_date
                })
            
            return completeness_report
    
    def validate_data_ranges(self, listing_ids: list):
        """
        Validate data ranges and business rules
        """
        with RedshiftDbContext(self.database) as session:
            results = session.query(FeatureStore).filter(
                FeatureStore.listing_id.in_(listing_ids)
            ).all()
            
            validation_report = []
            for result in results:
                issues = []
                
                # Validate price ranges
                if result.price and (float(result.price) <= 0 or float(result.price) > 10000):
                    issues.append("Price out of valid range")
                
                # Validate bedrooms
                if result.bedrooms and (result.bedrooms < 0 or result.bedrooms > 20):
                    issues.append("Bedroom count invalid")
                
                # Validate rating
                if result.rating_value and (result.rating_value < 0 or result.rating_value > 5):
                    issues.append("Rating value out of range")
                
                validation_report.append({
                    'listing_id': result.listing_id,
                    'is_valid': len(issues) == 0,
                    'validation_issues': issues,
                    'calendar_date': result.calendar_date
                })
            
            return validation_report