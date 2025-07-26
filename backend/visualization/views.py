"""
Django views for visualization app
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

# Import our models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from papers.models import Paper, Author, Collaboration, Collection


class DashboardView(APIView):
    """Main dashboard API endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'ArXiv Paper Collector Dashboard',
            'stats': {
                'total_papers': Paper.objects.count(),
                'total_authors': Author.objects.count(),
                'total_collaborations': Collaboration.objects.count(),
                'total_collections': Collection.objects.count(),
            },
            'recent_papers': list(Paper.objects.values('title', 'publication_date', 'arxiv_id')[:5]),
            'recent_collections': list(Collection.objects.values('name', 'created_at')[:5])
        })


class NetworkView(APIView):
    """Network visualization info"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Network Visualization',
            'available_endpoints': {
                'network_data': '/visualization/network/data/',
                'full_analysis': '/api/network/analysis/'
            }
        })


class NetworkDataView(APIView):
    """API endpoint for network visualization data"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get authors with their paper counts
        authors = Author.objects.all()[:100]  # Limit for performance
        nodes = []
        
        for author in authors:
            nodes.append({
                'id': author.id,
                'name': author.name,
                'paper_count': author.paper_set.count(),
                'affiliation': author.affiliation or 'Unknown'
            })
        
        # Get collaborations
        collaborations = Collaboration.objects.all()[:200]  # Limit for performance
        edges = []
        
        for collab in collaborations:
            edges.append({
                'source': collab.author1.id,
                'target': collab.author2.id,
                'weight': collab.paper_count
            })
        
        return Response({
            'nodes': nodes,
            'edges': edges
        })


class CollectionsView(APIView):
    """Collections management API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        collections = Collection.objects.all().order_by('-created_at')[:20]
        return Response({
            'message': 'Collections Management',
            'collections': [{
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'created_at': c.created_at,
                'total_papers': c.papers.count() if hasattr(c, 'papers') else 0
            } for c in collections]
        })


class CollectionDetailView(APIView):
    """Collection detail API"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            collection = Collection.objects.get(id=pk)
            return Response({
                'id': collection.id,
                'name': collection.name,
                'description': collection.description,
                'created_at': collection.created_at,
                'papers': list(collection.papers.values('title', 'arxiv_id', 'publication_date')[:50]) if hasattr(collection, 'papers') else []
            })
        except Collection.DoesNotExist:
            return Response({'error': 'Collection not found'}, status=404)


class NewCollectionView(APIView):
    """New collection creation API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Create New Collection',
            'instructions': 'Send POST request with name and description'
        })
    
    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        
        if not name:
            return Response({'error': 'Name is required'}, status=400)
        
        collection = Collection.objects.create(name=name, description=description)
        return Response({
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
            'created_at': collection.created_at
        })


class PapersView(APIView):
    """Papers listing API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        papers = Paper.objects.all().order_by('-publication_date')[:50]
        return Response({
            'message': 'Papers List',
            'total_count': Paper.objects.count(),
            'papers': [{
                'id': p.id,
                'title': p.title,
                'arxiv_id': p.arxiv_id,
                'publication_date': p.publication_date,
                'authors': [a.name for a in p.authors.all()[:3]]  # First 3 authors
            } for p in papers]
        })


class PaperDetailView(APIView):
    """Paper detail API"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            paper = Paper.objects.get(id=pk)
            return Response({
                'id': paper.id,
                'title': paper.title,
                'arxiv_id': paper.arxiv_id,
                'abstract': paper.abstract,
                'publication_date': paper.publication_date,
                'arxiv_url': paper.arxiv_url,
                'pdf_url': paper.pdf_url,
                'authors': [{'id': a.id, 'name': a.name, 'affiliation': a.affiliation} for a in paper.authors.all()],
                'keywords': paper.keywords
            })
        except Paper.DoesNotExist:
            return Response({'error': 'Paper not found'}, status=404)


class AuthorsView(APIView):
    """Authors listing API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        authors = Author.objects.all().order_by('name')[:50]
        return Response({
            'message': 'Authors List',
            'total_count': Author.objects.count(),
            'authors': [{
                'id': a.id,
                'name': a.name,
                'affiliation': a.affiliation,
                'paper_count': a.paper_set.count()
            } for a in authors]
        })


class AuthorDetailView(APIView):
    """Author detail API"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            author = Author.objects.get(id=pk)
            return Response({
                'id': author.id,
                'name': author.name,
                'affiliation': author.affiliation,
                'papers': [{
                    'id': p.id,
                    'title': p.title,
                    'arxiv_id': p.arxiv_id,
                    'publication_date': p.publication_date
                } for p in author.paper_set.all()[:20]]
            })
        except Author.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)


class AnalyticsView(APIView):
    """Analytics dashboard API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Analytics Dashboard',
            'stats': {
                'total_papers': Paper.objects.count(),
                'total_authors': Author.objects.count(),
                'total_collaborations': Collaboration.objects.count(),
                'papers_this_month': Paper.objects.filter(
                    created_at__gte=timezone.now().replace(day=1)
                ).count()
            }
        })


class TrendsView(APIView):
    """Research trends API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Research Trends Analysis',
            'note': 'Trend analysis endpoint - implement specific analytics as needed'
        })


class InstitutionsView(APIView):
    """Institutions analysis API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Institutions Analysis',
            'note': 'Institution analysis endpoint - implement specific analytics as needed'
        })
