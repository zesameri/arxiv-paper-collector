"""
Django REST Framework serializers for papers app
"""

from rest_framework import serializers
from django.db import models
from .models import Paper, Author, PaperAuthor, Collaboration, Collection, CollectionTask


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model"""
    paper_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = ['id', 'name', 'email', 'affiliation', 'orcid_id', 'paper_count', 'created_at']
        read_only_fields = ['created_at']
    
    def get_paper_count(self, obj):
        return obj.paper_set.count()


class PaperAuthorSerializer(serializers.ModelSerializer):
    """Serializer for PaperAuthor through model"""
    author_name = serializers.CharField(source='author.name', read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    
    class Meta:
        model = PaperAuthor
        fields = ['author_id', 'author_name', 'order', 'is_corresponding']


class PaperSerializer(serializers.ModelSerializer):
    """Serializer for Paper model"""
    authors_detail = PaperAuthorSerializer(source='paperauthor_set', many=True, read_only=True)
    author_names = serializers.SerializerMethodField()
    unique_id = serializers.CharField(source='get_unique_id', read_only=True)
    
    class Meta:
        model = Paper
        fields = [
            'id', 'title', 'abstract', 'publication_date', 'arxiv_id', 'pubmed_id',
            'doi', 'journal', 'citations', 'keywords', 'institution_affiliations',
            'source', 'authors_detail', 'author_names', 'unique_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_author_names(self, obj):
        return [author.name for author in obj.authors.all()]


class CollaborationSerializer(serializers.ModelSerializer):
    """Serializer for Collaboration model"""
    author1_name = serializers.CharField(source='author1.name', read_only=True)
    author2_name = serializers.CharField(source='author2.name', read_only=True)
    author1_affiliation = serializers.CharField(source='author1.affiliation', read_only=True)
    author2_affiliation = serializers.CharField(source='author2.affiliation', read_only=True)
    paper_titles = serializers.SerializerMethodField()
    
    class Meta:
        model = Collaboration
        fields = [
            'id', 'author1_name', 'author2_name', 'author1_affiliation', 'author2_affiliation',
            'paper_count', 'first_collaboration', 'last_collaboration', 'paper_titles'
        ]
    
    def get_paper_titles(self, obj):
        return [paper.title[:100] for paper in obj.papers.all()[:5]]  # First 5 papers, truncated


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model"""
    paper_count = serializers.SerializerMethodField()
    recent_papers = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id', 'name', 'description', 'created_by', 'paper_count',
            'recent_papers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_paper_count(self, obj):
        return obj.papers.count()
    
    def get_recent_papers(self, obj):
        recent = obj.papers.order_by('-publication_date')[:5]
        return [{'id': p.id, 'title': p.title, 'publication_date': p.publication_date} for p in recent]


class CollectionTaskSerializer(serializers.ModelSerializer):
    """Serializer for CollectionTask model"""
    collection_name = serializers.CharField(source='collection.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CollectionTask
        fields = [
            'id', 'name', 'task_type', 'parameters', 'status', 'papers_collected',
            'error_message', 'started_at', 'completed_at', 'collection', 'collection_name', 'duration'
        ]
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration)
        return None


class CollectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating collections with papers"""
    paper_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Collection
        fields = ['name', 'description', 'created_by', 'paper_ids']
    
    def create(self, validated_data):
        paper_ids = validated_data.pop('paper_ids', [])
        collection = Collection.objects.create(**validated_data)
        
        if paper_ids:
            papers = Paper.objects.filter(id__in=paper_ids)
            collection.papers.set(papers)
        
        return collection


class PaperListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for paper lists"""
    author_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Paper
        fields = [
            'id', 'title', 'author_names', 'publication_date', 
            'journal', 'citations', 'source'
        ]
    
    def get_author_names(self, obj):
        return [author.name for author in obj.authors.all()]


class AuthorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for author with papers and collaborations"""
    papers = PaperListSerializer(source='paper_set', many=True, read_only=True)
    collaborations = serializers.SerializerMethodField()
    paper_count = serializers.SerializerMethodField()
    total_citations = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = [
            'id', 'name', 'email', 'affiliation', 'orcid_id',
            'paper_count', 'total_citations', 'papers', 'collaborations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_paper_count(self, obj):
        return obj.paper_set.count()
    
    def get_total_citations(self, obj):
        return sum(paper.citations for paper in obj.paper_set.all())
    
    def get_collaborations(self, obj):
        # Get collaborations where this author is author1 or author2
        collaborations = Collaboration.objects.filter(
            models.Q(author1=obj) | models.Q(author2=obj)
        ).select_related('author1', 'author2')[:10]
        
        result = []
        for collab in collaborations:
            other_author = collab.author2 if collab.author1 == obj else collab.author1
            result.append({
                'author_name': other_author.name,
                'author_id': other_author.id,
                'paper_count': collab.paper_count,
                'affiliation': other_author.affiliation
            })
        
        return result


class NetworkDataSerializer(serializers.Serializer):
    """Serializer for network visualization data"""
    nodes = serializers.ListField()
    edges = serializers.ListField()
    
    def to_representation(self, instance):
        return {
            'nodes': instance.get('nodes', []),
            'edges': instance.get('edges', []),
            'metadata': {
                'total_nodes': len(instance.get('nodes', [])),
                'total_edges': len(instance.get('edges', [])),
                'generated_at': instance.get('generated_at')
            }
        } 