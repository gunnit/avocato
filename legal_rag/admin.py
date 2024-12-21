from django.contrib import admin
from django.utils.html import format_html
from .models import PenalCodeBook, PenalCodeTitle, PenalCodeArticle, SavedSearchResult

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
