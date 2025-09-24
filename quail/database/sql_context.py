import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

from .base import IDbContext


class SqlDbContext(IDbContext):
    """SQL Database context manager using SQLAlchemy"""
    
    def __init__(self, connection_string: str, schema: Optional[str] = None, **engine_kwargs):
        self.connection_string = connection_string
        self.schema = schema
        self.engine_kwargs = engine_kwargs
        self.engine = None
        self.session = None
        self._session_factory = None
        self.metadata = None
        self.tables: Dict[str, Table] = {}
        self.table_registry: Dict[str, str] = {}
        
        # Create base declarative class
        self.Base = declarative_base()
        
    def __enter__(self):
        """Initialize database connection and session"""
        try:
            # Create engine with connection pooling and error handling
            engine_config = {
                'pool_pre_ping': True,
                'future': True,
                **self.engine_kwargs
            }
            self.engine = create_engine(self.connection_string, **engine_config)
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self.engine, 
                autoflush=False, 
                expire_on_commit=False,
                future=True
            )
            
            # Create session
            self.session = self._session_factory()
            
            # Initialize metadata
            self.metadata = MetaData(schema=self.schema) if self.schema else MetaData()
            self.metadata.bind = self.engine
            
            return self
            
        except SQLAlchemyError as e:
            logging.error(f"Failed to initialize SQL database connection: {e}")
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up database resources"""
        if exc_type is not None:
            logging.error(f"Exception in SQL context: Type={exc_type}, Value={exc_val}")
            if self.session:
                self.session.rollback()
        
        self.close()

    def get_session(self) -> Session:
        """Get the current database session"""
        if not self.session:
            raise RuntimeError("Database session not initialized. Use context manager.")
        return self.session

    def get_new_session(self) -> Session:
        """Create a new database session"""
        if not self._session_factory:
            raise RuntimeError("Session factory not initialized. Use context manager.")
        return self._session_factory()

    def close(self):
        """Close database connection and cleanup resources"""
        if self.session:
            try:
                self.session.close()
            except SQLAlchemyError as e:
                logging.error(f"Error closing session: {e}")

        if self.engine:
            try:
                self.engine.dispose()
            except SQLAlchemyError as e:
                logging.error(f"Error disposing engine: {e}")

    def reflect_table(self, table_name: str, schema: Optional[str] = None, alias: Optional[str] = None) -> Table:
        """Reflect a single table from the database"""
        schema = schema or self.schema
        alias = alias or table_name
        key = f"{schema}.{table_name}" if schema else table_name
        
        if key in self.tables:
            return self.tables[key]
            
        try:
            # Create metadata for this specific table
            table_metadata = MetaData(schema=schema)
            table = Table(table_name, table_metadata, schema=schema, autoload_with=self.engine)
            
            # Store in tables registry
            self.tables[key] = table
            self.table_registry[alias] = key
            
            return table
            
        except SQLAlchemyError as e:
            logging.error(f"Failed to reflect table '{table_name}' in schema '{schema}': {e}")
            raise e

    def reflect_tables(self, table_configs: list) -> Dict[str, Table]:
        """Reflect multiple tables based on configuration"""
        reflected = {}
        
        for config in table_configs:
            if isinstance(config, str):
                # Simple string format: "table_name"
                table_name = config
                schema = self.schema
                alias = config
            elif isinstance(config, dict):
                # Dict format: {"name": "table_name", "schema": "schema", "alias": "alias"}
                table_name = config.get("name") or config.get("table")
                if not table_name:
                    continue
                schema = config.get("schema", self.schema)
                alias = config.get("alias", table_name)
            else:
                continue
                
            try:
                table = self.reflect_table(table_name, schema, alias)
                reflected[alias] = table
            except Exception as e:
                logging.warning(f"Failed to reflect table {table_name}: {e}")
                continue
                
        return reflected

    def get_table(self, alias_or_key: str) -> Table:
        """Get table by alias or fully qualified key"""
        # Try alias first
        key = self.table_registry.get(alias_or_key, alias_or_key)
        
        if key not in self.tables:
            raise KeyError(f"Table '{alias_or_key}' not found. Available tables: {list(self.tables.keys())}")
            
        return self.tables[key]

    def execute_query(self, query, **kwargs):
        """Execute a query and return results"""
        try:
            return self.session.execute(query, **kwargs)
        except SQLAlchemyError as e:
            logging.error(f"Query execution failed: {e}")
            self.session.rollback()
            raise e

    def commit(self):
        """Commit current transaction"""
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            logging.error(f"Commit failed: {e}")
            self.session.rollback()
            raise e