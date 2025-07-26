"""
Core data models for paper collection system
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Paper:
    """Data class for storing paper information"""
    title: str
    authors: List[str]
    abstract: str
    publication_date: str
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    citations: int = 0
    keywords: List[str] = None
    institution_affiliations: List[str] = None
    source: str = "unknown"
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.institution_affiliations is None:
            self.institution_affiliations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert paper to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """Create Paper instance from dictionary"""
        return cls(**data)
    
    def get_unique_id(self) -> str:
        """Get a unique identifier for this paper"""
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id}"
        elif self.pubmed_id:
            return f"pubmed:{self.pubmed_id}"
        elif self.doi:
            return f"doi:{self.doi}"
        else:
            # Fallback to title hash
            import hashlib
            return f"title:{hashlib.md5(self.title.encode()).hexdigest()[:8]}"


@dataclass
class Author:
    """Data class for author information"""
    name: str
    email: Optional[str] = None
    affiliation: Optional[str] = None
    orcid_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Collaboration:
    """Data class for collaboration relationships"""
    author1: str
    author2: str
    paper_count: int = 1
    papers: List[str] = None  # List of paper IDs
    
    def __post_init__(self):
        if self.papers is None:
            self.papers = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkAnalysis:
    """Data class for network analysis results"""
    total_authors: int
    total_collaborations: int
    average_collaborations_per_author: float
    most_collaborative_authors: List[tuple]
    connected_components: int
    largest_component_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self) 