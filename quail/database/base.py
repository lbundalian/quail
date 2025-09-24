from abc import ABC, abstractmethod
from typing import Any


class IDbContext(ABC):
    """Abstract base class for database contexts"""

    @abstractmethod
    def __enter__(self):
        """Context manager entry"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup"""
        pass

    @abstractmethod
    def get_session(self):
        """Get database session/connection"""
        pass

    @abstractmethod
    def close(self):
        """Close database connection"""
        pass