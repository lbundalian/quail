import logging
from typing import Optional, Dict, Any
import mongoengine
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .base import IDbContext


class MongoDbContext(IDbContext):
    """MongoDB context manager using PyMongo and MongoEngine"""
    
    def __init__(self, 
                 connection_string: str, 
                 database_name: str,
                 timeout_minutes: int = 120,
                 **kwargs):
        self.connection_string = connection_string
        self.database_name = database_name
        self.timeout_ms = timeout_minutes * 60 * 1000
        self.connection_kwargs = kwargs
        self.client = None
        self.database = None
        self.connection = None

    def __enter__(self):
        """Initialize MongoDB connection"""
        try:
            # Disconnect any existing connections
            mongoengine.disconnect()
            
            # Create MongoClient
            self.client = MongoClient(
                self.connection_string,
                socketTimeoutMS=self.timeout_ms,
                connectTimeoutMS=self.timeout_ms,
                **self.connection_kwargs
            )
            
            # Get database
            self.database = self.client[self.database_name]
            
            # Connect with MongoEngine for ODM support
            self.connection = mongoengine.connect(
                db=self.database_name,
                host=self.connection_string,
                socketTimeoutMS=self.timeout_ms,
                connectTimeoutMS=self.timeout_ms,
                **self.connection_kwargs
            )
            
            return self
            
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up MongoDB resources"""
        if exc_type is not None:
            logging.error(f"Exception in MongoDB context: Type={exc_type}, Value={exc_val}")
        
        self.close()

    def get_session(self):
        """Get database connection (returns the database object)"""
        if not self.database:
            raise RuntimeError("MongoDB not initialized. Use context manager.")
        return self.database

    def get_client(self):
        """Get MongoDB client"""
        if not self.client:
            raise RuntimeError("MongoDB client not initialized. Use context manager.")
        return self.client

    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        if not self.database:
            raise RuntimeError("MongoDB not initialized. Use context manager.")
        return self.database[collection_name]

    def close(self):
        """Close MongoDB connection"""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logging.error(f"Error closing MongoEngine connection: {e}")
        
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logging.error(f"Error closing MongoDB client: {e}")

    def find_documents(self, collection_name: str, query: Dict[str, Any] = None, **kwargs):
        """Find documents in a collection"""
        try:
            collection = self.get_collection(collection_name)
            return collection.find(query or {}, **kwargs)
        except PyMongoError as e:
            logging.error(f"Failed to find documents in {collection_name}: {e}")
            raise e

    def insert_document(self, collection_name: str, document: Dict[str, Any]):
        """Insert a document into a collection"""
        try:
            collection = self.get_collection(collection_name)
            return collection.insert_one(document)
        except PyMongoError as e:
            logging.error(f"Failed to insert document into {collection_name}: {e}")
            raise e

    def update_document(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any], **kwargs):
        """Update documents in a collection"""
        try:
            collection = self.get_collection(collection_name)
            return collection.update_many(query, update, **kwargs)
        except PyMongoError as e:
            logging.error(f"Failed to update documents in {collection_name}: {e}")
            raise e

    def delete_documents(self, collection_name: str, query: Dict[str, Any]):
        """Delete documents from a collection"""
        try:
            collection = self.get_collection(collection_name)
            return collection.delete_many(query)
        except PyMongoError as e:
            logging.error(f"Failed to delete documents from {collection_name}: {e}")
            raise e