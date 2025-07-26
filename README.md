# Paper Collector for Synthetic Biology Research

A comprehensive tool for systematically collecting and analyzing academic papers to understand research networks, collaborations, and institutional relationships in synthetic biology and other research domains.

## 🎯 Overview

This project helps map the academic landscape by building a knowledge graph that connects:

- **Authors → Institutions → Research Areas → Papers**
- **Collaboration patterns between labs**
- **Research topic clusters and emerging areas**
- **Citation networks and influence patterns**

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./setup.sh
```

This script will:
- Install Poetry if needed
- Configure the correct Python version (3.11 or 3.12)
- Install all dependencies

### Option 2: Manual Setup

#### Prerequisites
- Python 3.11 or 3.12 (Poetry will handle virtual environments)
- [Poetry](https://python-poetry.org/) for dependency management

#### Install Dependencies

```bash
poetry install
```

### Interactive Quick Start

```bash
poetry run python quick_start.py
```

This will launch an interactive menu where you can:
- Collect papers by author names
- Collect papers by keywords
- Analyze existing collections
- Export data to CSV

### Command Line Usage

```bash
# Collect papers from specific authors with network expansion
poetry run python main.py --email your@email.com --authors "Drew Endy" "Christopher Voigt" --expand --max-papers 50

# Collect papers by keywords
poetry run python main.py --email your@email.com --keywords "synthetic biology" "gene circuit"

# Generate network analysis
poetry run python main.py --email your@email.com --analysis
```

## 📚 Features

### Multi-Source Collection
- **arXiv**: Academic preprints and papers
- **PubMed**: Biomedical literature  
- **Semantic Scholar**: Citation data and metrics

### Smart Network Expansion
- Start with seed authors from labs you're interested in
- Automatically discover co-authors and collaborators
- Expand collection based on collaboration frequency
- Build comprehensive research networks

### Data Analysis
- **Collaboration Networks**: Who works with whom
- **Research Topic Clustering**: Identify emerging areas
- **Citation Analysis**: Influence and impact metrics
- **Institutional Mapping**: Lab relationships and affiliations

### Data Management
- **SQLite Database**: Robust local storage
- **Deduplication**: Automatic handling of duplicate papers
- **Export Options**: CSV, JSON, and programmatic access
- **Incremental Collection**: Resume and expand existing collections

## 🔬 Usage Examples

### Example 1: Synthetic Biology Lab Collection

```python
from main import PaperCollector

collector = PaperCollector("your@email.com")

# Start with key synthetic biology researchers
synthetic_bio_authors = [
    "Drew Endy",
    "Christopher Voigt", 
    "James Collins",
    "Christina Smolke"
]

# Collect papers and expand network
papers = collector.collect_from_author_list(
    synthetic_bio_authors,
    expand_network=True,
    max_papers_per_author=30
)

# Analyze the network
analysis = collector.generate_network_analysis()
print(f"Network includes {analysis['total_authors']} authors")
```

### Example 2: Keyword-Based Discovery

```python
# Discover papers in emerging research areas
keywords = [
    "synthetic biology",
    "gene circuit", 
    "metabolic engineering",
    "CRISPR design"
]

papers = collector.collect_by_keywords(keywords, max_papers=100)
```

### Example 3: Lab-Specific Analysis

```python
# Compare different research groups
mit_researchers = ["Timothy Lu", "Christopher Voigt", "James Collins"]
stanford_researchers = ["Christina Smolke", "Drew Endy"]

mit_papers = collector.collect_from_author_list(mit_researchers, expand_network=False)
stanford_papers = collector.collect_from_author_list(stanford_researchers, expand_network=False)
```

## 📊 Analysis Capabilities

### Collaboration Network Analysis
```python
analysis = collector.generate_network_analysis()

# Key metrics:
# - Total authors and collaborations
# - Average collaborations per author  
# - Most collaborative researchers
# - Connected components and clusters
# - Network density and structure
```

### Export and Visualization
```python
# Export to CSV for external analysis
import pandas as pd
papers_df = pd.read_sql_query("SELECT * FROM papers", sqlite3.connect("papers.db"))
papers_df.to_csv("research_network.csv")

