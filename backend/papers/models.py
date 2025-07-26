"""
Django models for paper collection system
"""

from django.db import models
from django.utils import timezone
import json

# Use JSONField instead of ArrayField for SQLite compatibility
try:
    from django.contrib.postgres.fields import ArrayField
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class Author(models.Model):
    """Model for storing author information"""
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, null=True)
    affiliation = models.CharField(max_length=500, blank=True, null=True)
    orcid_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['orcid_id']),
        ]
    
    def __str__(self):
        return self.name


class Paper(models.Model):
    """Model for storing paper information"""
    SOURCE_CHOICES = [
        ('arxiv', 'ArXiv'),
        ('pubmed', 'PubMed'),
        ('semantic_scholar', 'Semantic Scholar'),
        ('manual', 'Manual Entry'),
        ('unknown', 'Unknown'),
    ]
    
    title = models.TextField()
    abstract = models.TextField(blank=True)
    publication_date = models.DateField()
    arxiv_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    pubmed_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    doi = models.CharField(max_length=200, blank=True, null=True, unique=True)
    journal = models.CharField(max_length=300, blank=True, null=True)
    citations = models.IntegerField(default=0)
    keywords = models.JSONField(blank=True, default=list)
    institution_affiliations = models.JSONField(blank=True, default=list)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='unknown')
    
    # Relationships
    authors = models.ManyToManyField(Author, through='PaperAuthor')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['publication_date']),
            models.Index(fields=['source']),
            models.Index(fields=['arxiv_id']),
            models.Index(fields=['pubmed_id']),
            models.Index(fields=['doi']),
            models.Index(fields=['citations']),
        ]
        unique_together = ['title', 'publication_date']  # Prevent exact duplicates
    
    def __str__(self):
        return f"{self.title[:100]}... ({self.publication_date})"
    
    def get_unique_id(self):
        """Get a unique identifier for this paper"""
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id}"
        elif self.pubmed_id:
            return f"pubmed:{self.pubmed_id}"
        elif self.doi:
            return f"doi:{self.doi}"
        else:
            return f"paper:{self.id}"
    
    def to_dict(self):
        """Convert to dictionary for API serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'authors': [author.name for author in self.authors.all()],
            'abstract': self.abstract,
            'publication_date': self.publication_date.isoformat(),
            'arxiv_id': self.arxiv_id,
            'pubmed_id': self.pubmed_id,
            'doi': self.doi,
            'journal': self.journal,
            'citations': self.citations,
            'keywords': self.keywords,
            'institution_affiliations': self.institution_affiliations,
            'source': self.source,
            'unique_id': self.get_unique_id(),
        }


class PaperAuthor(models.Model):
    """Through model for Paper-Author relationship with order"""
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  # Author order in the paper
    is_corresponding = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['paper', 'author']
        ordering = ['order']
    
    def __str__(self):
        return f"{self.author.name} - {self.paper.title[:50]}..."


class Collaboration(models.Model):
    """Model for tracking author collaborations"""
    author1 = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='collaborations_as_author1')
    author2 = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='collaborations_as_author2')
    paper_count = models.PositiveIntegerField(default=1)
    papers = models.ManyToManyField(Paper, blank=True)
    first_collaboration = models.DateField()
    last_collaboration = models.DateField()
    
    class Meta:
        unique_together = ['author1', 'author2']
        indexes = [
            models.Index(fields=['paper_count']),
            models.Index(fields=['first_collaboration']),
        ]
    
    def __str__(self):
        return f"{self.author1.name} & {self.author2.name} ({self.paper_count} papers)"
    
    def save(self, *args, **kwargs):
        # Ensure author1 is always "smaller" to avoid duplicates
        if self.author1.name > self.author2.name:
            self.author1, self.author2 = self.author2, self.author1
        super().save(*args, **kwargs)


class Collection(models.Model):
    """Model for organizing papers into collections"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    papers = models.ManyToManyField(Paper, blank=True)
    created_by = models.CharField(max_length=100, blank=True)  # Could be linked to User model later
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def paper_count(self):
        return self.papers.count()


class CollectionTask(models.Model):
    """Model for tracking paper collection tasks"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=50)  # 'author_search', 'keyword_search', etc.
    parameters = models.JSONField()  # Store search parameters
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    papers_collected = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.status})"
