"""
ArXiv paper collector
"""

from typing import List
import arxiv
from ratelimit import limits, sleep_and_retry

from shared.models.paper import Paper
from .base_collector import BaseCollector


class ArxivCollector(BaseCollector):
    """Collector for arXiv papers"""
    
    def __init__(self):
        super().__init__("arxiv")
    
    @sleep_and_retry
    @limits(calls=1, period=3)  # Rate limit: 1 call per 3 seconds
    def search_by_author(self, author_name: str, max_results: int = 100) -> List[Paper]:
        """Search arXiv papers by author name"""
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=f"au:{author_name}",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in client.results(search):
                paper = Paper(
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    publication_date=result.published.strftime('%Y-%m-%d'),
                    arxiv_id=result.entry_id.split('/')[-1],
                    doi=getattr(result, 'doi', None),
                    journal=getattr(result, 'journal_ref', None),
                    keywords=[category for category in result.categories],
                    source="arxiv"
                )
                papers.append(paper)
            
            self.log_result(author_name, papers)
            return papers
            
        except Exception as e:
            return self.handle_error("search_by_author", author_name, e)
    
    @sleep_and_retry
    @limits(calls=1, period=3)
    def search_by_keywords(self, keywords: List[str], max_results: int = 100) -> List[Paper]:
        """Search arXiv papers by keywords"""
        try:
            query = " AND ".join([f'"{keyword}"' for keyword in keywords])
            
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in client.results(search):
                paper = Paper(
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    publication_date=result.published.strftime('%Y-%m-%d'),
                    arxiv_id=result.entry_id.split('/')[-1],
                    doi=getattr(result, 'doi', None),
                    journal=getattr(result, 'journal_ref', None),
                    keywords=[category for category in result.categories],
                    source="arxiv"
                )
                papers.append(paper)
            
            keywords_str = ", ".join(keywords)
            self.log_result(keywords_str, papers)
            return papers
            
        except Exception as e:
            keywords_str = ", ".join(keywords)
            return self.handle_error("search_by_keywords", keywords_str, e) 