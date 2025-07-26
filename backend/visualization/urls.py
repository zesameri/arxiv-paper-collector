"""
URL patterns for visualization views
"""

from django.urls import path
from . import views

app_name = 'visualization'

urlpatterns = [
    # Main dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Network visualization
    path('network/', views.NetworkView.as_view(), name='network'),
    path('network/data/', views.NetworkDataView.as_view(), name='network-data'),
    
    # Collection management
    path('collections/', views.CollectionsView.as_view(), name='collections'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection-detail'),
    path('collections/new/', views.NewCollectionView.as_view(), name='new-collection'),
    
    # Paper exploration
    path('papers/', views.PapersView.as_view(), name='papers'),
    path('papers/<int:pk>/', views.PaperDetailView.as_view(), name='paper-detail'),
    
    # Author exploration
    path('authors/', views.AuthorsView.as_view(), name='authors'),
    path('authors/<int:pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
    
    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('analytics/trends/', views.TrendsView.as_view(), name='trends'),
    path('analytics/institutions/', views.InstitutionsView.as_view(), name='institutions'),
] 