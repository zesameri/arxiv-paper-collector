#!/usr/bin/env python3
"""
ArXiv Paper Collector
A comprehensive system for collecting and analyzing academic papers from multiple sources.
"""

import os
import json
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import arxiv
import requests
from Bio import Entrez
import pandas as pd
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class PaperDatabase:
    """SQLite database manager for storing papers and relationships"""
    
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Papers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                abstract TEXT,
                publication_date TEXT,
                arxiv_id TEXT UNIQUE,
                pubmed_id TEXT UNIQUE,
                doi TEXT UNIQUE,
                journal TEXT,
                citations INTEGER DEFAULT 0,
                keywords TEXT,
                institution_affiliations TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Author relationships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS author_collaborations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author1 TEXT NOT NULL,
                author2 TEXT NOT NULL,
                paper_id INTEGER,
                collaboration_count INTEGER DEFAULT 1,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
        ''')
        
        # Keywords table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                keyword TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_paper(self, paper: Paper) -> int:
        """Add a paper to the database and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO papers 
                (title, authors, abstract, publication_date, arxiv_id, pubmed_id, 
                 doi, journal, citations, keywords, institution_affiliations, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                paper.title,
                json.dumps(paper.authors),
                paper.abstract,
                paper.publication_date,
                paper.arxiv_id,
                paper.pubmed_id,
                paper.doi,
                paper.journal,
                paper.citations,
                json.dumps(paper.keywords),
                json.dumps(paper.institution_affiliations),
                paper.source
            ))
            
            paper_id = cursor.lastrowid
            
            # Add keywords
            for keyword in paper.keywords:
                cursor.execute('''
                    INSERT INTO paper_keywords (paper_id, keyword) VALUES (?, ?)
                ''', (paper_id, keyword))
            
            # Add author collaborations
            for i, author1 in enumerate(paper.authors):
                for author2 in paper.authors[i+1:]:
                    cursor.execute('''
                        INSERT OR REPLACE INTO author_collaborations 
                        (author1, author2, paper_id) VALUES (?, ?, ?)
                    ''', (author1, author2, paper_id))
            
            conn.commit()
            return paper_id
            
        except Exception as e:
            logger.error(f"Error adding paper to database: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def get_authors_by_frequency(self, limit: int = 50) -> List[Tuple[str, int]]:
        """Get most frequent authors in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT author1 as author, COUNT(*) as frequency
            FROM author_collaborations
            GROUP BY author1
            UNION ALL
            SELECT author2 as author, COUNT(*) as frequency
            FROM author_collaborations
            GROUP BY author2
            ORDER BY frequency DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results

class ArxivCollector:
    """Collector for arXiv papers"""
    
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
            
            logger.info(f"Found {len(papers)} papers for author: {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv for author {author_name}: {e}")
            return []
    
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
            
            logger.info(f"Found {len(papers)} papers for keywords: {keywords}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv for keywords {keywords}: {e}")
            return []

class PubMedCollector:
    """Collector for PubMed papers"""
    
    def __init__(self, email: str):
        Entrez.email = email
    
    @sleep_and_retry
    @limits(calls=3, period=1)  # Rate limit: 3 calls per second
    def search_by_author(self, author_name: str, max_results: int = 100) -> List[Paper]:
        """Search PubMed papers by author name"""
        try:
            # Search for papers
            handle = Entrez.esearch(
                db="pubmed", 
                term=f"{author_name}[Author]",
                retmax=max_results,
                sort="date"
            )
            search_results = Entrez.read(handle)
            handle.close()
            
            if not search_results["IdList"]:
                logger.info(f"No papers found for author: {author_name}")
                return []
            
            # Fetch paper details
            handle = Entrez.efetch(
                db="pubmed",
                id=search_results["IdList"],
                rettype="medline",
                retmode="xml"
            )
            papers_data = Entrez.read(handle)
            handle.close()
            
            papers = []
            for paper_data in papers_data['PubmedArticle']:
                article = paper_data['MedlineCitation']['Article']
                
                # Extract authors
                authors = []
                if 'AuthorList' in article:
                    for author in article['AuthorList']:
                        if 'LastName' in author and 'ForeName' in author:
                            authors.append(f"{author['ForeName']} {author['LastName']}")
                
                # Extract publication date
                pub_date = ""
                if 'DateCompleted' in paper_data['MedlineCitation']:
                    date_info = paper_data['MedlineCitation']['DateCompleted']
                    pub_date = f"{date_info['Year']}-{date_info.get('Month', '01')}-{date_info.get('Day', '01')}"
                
                paper = Paper(
                    title=article.get('ArticleTitle', ''),
                    authors=authors,
                    abstract=article.get('Abstract', {}).get('AbstractText', [''])[0] if article.get('Abstract') else '',
                    publication_date=pub_date,
                    pubmed_id=paper_data['MedlineCitation']['PMID'],
                    journal=article.get('Journal', {}).get('Title', ''),
                    source="pubmed"
                )
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers for author: {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching PubMed for author {author_name}: {e}")
            return []

class SemanticScholarCollector:
    """Collector for Semantic Scholar papers with citation data"""
    
    def __init__(self):
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
                logger.info(f"No author found: {author_name}")
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
            
            logger.info(f"Found {len(papers)} papers for author: {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar for author {author_name}: {e}")
            return []

class PaperCollector:
    """Main paper collection orchestrator"""
    
    def __init__(self, email: str, db_path: str = "papers.db"):
        self.db = PaperDatabase(db_path)
        self.arxiv_collector = ArxivCollector()
        self.pubmed_collector = PubMedCollector(email)
        self.semantic_scholar_collector = SemanticScholarCollector()
        self.collected_authors: Set[str] = set()
    
    def collect_from_author_list(self, authors: List[str], expand_network: bool = True, max_papers_per_author: int = 50):
        """Collect papers from a list of authors and optionally expand the network"""
        logger.info(f"Starting collection for {len(authors)} authors")
        
        all_papers = []
        
        for author in tqdm(authors, desc="Collecting papers by author"):
            if author in self.collected_authors:
                logger.info(f"Already collected papers for: {author}")
                continue
            
            # Collect from multiple sources
            arxiv_papers = self.arxiv_collector.search_by_author(author, max_papers_per_author)
            pubmed_papers = self.pubmed_collector.search_by_author(author, max_papers_per_author)
            semantic_papers = self.semantic_scholar_collector.search_by_author(author, max_papers_per_author)
            
            author_papers = arxiv_papers + pubmed_papers + semantic_papers
            
            # Store papers in database
            for paper in author_papers:
                paper_id = self.db.add_paper(paper)
                if paper_id > 0:
                    all_papers.append(paper)
            
            self.collected_authors.add(author)
            
            # Add delay between authors to be respectful
            time.sleep(2)
        
        if expand_network:
            self._expand_author_network(all_papers)
        
        logger.info(f"Collection complete. Total papers collected: {len(all_papers)}")
        return all_papers
    
    def _expand_author_network(self, papers: List[Paper], expansion_rounds: int = 2):
        """Expand the author network by finding co-authors"""
        logger.info("Expanding author network...")
        
        for round_num in range(expansion_rounds):
            # Get co-authors from collected papers
            new_authors = set()
            for paper in papers:
                for author in paper.authors:
                    if author not in self.collected_authors:
                        new_authors.add(author)
            
            # Limit expansion to most frequent co-authors
            frequent_authors = self.db.get_authors_by_frequency(limit=20)
            new_authors = {author for author, _ in frequent_authors if author not in self.collected_authors}
            
            if not new_authors:
                break
            
            logger.info(f"Round {round_num + 1}: Collecting papers for {len(new_authors)} co-authors")
            
            # Collect papers for new authors (fewer papers per author in expansion)
            new_papers = self.collect_from_author_list(
                list(new_authors)[:10],  # Limit to top 10 new authors
                expand_network=False,
                max_papers_per_author=20
            )
            
            papers.extend(new_papers)
    
    def collect_by_keywords(self, keywords: List[str], max_papers: int = 100):
        """Collect papers by research keywords"""
        logger.info(f"Collecting papers for keywords: {keywords}")
        
        arxiv_papers = self.arxiv_collector.search_by_keywords(keywords, max_papers)
        
        # Store in database
        for paper in arxiv_papers:
            self.db.add_paper(paper)
        
        return arxiv_papers
    
    def generate_network_analysis(self) -> Dict:
        """Generate collaboration network analysis"""
        logger.info("Generating network analysis...")
        
        # Create collaboration graph
        G = nx.Graph()
        
        # Get collaboration data from database
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT author1, author2, COUNT(*) as collaboration_count
            FROM author_collaborations
            GROUP BY author1, author2
        ''')
        
        collaborations = cursor.fetchall()
        conn.close()
        
        # Build graph
        for author1, author2, count in collaborations:
            G.add_edge(author1, author2, weight=count)
        
        # Calculate network metrics
        analysis = {
            "total_authors": G.number_of_nodes(),
            "total_collaborations": G.number_of_edges(),
            "average_collaborations_per_author": sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
            "most_collaborative_authors": sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10],
            "connected_components": nx.number_connected_components(G),
            "largest_component_size": len(max(nx.connected_components(G), key=len)) if G.number_of_nodes() > 0 else 0
        }
        
        return analysis

def main():
    """Main entry point for the paper collector"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArXiv Paper Collector")
    parser.add_argument("--email", required=True, help="Your email for PubMed API")
    parser.add_argument("--authors", nargs="+", help="List of author names to start with")
    parser.add_argument("--keywords", nargs="+", help="List of keywords to search for")
    parser.add_argument("--expand", action="store_true", help="Expand author network")
    parser.add_argument("--max-papers", type=int, default=50, help="Maximum papers per author")
    parser.add_argument("--analysis", action="store_true", help="Generate network analysis")
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = PaperCollector(args.email)
    
    # Collect papers
    if args.authors:
        collector.collect_from_author_list(
            args.authors,
            expand_network=args.expand,
            max_papers_per_author=args.max_papers
        )
    
    if args.keywords:
        collector.collect_by_keywords(args.keywords)
    
    # Generate analysis
    if args.analysis:
        analysis = collector.generate_network_analysis()
        print("\n=== Network Analysis ===")
        for key, value in analysis.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
