"""
PubMed paper collector (currently disabled due to maintenance)
"""

from typing import List
from shared.models.paper import Paper
from .base_collector import BaseCollector


class PubMedCollector(BaseCollector):
    """Collector for PubMed papers (disabled during maintenance)"""
    
    def __init__(self, email: str = None):
        super().__init__("pubmed")
        self.email = email
        self.maintenance_mode = True  # Enable when PubMed is back online
    
    def search_by_author(self, author_name: str, max_results: int = 100) -> List[Paper]:
        """Search PubMed papers by author name"""
        if self.maintenance_mode:
            self.logger.warning("PubMed is currently under maintenance. Skipping collection.")
            return []
        
        # TODO: Implement PubMed search when service is restored
        # Original implementation available in scripts/main.py
        return []
    
    def search_by_keywords(self, keywords: List[str], max_results: int = 100) -> List[Paper]:
        """Search PubMed papers by keywords"""
        if self.maintenance_mode:
            self.logger.warning("PubMed is currently under maintenance. Skipping collection.")
            return []
        
        # TODO: Implement keyword search when service is restored
        return [] 