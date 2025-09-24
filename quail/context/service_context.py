from typing import Dict, Any, Optional
from ..database import SqlDbContext, MongoDbContext
from ..services import SqlService, MongoService, QualityService, ReportService


class ServiceContext:
    """Context for managing all services with dependency injection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.environment = config.get('environment', 'dev')
        
        # Database contexts
        self.sql_context = None
        self.mongo_context = None
        
        # Services
        self.sql_service = None
        self.mongo_service = None
        self.quality_service = None
        self.report_service = None
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services based on configuration"""
        # Initialize SQL context and service
        if 'sql' in self.config:
            sql_config = self.config['sql']
            self.sql_context = SqlDbContext(
                connection_string=sql_config['url'],
                schema=sql_config.get('schema'),
                **sql_config.get('engine_options', {})
            )
            self.sql_service = SqlService(self.sql_context, self.environment)
            self.sql_service.initialize()
        
        # Initialize MongoDB context and service
        if 'mongo' in self.config:
            mongo_config = self.config['mongo']
            self.mongo_context = MongoDbContext(
                connection_string=mongo_config['url'],
                database_name=mongo_config['database'],
                timeout_minutes=mongo_config.get('timeout_minutes', 120)
            )
            self.mongo_service = MongoService(self.mongo_context, self.environment)
            self.mongo_service.initialize()
        
        # Initialize integrated quality service
        if self.sql_service and self.mongo_service:
            self.quality_service = QualityService(self.sql_service, self.mongo_service)
            self.report_service = ReportService(self.quality_service)
    
    def get_sql_service(self) -> Optional[SqlService]:
        """Get SQL service instance"""
        return self.sql_service
    
    def get_mongo_service(self) -> Optional[MongoService]:
        """Get MongoDB service instance"""
        return self.mongo_service
    
    def get_quality_service(self) -> Optional[QualityService]:
        """Get quality service instance"""
        return self.quality_service
    
    def get_report_service(self) -> Optional[ReportService]:
        """Get report service instance"""
        return self.report_service
    
    def reflect_tables(self, table_configs: list) -> Dict[str, Any]:
        """Reflect tables using SQL service"""
        if not self.sql_service:
            raise RuntimeError("SQL service not initialized")
        
        with self.sql_context as db:
            reflected_tables = db.reflect_tables(table_configs)
            return {
                'reflected': list(reflected_tables.keys()),
                'registry': db.table_registry,
                'total_tables': len(reflected_tables)
            }
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all database connections"""
        results = {}
        
        if self.sql_service:
            results['sql'] = self.sql_service.test_connection()
        
        if self.mongo_service:
            try:
                with self.mongo_context as db:
                    # Simple test - list collections
                    db.get_session().list_collection_names()
                    results['mongo'] = True
            except Exception:
                results['mongo'] = False
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {
            'environment': self.environment,
            'services': {
                'sql_service': self.sql_service is not None,
                'mongo_service': self.mongo_service is not None,
                'quality_service': self.quality_service is not None,
                'report_service': self.report_service is not None
            }
        }
        
        # Test connections
        connection_status = self.test_connections()
        status['connections'] = connection_status
        
        return status
    
    def cleanup(self):
        """Cleanup all service resources"""
        if self.sql_context:
            self.sql_context.close()
        
        if self.mongo_context:
            self.mongo_context.close()