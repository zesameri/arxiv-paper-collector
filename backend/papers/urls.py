"""
URL patterns for papers API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'papers', views.PaperViewSet)
router.register(r'authors', views.AuthorViewSet)
router.register(r'collaborations', views.CollaborationViewSet)
router.register(r'collections', views.CollectionViewSet)
router.register(r'tasks', views.CollectionTaskViewSet)

urlpatterns = [
    # Root API endpoint
    path('', views.RootAPIView.as_view(), name='api-root'),
    
    # API endpoints
    path('', include(router.urls)),
    
    # Custom endpoints
    path('collect/authors/', views.CollectByAuthorsView.as_view(), name='collect-authors'),
    path('collect/keywords/', views.CollectByKeywordsView.as_view(), name='collect-keywords'),
    path('network/analysis/', views.NetworkAnalysisView.as_view(), name='network-analysis'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    
    # Data export endpoints
    path('export/papers/', views.ExportPapersView.as_view(), name='export-papers'),
    path('export/network/', views.ExportNetworkView.as_view(), name='export-network'),
] 