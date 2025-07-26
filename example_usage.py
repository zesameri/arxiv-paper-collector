#!/usr/bin/env python3
"""
Example usage of the ArXiv Paper Collector
"""

from main import PaperCollector
import json

def example_synthetic_biology_collection():
    """Example: Collect papers from synthetic biology labs"""
    
    # Initialize collector (replace with your email)
    collector = PaperCollector("your_email@domain.com")
    
    # Some well-known synthetic biology researchers to start with
    synthetic_bio_authors = [
        "Drew Endy",
        "Tom Knight", 
        "Christopher Voigt",
        "James Collins",
        "Ahmad Khalil",
        "Christina Smolke",
        "Jay Keasling",
        "George Church"
    ]
    
    print("Starting synthetic biology paper collection...")
    
    # Collect papers and expand network
    papers = collector.collect_from_author_list(
        synthetic_bio_authors,
        expand_network=True,
        max_papers_per_author=30
    )
    
    print(f"Collected {len(papers)} papers")
    
    # Generate network analysis
    analysis = collector.generate_network_analysis()
    
    print("\n=== Network Analysis ===")
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    return papers, analysis

def example_keyword_based_collection():
    """Example: Collect papers by research keywords"""
    
    collector = PaperCollector("your_email@domain.com")
    
    # Synthetic biology keywords
    keywords = [
        "synthetic biology",
        "gene circuit",
        "bioengineering",
        "metabolic engineering"
    ]
    
    print(f"Collecting papers for keywords: {keywords}")
    
    papers = collector.collect_by_keywords(keywords, max_papers=100)
    
    print(f"Collected {len(papers)} papers by keywords")
    
    return papers

def example_specific_lab_collection():
    """Example: Collect papers from specific labs/institutions"""
    
    collector = PaperCollector("your_email@domain.com")
    
    # MIT Synthetic Biology Center researchers
    mit_synthetic_bio = [
        "Timothy Lu",
        "Christopher Voigt", 
        "James Collins",
        "Ron Weiss"
    ]
    
    # Stanford Bioengineering researchers
    stanford_bioeng = [
        "Christina Smolke",
        "Drew Endy",
        "Manu Prakash"
    ]
    
    # Combine and collect
    lab_researchers = mit_synthetic_bio + stanford_bioeng
    
    papers = collector.collect_from_author_list(
        lab_researchers,
        expand_network=False,  # Don't expand for focused lab study
        max_papers_per_author=50
    )
    
    print(f"Collected {len(papers)} papers from target labs")
    
    return papers

def analyze_collaboration_patterns():
    """Example: Analyze collaboration patterns in collected data"""
    
    collector = PaperCollector("your_email@domain.com")
    
    # Generate analysis
    analysis = collector.generate_network_analysis()
    
    print("=== Collaboration Analysis ===")
    print(f"Total Authors: {analysis['total_authors']}")
    print(f"Total Collaborations: {analysis['total_collaborations']}")
    print(f"Average Collaborations per Author: {analysis['average_collaborations_per_author']:.2f}")
    
    print("\n=== Most Collaborative Authors ===")
    for author, collab_count in analysis['most_collaborative_authors']:
        print(f"{author}: {collab_count} collaborations")
    
    print(f"\nConnected Components: {analysis['connected_components']}")
    print(f"Largest Component Size: {analysis['largest_component_size']}")

def export_papers_to_csv():
    """Example: Export collected papers to CSV for further analysis"""
    
    import sqlite3
    import pandas as pd
    
    # Connect to database
    conn = sqlite3.connect("papers.db")
    
    # Read papers into DataFrame
    papers_df = pd.read_sql_query("""
        SELECT 
            title, 
            authors, 
            abstract,
            publication_date,
            arxiv_id,
            pubmed_id,
            doi,
            journal,
            citations,
            keywords,
            source,
            created_at
        FROM papers
        ORDER BY publication_date DESC
    """, conn)
    
    conn.close()
    
    # Save to CSV
    papers_df.to_csv("collected_papers.csv", index=False)
    print(f"Exported {len(papers_df)} papers to collected_papers.csv")
    
    # Basic statistics
    print(f"\n=== Paper Statistics ===")
    print(f"Total Papers: {len(papers_df)}")
    print(f"Date Range: {papers_df['publication_date'].min()} to {papers_df['publication_date'].max()}")
    print(f"Sources: {papers_df['source'].value_counts().to_dict()}")
    
    return papers_df

if __name__ == "__main__":
    # Uncomment the example you want to run:
    
    # 1. Comprehensive synthetic biology collection
    # example_synthetic_biology_collection()
    
    # 2. Keyword-based collection
    # example_keyword_based_collection()
    
    # 3. Specific lab collection
    # example_specific_lab_collection()
    
    # 4. Analyze existing data
    # analyze_collaboration_patterns()
    
    # 5. Export to CSV
    # export_papers_to_csv()
    
    print("Uncomment the example you want to run in the main section!") 