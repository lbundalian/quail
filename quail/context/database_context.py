from typing import Dict, Any, Optional
from ..database import SqlDbContext, MongoDbContext


class DatabaseContext:
    """Context for managing database connections and configurations"""
    
    def __init__(self, database_config: Dict[str, Any]):
        self.config = database_config
        self.sql_contexts = {}
        self.mongo_contexts = {}
    
    def create_sql_context(self, name: str, config: Dict[str, Any]) -> SqlDbContext:
        """Create and register a SQL database context"""
        context = SqlDbContext(
            connection_string=config['url'],
            schema=config.get('schema'),
            **config.get('options', {})
        )
        self.sql_contexts[name] = context
        return context
    
    def create_mongo_context(self, name: str, config: Dict[str, Any]) -> MongoDbContext:
        """Create and register a MongoDB context"""
        context = MongoDbContext(
            connection_string=config['url'],
            database_name=config['database'],
            timeout_minutes=config.get('timeout_minutes', 120),
            **config.get('options', {})
        )
        self.mongo_contexts[name] = context
        return context
    
    def get_sql_context(self, name: str) -> Optional[SqlDbContext]:
        """Get SQL context by name"""
        return self.sql_contexts.get(name)
    
    def get_mongo_context(self, name: str) -> Optional[MongoDbContext]:
        """Get MongoDB context by name"""
        return self.mongo_contexts.get(name)
    
    def get_primary_sql_context(self) -> Optional[SqlDbContext]:
        """Get the primary SQL context (first one registered)"""
        if self.sql_contexts:
            return next(iter(self.sql_contexts.values()))
        return None
    
    def get_primary_mongo_context(self) -> Optional[MongoDbContext]:
        """Get the primary MongoDB context (first one registered)"""
        if self.mongo_contexts:
            return next(iter(self.mongo_contexts.values()))
        return None
    
    def test_all_connections(self) -> Dict[str, Dict[str, bool]]:
        """Test all registered database connections"""
        results = {'sql': {}, 'mongo': {}}
        
        # Test SQL connections
        for name, context in self.sql_contexts.items():
            try:
                with context as db:
                    db.execute_query("SELECT 1")
                    results['sql'][name] = True
            except Exception:
                results['sql'][name] = False
        
        # Test MongoDB connections
        for name, context in self.mongo_contexts.items():
            try:
                with context as db:
                    db.get_session().list_collection_names()
                    results['mongo'][name] = True
            except Exception:
                results['mongo'][name] = False
        
        return results
    
    def cleanup_all(self):
        """Cleanup all database contexts"""
        for context in self.sql_contexts.values():
            context.close()
        
        for context in self.mongo_contexts.values():
            context.close()
        
        self.sql_contexts.clear()
        self.mongo_contexts.clear()