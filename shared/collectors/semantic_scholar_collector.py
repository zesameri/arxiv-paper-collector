"""
Semantic Scholar paper collector
"""

from typing import List
import requests
from ratelimit import limits, sleep_and_retry

from shared.models.paper import Paper
from .base_collector import BaseCollector


class SemanticScholarCollector(BaseCollector):
    """Collector for Semantic Scholar papers with citation data"""
    
    def __init__(self):
        super().__init__("semantic_scholar")
        self.base_url = "https://api.semanticscholar.org/graph/v1"
    
    @sleep_and_retry
    @limits(calls=100, period=300)  # Rate limit: 100 calls per 5 minutes
    def search_by_author(self, author_name: str, max_results: int = 100) -> List[Paper]:
        """Search Semantic Scholar papers by author name"""
        try:
            # First, find the author ID
            response = requests.get(
                f"{self.base_url}/author/search",
                params={"query": author_name, "limit": 1}
            )
            response.raise_for_status()
            
            authors_data = response.json()
            if not authors_data.get("data"):
                self.logger.info(f"No author found: {author_name}")
                return []
            
            author_id = authors_data["data"][0]["authorId"]
            
            # Get author's papers
            response = requests.get(
                f"{self.base_url}/author/{author_id}/papers",
                params={
                    "fields": "title,authors,abstract,year,citationCount,journal,externalIds",
                    "limit": max_results
                }
            )
            response.raise_for_status()
            
            papers_data = response.json()
            papers = []
            
            for paper_data in papers_data.get("data", []):
                authors = [author["name"] for author in paper_data.get("authors", [])]
                
                paper = Paper(
                    title=paper_data.get("title", ""),
                    authors=authors,
                    abstract=paper_data.get("abstract", ""),
                    publication_date=f"{paper_data.get('year', '')}-01-01" if paper_data.get('year') else "",
                    arxiv_id=paper_data.get("externalIds", {}).get("ArXiv"),
                    pubmed_id=paper_data.get("externalIds", {}).get("PubMed"),
                    doi=paper_data.get("externalIds", {}).get("DOI"),
                    journal=paper_data.get("journal", {}).get("name") if paper_data.get("journal") else "",
                    citations=paper_data.get("citationCount", 0),
                    source="semantic_scholar"
                )
                papers.append(paper)
            
            self.log_result(author_name, papers)
            return papers
            
        except Exception as e:
            return self.handle_error("search_by_author", author_name, e)
    
    def search_by_keywords(self, keywords: List[str], max_results: int = 100) -> List[Paper]:
        """Search Semantic Scholar papers by keywords"""
        try:
            # Semantic Scholar doesn't have direct keyword search, 
            # so we'll search by title/abstract query
            query = " ".join(keywords)
            
            response = requests.get(
                f"{self.base_url}/paper/search",
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": "title,authors,abstract,year,citationCount,journal,externalIds"
                }
            )
            response.raise_for_status()
            
            papers_data = response.json()
            papers = []
            
            for paper_data in papers_data.get("data", []):
                authors = [author["name"] for author in paper_data.get("authors", [])]
                
                paper = Paper(
                    title=paper_data.get("title", ""),
                    authors=authors,
                    abstract=paper_data.get("abstract", ""),
                    publication_date=f"{paper_data.get('year', '')}-01-01" if paper_data.get('year') else "",
                    arxiv_id=paper_data.get("externalIds", {}).get("ArXiv"),
                    pubmed_id=paper_data.get("externalIds", {}).get("PubMed"),
                    doi=paper_data.get("externalIds", {}).get("DOI"),
                    journal=paper_data.get("journal", {}).get("name") if paper_data.get("journal") else "",
                    citations=paper_data.get("citationCount", 0),
                    source="semantic_scholar"
                )
                papers.append(paper)
            
            keywords_str = ", ".join(keywords)
            self.log_result(keywords_str, papers)
            return papers
            
        except Exception as e:
            keywords_str = ", ".join(keywords)
            return self.handle_error("search_by_keywords", keywords_str, e) 