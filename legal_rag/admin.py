from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PenalCodeBook, PenalCodeTitle, PenalCodeArticle, 
    SavedSearchResult, PDFAnalysisResult, LegalSearchResult
)

@admin.register(LegalSearchResult)
class LegalSearchResultAdmin(admin.ModelAdmin):
    list_display = ('caso', 'search_query_preview', 'results_count', 'date_saved')
    list_filter = ('date_saved', 'caso')
    search_fields = ('caso__titolo', 'search_query')
    ordering = ('-date_saved',)

    def search_query_preview(self, obj):
        query_data = obj.search_query
        if isinstance(query_data, str):
            import json
            try:
                query_data = json.loads(query_data)
            except json.JSONDecodeError:
                return query_data[:100]
        return query_data.get('query', '')[:100] if isinstance(query_data, dict) else str(query_data)[:100]
    search_query_preview.short_description = 'Search Query'

    def results_count(self, obj):
        results_data = obj.search_results
        if isinstance(results_data, str):
            import json
            try:
                results_data = json.loads(results_data)
            except json.JSONDecodeError:
                return 0
        
        if isinstance(results_data, dict) and 'results_by_source' in results_data:
            total = sum(len(results) for results in results_data['results_by_source'].values())
            return total
        return 0
    results_count.short_description = 'Results Count'

    readonly_fields = ('date_saved', 'formatted_results')
    
    def formatted_results(self, obj):
        results_data = obj.search_results
        if isinstance(results_data, str):
            import json
            try:
                results_data = json.loads(results_data)
            except json.JSONDecodeError:
                return "Invalid JSON data"
        
        if not isinstance(results_data, dict) or 'results_by_source' not in results_data:
            return "No results found"
            
        html = []
        for source, results in results_data['results_by_source'].items():
            html.append(f"<h3>{source} ({len(results)} results)</h3>")
            for result in results:
                html.append("<div style='margin-bottom: 15px;'>")
                html.append(f"<strong><a href='{result.get('url', '#')}' target='_blank'>{result.get('title', 'No title')}</a></strong>")
                html.append(f"<p style='margin: 5px 0;'>{result.get('snippet', 'No snippet')}</p>")
                html.append("</div>")
        
        return format_html("".join(html))
    formatted_results.short_description = 'Formatted Results'

    fieldsets = (
        ('Basic Information', {
            'fields': ('caso', 'search_query')
        }),
        ('Search Results', {
            'fields': ('formatted_results', 'search_results'),
            'classes': ('wide',)
        }),
        ('Search Strategy', {
            'fields': ('search_strategy',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('date_saved',),
            'classes': ('collapse',)
        }),
    )

@admin.register(PDFAnalysisResult)
class PDFAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('filename', 'caso', 'processing_type', 'status_display', 'created_at')
    list_filter = ('processing_type', 'processing_completed', 'analysis_completed', 'created_at')
    search_fields = ('filename', 'caso__titolo', 'extracted_text')
    ordering = ('-created_at',)
    
    def status_display(self, obj):
        if obj.processing_completed and obj.analysis_completed:
            return format_html('<span style="color: green;">✓ Completed</span>')
        elif obj.processing_completed:
            return format_html('<span style="color: orange;">⚡ Analysis Pending</span>')
        else:
            return format_html('<span style="color: blue;">⟳ Processing</span>')
    status_display.short_description = 'Status'

    readonly_fields = ('created_at', 'updated_at', 'trace_id')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('caso', 'filename', 'pdf_file', 'processing_type')
        }),
        ('Processing Status', {
            'fields': ('processing_completed', 'analysis_completed')
        }),
        ('Processing Results', {
            'fields': ('extracted_text', 'structured_content', 'content_chunks'),
            'classes': ('collapse',)
        }),
        ('Analysis Results', {
            'fields': ('dati_generali', 'informazioni_legali_specifiche', 
                      'dati_processuali', 'analisi_linguistica'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'trace_id'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SavedSearchResult)
class SavedSearchResultAdmin(admin.ModelAdmin):
    list_display = ('search_title', 'caso', 'date_saved', 'snippet_preview')
    list_filter = ('date_saved', 'caso')
    search_fields = ('search_title', 'search_snippet', 'caso__titolo')
    ordering = ('-date_saved',)
    
    def snippet_preview(self, obj):
        return format_html('<span title="{}">{}</span>', 
                         obj.search_snippet, 
                         obj.search_snippet[:100] + '...' if len(obj.search_snippet) > 100 else obj.search_snippet)
    snippet_preview.short_description = 'Snippet Preview'

    readonly_fields = ('date_saved',)
    
    fieldsets = (
        ('Search Result', {
            'fields': ('caso', 'search_title', 'search_link', 'search_snippet')
        }),
        ('Metadata', {
            'fields': ('date_saved',),
            'classes': ('collapse',)
        }),
    )

class PenalCodeTitleInline(admin.TabularInline):
    model = PenalCodeTitle
    extra = 1
    show_change_link = True
    fields = ('number', 'name', 'articles_range')
    ordering = ('number',)

class PenalCodeArticleInline(admin.TabularInline):
    model = PenalCodeArticle
    extra = 1
    fields = ('number', 'heading')
    ordering = ('number',)

@admin.register(PenalCodeBook)
class PenalCodeBookAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'title_count', 'view_description')
    list_display_links = ('number', 'name')
    search_fields = ('name', 'description')
    ordering = ('number',)
    inlines = [PenalCodeTitleInline]

    def title_count(self, obj):
        return obj.titles.count()
    title_count.short_description = 'Number of Titles'

    def view_description(self, obj):
        return format_html('<span title="{}">{}</span>', 
                         obj.description, 
                         obj.description[:100] + '...' if len(obj.description) > 100 else obj.description)
    view_description.short_description = 'Description'

@admin.register(PenalCodeTitle)
class PenalCodeTitleAdmin(admin.ModelAdmin):
    list_display = ('full_title', 'book', 'articles_range', 'article_count')
    list_filter = ('book',)
    search_fields = ('name', 'description', 'articles_range')
    ordering = ('book__number', 'number')
    inlines = [PenalCodeArticleInline]
    
    def full_title(self, obj):
        return f"Title {obj.number} - {obj.name}"
    full_title.short_description = 'Title'
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Number of Articles'

@admin.register(PenalCodeArticle)
class PenalCodeArticleAdmin(admin.ModelAdmin):
    list_display = ('article_display', 'title', 'last_updated', 'content_preview')
    list_filter = ('title__book', 'title', 'last_updated')
    search_fields = ('number', 'heading', 'content')
    ordering = ('number',)
    readonly_fields = ('last_updated',)
    
    def article_display(self, obj):
        return f"Article {obj.number} - {obj.heading}"
    article_display.short_description = 'Article'
    
    def content_preview(self, obj):
        return format_html('<span title="{}">{}</span>', 
                         obj.content, 
                         obj.content[:100] + '...' if len(obj.content) > 100 else obj.content)
    content_preview.short_description = 'Content Preview'

    fieldsets = (
        ('Article Information', {
            'fields': ('title', 'number', 'heading')
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
