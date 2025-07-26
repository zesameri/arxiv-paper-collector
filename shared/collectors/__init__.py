"""
Paper collection modules for various academic databases
"""

from .arxiv_collector import ArxivCollector
from .pubmed_collector import PubMedCollector  
from .semantic_scholar_collector import SemanticScholarCollector
from .base_collector import BaseCollector

__all__ = [
    'ArxivCollector',
    'PubMedCollector', 
    'SemanticScholarCollector',
    'BaseCollector'
] 