# Generate collaboration graphs with NetworkX
import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()
# Add edges based on co-authorships
nx.draw(G, with_labels=True)
plt.show()
```

## 🔧 Configuration

### Rate Limiting
The system includes built-in rate limiting to respect API limits:
- **arXiv**: 1 call per 3 seconds
- **PubMed**: 3 calls per second  
- **Semantic Scholar**: 100 calls per 5 minutes

### Database Schema
```sql
-- Papers table
papers (id, title, authors, abstract, publication_date, arxiv_id, pubmed_id, doi, journal, citations, keywords, source)

-- Collaboration tracking
author_collaborations (author1, author2, paper_id, collaboration_count)

-- Keyword indexing  
paper_keywords (paper_id, keyword)
```

## 🎛️ Advanced Usage

### Custom Collection Strategies

```python
class CustomCollector(PaperCollector):
    def collect_institutional_papers(self, institution: str):
        """Collect papers from a specific institution"""
        # Implementation for institution-based collection
        pass
    
    def collect_recent_papers(self, authors: list, days: int = 30):
        """Collect only recent papers from authors"""
        # Implementation for time-based filtering
        pass
```

### Batch Processing

```python
# Process multiple author lists
lab_groups = {
    "MIT_SynBio": ["Timothy Lu", "Christopher Voigt"],
    "Stanford_BioE": ["Christina Smolke", "Drew Endy"],
    "Harvard_Wyss": ["George Church", "Pamela Silver"]
}

for lab_name, authors in lab_groups.items():
    papers = collector.collect_from_author_list(authors)
    print(f"{lab_name}: {len(papers)} papers collected")
```

## 📈 Data Analysis Examples

### Research Trend Analysis
```python
# Analyze research trends over time
papers_by_year = papers_df.groupby('publication_date').size()
trending_keywords = papers_df['keywords'].value_counts().head(10)
```

### Citation Impact Analysis
```python
# Find highly cited papers and influential authors
high_impact_papers = papers_df[papers_df['citations'] > 100]
influential_authors = papers_df.groupby('authors')['citations'].sum().sort_values(ascending=False)
```

### Collaboration Pattern Analysis
```python
# Identify key collaboration hubs
collaboration_graph = nx.from_pandas_edgelist(collaborations_df, 'author1', 'author2')
centrality_scores = nx.betweenness_centrality(collaboration_graph)
hub_authors = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)[:10]
```

## 🔍 Research Applications

### 1. Literature Reviews
- Systematically collect papers in your research area
- Identify key authors and seminal works
- Track research evolution over time

### 2. Collaboration Discovery  
- Find potential collaborators in your field
- Identify research clusters and communities
- Map institutional relationships

### 3. Grant Writing
- Identify funding patterns and successful researchers
- Build comprehensive literature foundations
- Demonstrate research landscape knowledge

### 4. Academic Networking
- Discover researchers working on similar problems
- Identify conference and workshop participants
- Build comprehensive research networks

## 🚦 Best Practices

### Collection Strategy
1. **Start Small**: Begin with 3-5 key authors you know
2. **Expand Gradually**: Use network expansion to discover related researchers
3. **Use Keywords**: Supplement author-based collection with keyword searches
4. **Regular Updates**: Re-run collections periodically to capture new papers

### Data Quality
1. **Check Results**: Review collected papers for relevance
2. **Handle Duplicates**: The system automatically deduplicates, but manual review helps
3. **Verify Authors**: Check for name variations and author disambiguation
4. **Update Metadata**: Enhance papers with additional information as needed

### Ethical Considerations
1. **Respect Rate Limits**: Don't overwhelm APIs with requests
2. **Attribution**: Properly cite papers and data sources in your research
3. **Privacy**: Be mindful of researcher privacy when sharing network data
4. **Fair Use**: Use collected data for legitimate research purposes

## 🛠️ Troubleshooting

### Common Issues

**"No papers found for author"**
- Check author name spelling and variations
- Try different name formats (First Last, Last First, etc.)
- Author might not have papers in the selected databases

**"Rate limit exceeded"**
- Wait for the rate limit to reset
- Reduce the number of papers per author
- Consider running collections over longer time periods

**"Database connection error"**
- Ensure write permissions in the working directory
- Check available disk space
- Restart the application

### Performance Tips

- Use `max_papers_per_author` to limit collection size
- Set `expand_network=False` for focused collections
- Export data regularly to avoid large database files
- Consider running large collections overnight

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

If you encounter issues or have questions:
1. Check the troubleshooting section above
2. Review the example usage scripts
3. Open an issue on GitHub with details about your problem

---

**Happy researching! 🔬📚**
