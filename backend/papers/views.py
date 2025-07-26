"""
Django REST API views for papers app
"""

from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import networkx as nx
from datetime import datetime, timedelta
import json
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.collectors import ArxivCollector, PubMedCollector, SemanticScholarCollector
from shared.models.paper import Paper as PaperDataclass

from .models import Paper, Author, Collaboration, Collection, CollectionTask
from .serializers import (
    PaperSerializer, AuthorSerializer, CollaborationSerializer,
    CollectionSerializer, CollectionTaskSerializer
)


class RootAPIView(APIView):
    """Root API endpoint with basic info and available endpoints"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'ArXiv Paper Collector API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'papers': '/api/papers/',
                'authors': '/api/authors/',
                'collaborations': '/api/collaborations/',
                'collections': '/api/collections/',
                'tasks': '/api/tasks/',
                'stats': '/api/stats/',
                'collect_by_authors': '/api/collect/authors/',
                'collect_by_keywords': '/api/collect/keywords/',
                'network_analysis': '/api/network/analysis/',
                'export_papers': '/api/export/papers/',
                'export_network': '/api/export/network/',
            }
        })


class PaperViewSet(viewsets.ModelViewSet):
    """ViewSet for Paper CRUD operations"""
    queryset = Paper.objects.all().order_by('-publication_date')
    serializer_class = PaperSerializer
    permission_classes = [AllowAny]
    search_fields = ['title', 'abstract', 'authors__name']
    filterset_fields = ['source', 'journal']
    ordering_fields = ['publication_date', 'citations', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(publication_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(publication_date__lte=end_date)
        
        # Filter by author
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(authors__name__icontains=author)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def collaborators(self, request, pk=None):
        """Get all collaborators for papers by this paper's authors"""
        paper = self.get_object()
        collaborators = Author.objects.filter(
            paper__in=Paper.objects.filter(authors__in=paper.authors.all())
        ).exclude(
            id__in=paper.authors.all()
        ).annotate(
            collaboration_count=Count('paper')
        ).order_by('-collaboration_count')[:10]
        
        serializer = AuthorSerializer(collaborators, many=True)
        return Response(serializer.data)


class AuthorViewSet(viewsets.ModelViewSet):
    """ViewSet for Author CRUD operations"""
    queryset = Author.objects.all().order_by('name')
    serializer_class = AuthorSerializer
    permission_classes = [AllowAny]
    search_fields = ['name', 'affiliation']
    ordering_fields = ['name', 'created_at']
    
    @action(detail=True, methods=['get'])
    def papers(self, request, pk=None):
        """Get all papers by this author"""
        author = self.get_object()
        papers = author.paper_set.all().order_by('-publication_date')
        serializer = PaperSerializer(papers, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def collaborators(self, request, pk=None):
        """Get all collaborators for this author"""
        author = self.get_object()
        collaborators = Author.objects.filter(
            paper__in=author.paper_set.all()
        ).exclude(
            id=author.id
        ).annotate(
            collaboration_count=Count('paper')
        ).order_by('-collaboration_count')
        
        serializer = AuthorSerializer(collaborators, many=True)
        return Response(serializer.data)


class CollaborationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing collaborations"""
    queryset = Collaboration.objects.all().order_by('-paper_count')
    serializer_class = CollaborationSerializer
    permission_classes = [AllowAny]
    ordering_fields = ['paper_count', 'first_collaboration']


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Collection CRUD operations"""
    queryset = Collection.objects.all().order_by('-created_at')
    serializer_class = CollectionSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['post'])
    def add_papers(self, request, pk=None):
        """Add papers to this collection"""
        collection = self.get_object()
        paper_ids = request.data.get('paper_ids', [])
        
        papers = Paper.objects.filter(id__in=paper_ids)
        collection.papers.add(*papers)
        
        return Response({
            'message': f'Added {len(papers)} papers to collection',
            'total_papers': collection.papers.count()
        })


class CollectionTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for CollectionTask CRUD operations"""
    queryset = CollectionTask.objects.all().order_by('-started_at')
    serializer_class = CollectionTaskSerializer
    permission_classes = [AllowAny]


class CollectByAuthorsView(APIView):
    """API endpoint for collecting papers by author names"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        authors = request.data.get('authors', [])
        max_papers = request.data.get('max_papers', 50)
        expand_network = request.data.get('expand_network', False)
        collection_name = request.data.get('collection_name', f'Collection {timezone.now().strftime("%Y-%m-%d %H:%M")}')
        
        if not authors:
            return Response(
                {'error': 'No authors provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create collection
        collection = Collection.objects.create(
            name=collection_name,
            description=f'Papers collected from authors: {", ".join(authors)}'
        )
        
        # Create collection task
        task = CollectionTask.objects.create(
            name=f'Collect from authors: {", ".join(authors)}',
            task_type='author_search',
            parameters={
                'authors': authors,
                'max_papers': max_papers,
                'expand_network': expand_network
            },
            collection=collection,
            status='running',
            started_at=timezone.now()
        )
        
        try:
            # Initialize collectors
            arxiv_collector = ArxivCollector()
            semantic_collector = SemanticScholarCollector()
            # PubMed is in maintenance, so skip for now
            
            total_collected = 0
            
            for author_name in authors:
                # Collect from arXiv
                arxiv_papers = arxiv_collector.search_by_author(author_name, max_papers)
                
                # Collect from Semantic Scholar  
                semantic_papers = semantic_collector.search_by_author(author_name, max_papers)
                
                # Store papers in database
                for paper_data in arxiv_papers + semantic_papers:
                    paper_obj = self._store_paper(paper_data)
                    if paper_obj:
                        collection.papers.add(paper_obj)
                        total_collected += 1
            
            # Update task
            task.status = 'completed'
            task.papers_collected = total_collected
            task.completed_at = timezone.now()
            task.save()
            
            return Response({
                'message': f'Successfully collected {total_collected} papers',
                'collection_id': collection.id,
                'task_id': task.id
            })
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save()
            
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _store_paper(self, paper_data: PaperDataclass):
        """Store a paper dataclass in the database"""
        try:
            # Check if paper already exists
            existing = None
            if paper_data.arxiv_id:
                existing = Paper.objects.filter(arxiv_id=paper_data.arxiv_id).first()
            elif paper_data.pubmed_id:
                existing = Paper.objects.filter(pubmed_id=paper_data.pubmed_id).first()
            elif paper_data.doi:
                existing = Paper.objects.filter(doi=paper_data.doi).first()
            
            if existing:
                return existing
            
            # Parse publication date
            try:
                pub_date = datetime.strptime(paper_data.publication_date, '%Y-%m-%d').date()
            except:
                pub_date = timezone.now().date()
            
            # Create paper
            paper = Paper.objects.create(
                title=paper_data.title,
                abstract=paper_data.abstract,
                publication_date=pub_date,
                arxiv_id=paper_data.arxiv_id,
                pubmed_id=paper_data.pubmed_id,
                doi=paper_data.doi,
                journal=paper_data.journal,
                citations=paper_data.citations,
                keywords=paper_data.keywords,
                institution_affiliations=paper_data.institution_affiliations,
                source=paper_data.source
            )
            
            # Create authors and relationships
            for i, author_name in enumerate(paper_data.authors):
                author, created = Author.objects.get_or_create(name=author_name)
                paper.authors.add(author, through_defaults={'order': i})
            
            return paper
            
        except Exception as e:
            print(f"Error storing paper: {e}")
            return None


class CollectByKeywordsView(APIView):
    """API endpoint for collecting papers by keywords"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        keywords = request.data.get('keywords', [])
        max_papers = request.data.get('max_papers', 100)
        collection_name = request.data.get('collection_name', f'Keywords Collection {timezone.now().strftime("%Y-%m-%d %H:%M")}')
        
        if not keywords:
            return Response(
                {'error': 'No keywords provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create collection
        collection = Collection.objects.create(
            name=collection_name,
            description=f'Papers collected for keywords: {", ".join(keywords)}'
        )
        
        try:
            # Initialize collectors
            arxiv_collector = ArxivCollector()
            semantic_collector = SemanticScholarCollector()
            
            # Collect papers
            arxiv_papers = arxiv_collector.search_by_keywords(keywords, max_papers)
            semantic_papers = semantic_collector.search_by_keywords(keywords, max_papers)
            
            total_collected = 0
            
            # Store papers in database
            for paper_data in arxiv_papers + semantic_papers:
                paper_obj = CollectByAuthorsView()._store_paper(paper_data)
                if paper_obj:
                    collection.papers.add(paper_obj)
                    total_collected += 1
            
            return Response({
                'message': f'Successfully collected {total_collected} papers',
                'collection_id': collection.id
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NetworkAnalysisView(APIView):
    """API endpoint for network analysis"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Build collaboration graph
        G = nx.Graph()
        
        collaborations = Collaboration.objects.all()
        for collab in collaborations:
            G.add_edge(
                collab.author1.name, 
                collab.author2.name, 
                weight=collab.paper_count
            )
        
        # Calculate metrics
        if G.number_of_nodes() > 0:
            analysis = {
                'total_authors': G.number_of_nodes(),
                'total_collaborations': G.number_of_edges(),
                'average_collaborations_per_author': sum(dict(G.degree()).values()) / G.number_of_nodes(),
                'most_collaborative_authors': sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10],
                'connected_components': nx.number_connected_components(G),
                'largest_component_size': len(max(nx.connected_components(G), key=len)) if G.number_of_nodes() > 0 else 0,
                'density': nx.density(G),
                'clustering_coefficient': nx.average_clustering(G) if G.number_of_nodes() > 0 else 0
            }
        else:
            analysis = {
                'total_authors': 0,
                'total_collaborations': 0,
                'average_collaborations_per_author': 0,
                'most_collaborative_authors': [],
                'connected_components': 0,
                'largest_component_size': 0,
                'density': 0,
                'clustering_coefficient': 0
            }
        
        return Response(analysis)


class StatsView(APIView):
    """API endpoint for general statistics"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        stats = {
            'total_papers': Paper.objects.count(),
            'total_authors': Author.objects.count(),
            'total_collaborations': Collaboration.objects.count(),
            'total_collections': Collection.objects.count(),
            'papers_by_source': dict(Paper.objects.values_list('source').annotate(count=Count('id'))),
            'papers_by_year': dict(
                Paper.objects.extra(
                    select={'year': "EXTRACT(year FROM publication_date)"}
                ).values('year').annotate(count=Count('id')).order_by('year')
            ),
            'top_cited_papers': Paper.objects.order_by('-citations')[:10].values(
                'title', 'citations', 'publication_date'
            ),
            'most_productive_authors': Author.objects.annotate(
                paper_count=Count('paper')
            ).order_by('-paper_count')[:10].values('name', 'paper_count')
        }
        
        return Response(stats)


class ExportPapersView(APIView):
    """API endpoint for exporting papers data"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        papers = Paper.objects.all().select_related().prefetch_related('authors')
        
        data = []
        for paper in papers:
            data.append({
                'title': paper.title,
                'authors': [author.name for author in paper.authors.all()],
                'abstract': paper.abstract,
                'publication_date': paper.publication_date.isoformat(),
                'journal': paper.journal,
                'citations': paper.citations,
                'source': paper.source,
                'arxiv_id': paper.arxiv_id,
                'pubmed_id': paper.pubmed_id,
                'doi': paper.doi,
                'keywords': paper.keywords,
            })
        
        return Response(data)


class ExportNetworkView(APIView):
    """API endpoint for exporting network data"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get nodes (authors)
        authors = Author.objects.annotate(
            paper_count=Count('paper')
        ).values('id', 'name', 'paper_count', 'affiliation')
        
        # Get edges (collaborations)
        collaborations = Collaboration.objects.select_related(
            'author1', 'author2'
        ).values(
            'author1__id', 'author1__name',
            'author2__id', 'author2__name', 
            'paper_count'
        )
        
        return Response({
            'nodes': list(authors),
            'edges': list(collaborations)
        })
