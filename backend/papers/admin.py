"""
Django admin configuration for papers app
"""

from django.contrib import admin
from django.db.models import Count
from .models import Paper, Author, PaperAuthor, Collaboration, Collection, CollectionTask


class PaperAuthorInline(admin.TabularInline):
    """Inline admin for paper-author relationships"""
    model = PaperAuthor
    extra = 1
    autocomplete_fields = ['author']


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    """Admin interface for Paper model"""
    list_display = [
        'title_truncated', 'publication_date', 'source', 
        'citations', 'author_count', 'created_at'
    ]
    list_filter = ['source', 'publication_date', 'created_at']
    search_fields = ['title', 'abstract', 'authors__name', 'arxiv_id', 'doi']
    readonly_fields = ['created_at', 'updated_at', 'get_unique_id']
    inlines = [PaperAuthorInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'abstract', 'publication_date', 'journal', 'source')
        }),
        ('Identifiers', {
            'fields': ('arxiv_id', 'pubmed_id', 'doi', 'get_unique_id'),
            'classes': ('collapse',)
        }),
        ('Metrics & Classification', {
            'fields': ('citations', 'keywords', 'institution_affiliations')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_truncated(self, obj):
        return obj.title[:100] + '...' if len(obj.title) > 100 else obj.title
    title_truncated.short_description = 'Title'
    
    def author_count(self, obj):
        return obj.authors.count()
    author_count.short_description = 'Authors'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('authors')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Admin interface for Author model"""
    list_display = ['name', 'affiliation', 'paper_count', 'total_citations', 'created_at']
    list_filter = ['affiliation', 'created_at']
    search_fields = ['name', 'email', 'affiliation', 'orcid_id']
    readonly_fields = ['created_at', 'updated_at', 'paper_count', 'total_citations']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'affiliation', 'orcid_id')
        }),
        ('Statistics', {
            'fields': ('paper_count', 'total_citations'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def paper_count(self, obj):
        return obj.paper_set.count()
    paper_count.short_description = 'Papers'
    
    def total_citations(self, obj):
        return sum(paper.citations for paper in obj.paper_set.all())
    total_citations.short_description = 'Total Citations'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            papers_count=Count('paper')
        )


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    """Admin interface for Collaboration model"""
    list_display = [
        'author1', 'author2', 'paper_count', 
        'first_collaboration', 'last_collaboration'
    ]
    list_filter = ['first_collaboration', 'paper_count']
    search_fields = ['author1__name', 'author2__name']
    autocomplete_fields = ['author1', 'author2']
    readonly_fields = ['paper_count']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author1', 'author2')


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin interface for Collection model"""
    list_display = ['name', 'created_by', 'paper_count', 'created_at']
    list_filter = ['created_by', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['papers']
    readonly_fields = ['created_at', 'updated_at', 'paper_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Papers', {
            'fields': ('papers', 'paper_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def paper_count(self, obj):
        return obj.papers.count()
    paper_count.short_description = 'Paper Count'


@admin.register(CollectionTask)
class CollectionTaskAdmin(admin.ModelAdmin):
    """Admin interface for CollectionTask model"""
    list_display = [
        'name', 'task_type', 'status', 'papers_collected', 
        'started_at', 'completed_at'
    ]
    list_filter = ['task_type', 'status', 'started_at']
    search_fields = ['name', 'error_message']
    readonly_fields = ['started_at', 'completed_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('name', 'task_type', 'parameters', 'collection')
        }),
        ('Status', {
            'fields': ('status', 'papers_collected', 'error_message')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = 'ArXiv Paper Collector Admin'
admin.site.site_title = 'Paper Collector'
admin.site.index_title = 'Research Paper Collection Management'
