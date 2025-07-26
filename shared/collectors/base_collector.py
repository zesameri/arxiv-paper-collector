"""
Base collector class defining the interface for paper collection
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from shared.models.paper import Paper

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for paper collectors"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def search_by_author(self, author_name: str, max_results: int = 100) -> List[Paper]:
        """Search papers by author name"""
        pass
    
    @abstractmethod
    def search_by_keywords(self, keywords: List[str], max_results: int = 100) -> List[Paper]:
        """Search papers by keywords"""
        pass
    
    def log_result(self, author_or_keywords: str, papers: List[Paper]):
        """Log collection results"""
        self.logger.info(f"Found {len(papers)} papers for: {author_or_keywords}")
    
    def handle_error(self, operation: str, target: str, error: Exception):
        """Handle and log errors consistently"""
        self.logger.error(f"Error in {operation} for {target}: {error}")
        return [] 