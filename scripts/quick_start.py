#!/usr/bin/env python3
"""
Quick Start Script for Paper Collection
Simplified interface for common collection tasks
"""

from main import PaperCollector
import sys

def collect_from_authors():
    """Quick collection from a list of authors"""
    print("=== Quick Author-Based Collection ===")
    
    email = input("Enter your email for PubMed API: ")
    
    print("\nEnter author names (one per line, empty line to finish):")
    authors = []
    while True:
        author = input("> ").strip()
        if not author:
            break
        authors.append(author)
    
    if not authors:
        print("No authors provided!")
        return
    
    print(f"\nCollecting papers for {len(authors)} authors...")
    
    # Initialize collector
    collector = PaperCollector(email)
    
    # Collect papers
    papers = collector.collect_from_author_list(
        authors,
        expand_network=True,
        max_papers_per_author=30
    )
    
    print(f"\n✅ Collection complete! Found {len(papers)} papers")
    
    # Generate analysis
    analysis = collector.generate_network_analysis()
    print(f"📊 Network includes {analysis['total_authors']} authors with {analysis['total_collaborations']} collaborations")
    
    return papers

def collect_by_keywords():
    """Quick collection by keywords"""
    print("=== Quick Keyword-Based Collection ===")
    
    email = input("Enter your email for PubMed API: ")
    
    print("\nEnter keywords (separated by commas):")
    keywords_input = input("> ").strip()
    
    if not keywords_input:
        print("No keywords provided!")
        return
    
    keywords = [k.strip() for k in keywords_input.split(",")]
    
    print(f"\nCollecting papers for keywords: {keywords}")
    
    # Initialize collector
    collector = PaperCollector(email)
    
    # Collect papers
    papers = collector.collect_by_keywords(keywords, max_papers=100)
    
    print(f"\n✅ Collection complete! Found {len(papers)} papers")
    
    return papers

def analyze_existing_collection():
    """Analyze papers already in the database"""
    print("=== Analyze Existing Collection ===")
    
    collector = PaperCollector("dummy@email.com")  # Email not needed for analysis
    
    try:
        analysis = collector.generate_network_analysis()
        
        print("\n📊 Collection Statistics:")
        print(f"  • Total Authors: {analysis['total_authors']}")
        print(f"  • Total Collaborations: {analysis['total_collaborations']}")
        print(f"  • Avg Collaborations per Author: {analysis['average_collaborations_per_author']:.1f}")
        print(f"  • Connected Components: {analysis['connected_components']}")
        print(f"  • Largest Component: {analysis['largest_component_size']} authors")
        
        print(f"\n🤝 Top Collaborative Authors:")
        for i, (author, count) in enumerate(analysis['most_collaborative_authors'][:5]):
            print(f"  {i+1}. {author} ({count} collaborations)")
            
    except Exception as e:
        print(f"❌ Error analyzing collection: {e}")
        print("Make sure you have collected some papers first!")

def export_collection():
    """Export collection to CSV"""
    print("=== Export Collection ===")
    
    try:
        import sqlite3
        import pandas as pd
        
        # Check if database exists
        conn = sqlite3.connect("papers.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM papers")
        paper_count = cursor.fetchone()[0]
        
        if paper_count == 0:
            print("❌ No papers found in database. Collect some papers first!")
            conn.close()
            return
        
        print(f"Found {paper_count} papers in database")
        
        # Export to CSV
        papers_df = pd.read_sql_query("""
            SELECT 
                title, 
                authors, 
                publication_date,
                arxiv_id,
                pubmed_id,
                doi,
                journal,
                citations,
                source
            FROM papers
            ORDER BY publication_date DESC
        """, conn)
        
        conn.close()
        
        filename = "collected_papers.csv"
        papers_df.to_csv(filename, index=False)
        
        print(f"✅ Exported {len(papers_df)} papers to {filename}")
        
        # Show summary
        print(f"\n📈 Export Summary:")
        print(f"  • Date range: {papers_df['publication_date'].min()} to {papers_df['publication_date'].max()}")
        print(f"  • Sources: {dict(papers_df['source'].value_counts())}")
        
    except Exception as e:
        print(f"❌ Error exporting: {e}")

def main_menu():
    """Main interactive menu"""
    print("""
🔬 ArXiv Paper Collector - Quick Start
=====================================

Choose an option:
1. Collect papers by author names
2. Collect papers by keywords  
3. Analyze existing collection
4. Export collection to CSV
5. Exit

""")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        collect_from_authors()
    elif choice == "2":
        collect_by_keywords()
    elif choice == "3":
        analyze_existing_collection()
    elif choice == "4":
        export_collection()
    elif choice == "5":
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice. Please enter 1-5.")
    
    # Ask if user wants to continue
    print("\n" + "="*50)
    continue_choice = input("Continue? (y/N): ").strip().lower()
    if continue_choice == 'y':
        main_menu()
    else:
        print("👋 Goodbye!")

if __name__ == "__main__":
    print("""
🔬 ArXiv Paper Collector
========================
Welcome! This tool helps you collect and analyze academic papers.

Before starting:
1. Install Poetry: curl -sSL https://install.python-poetry.org | python3 -
2. Install dependencies: poetry install  
3. Have your email ready (required for PubMed API access)

""")
    
    main_menu() 