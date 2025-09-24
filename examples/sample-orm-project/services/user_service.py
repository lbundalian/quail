"""
User Service for querying MongoDB collections
Following the pattern from dynamic-pricing-strategy/services/user_service.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from models import UserProperty
from quail.context import MongoDbContext

class UserService:
    
    def __init__(self, database):
        """Initialize with database context - matches dynamic-pricing-strategy pattern"""
        self.database = database

    def get_user_ids(self, limit: int = None):
        """
        Get list of user IDs
        Similar to get_user_ids in UserService
        """
        with MongoDbContext(self.database) as db:
            query = UserProperty.objects().distinct('user_id')
            if limit:
                return query[:limit]
            return query
    
    def get_users(self, user_ids: list = None):
        """
        Get user data
        Similar to get_users in UserService
        """
        with MongoDbContext(self.database) as db:
            if user_ids:
                users = UserProperty.objects(user_id__in=user_ids).distinct('user_id')
            else:
                users = UserProperty.objects().distinct('user_id')
            
            return list(users)
    
    def get_user_properties_count(self, user_id: str):
        """
        Get count of properties for a user
        """
        with MongoDbContext(self.database) as db:
            count = UserProperty.objects(user_id=user_id).count()
            return count
    
    def update_quality_notifications(self, user_id: str, notification_data: dict):
        """
        Update quality notification settings for user
        """
        with MongoDbContext(self.database) as db:
            # In a real implementation, this might update a separate user settings collection
            # For this example, we'll update properties owned by the user
            UserProperty.objects(user_id=user_id).update(
                set__quality_checks_enabled=notification_data.get('quality_enabled', True)
            )
    
    def get_users_with_quality_issues(self, min_quality_score: float = 0.8):
        """
        Get users who have properties with quality issues
        """
        with MongoDbContext(self.database) as db:
            # Find properties with low quality scores
            low_quality_properties = UserProperty.objects(
                quality_score__lt=min_quality_score
            ).distinct('user_id')
            
            return list(low_quality_properties)